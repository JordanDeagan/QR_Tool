# -*- coding: windows-1252 -*-
"""
Name: QR Toolbox v1.3
Description: The QR Toolbox is a suite a tools for creating and reading QR codes. See the About screen for more
information
Author(s): Code integration, minor enhancements, & platform development - Timothy Boe boe.timothy@epa.gov;
    qrcode - Lincoln Loop info@lincolnloop.com; pyzbar - Lawrence Hudson quicklizard@googlemail.com;
    OpenCV code - Adrian Rosebrock https://www.pyimagesearch.com/author/adrian/;
Contact: Timothy Boe boe.timothy@epa.gov
Requirements: Python 3.7+, pyzbar, imutils, opencv-python, qrcode[pil]
"""

# import the necessary packages
import pkg_resources  # this one and platform are built-in, as are some others (and so don't need to be checked)
import platform
import argparse
import csv
import datetime
import os
import os.path
import shutil
import time
from datetime import timedelta
from time import strftime
from tkinter import *
from tkinter import filedialog


# colors
class bcolors:
    HEADER = ''
    OKBLUE = '[color=#009999]'
    OKGREEN = '[color=#66cc00]'
    WARNING = '[color=#e3e129]'
    FAIL = '[color=#a72618]'
    ENDC = '[/color]'
    BOLD = ''
    UNDERLINE = ''


"""
This function checks the Python version and the Python module versions to ensure they are accurate.
If they are not exactly the versions the QR Tool was built for, a warning message will be printed.
(System can still run, but issues may arise because the packages/Python version code may have changed)
"""


def check_versions():
    pkg_array = ["pyzbar", "imutils", "qrcode", "Pillow", "opencv-python", "Office365-REST-Python-Client", "Kivy", "kivy-deps.angle", "kivy-deps.glew",
                 "kivy-deps.gstreamer", "kivy-deps.sdl2", "Kivy-Garden"]
    pkg_version = {"pyzbar": "0.1.8", "imutils": "0.5.3", "qrcode": "6.1", "Pillow": "7.0.0", "opencv-python": "4.2.0.32",
                   "Office365-REST-Python-Client": "2.2.1", "Kivy": "1.11.1", "kivy-deps.angle": "0.2.0", "kivy-deps.glew": "0.2.0",
                   "kivy-deps.gstreamer": "0.2.0", "kivy-deps.sdl2": "0.2.0", "Kivy-Garden": "0.1.4"}
    pkgs_to_install = []
    i = 0
    while i < len(pkg_array):  # check which packages need to be installed or updated
        try:
            if pkg_resources.get_distribution(pkg_array[i]).version != pkg_version[pkg_array[i]]:
                pkgs_to_install.append(pkg_array[i])
        except:  # this catches errors thrown by a not-installed pkg resource, so we know to install it
            pkgs_to_install.append(pkg_array[i])
        i += 1

    if len(pkgs_to_install) > 0:
        print(f"{bcolors.WARNING}[WARNING] Some Python module versions are not accurate or installed, they will be installed "
              f"now.{bcolors.ENDC}\n")
    for pkg in pkgs_to_install:  # install the packages
        os.system(f"pip install {pkg}=={pkg_version[pkg]}")

    if os.environ.get('OPENCV_VIDEOIO_PRIORITY_MSMF') is None or os.environ.get('OPENCV_VIDEOIO_PRIORITY_MSMF') != '0':
        print(f"{bcolors.WARNING}[WARNING] OPENCV_VIDEOIO_PRIORITY_MSMF also not set. Setting now.{bcolors.ENDC}")
        os.system("setx OPENCV_VIDEOIO_PRIORITY_MSMF 0")

    if platform.python_version() != '3.7.4':
        print(f"{bcolors.WARNING}[WARNING] Your Python version is not 3.7.4. For the most stable build, install Python"
              f" version 3.7.4.{bcolors.ENDC}")


# import csv packages
import cv2
import imutils
import numpy as np
import qrcode
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
from imutils.video import VideoStream
from office365.runtime.auth.authentication_context import AuthenticationContext
from office365.sharepoint.client_context import ClientContext
from office365.sharepoint.file import File
from office365.sharepoint.file_creation_information import FileCreationInformation
from pyzbar import pyzbar
from pyzbar.pyzbar import ZBarSymbol

import threading
from kivy.app import App

from Setup.settings import settings

# Sharepoint related variables
listTitle = "QR Timestamps"
qrfolder = "QRCodes"
bkcsvfolder = "HXWTEST"
remoteQRBatchFile = "System_Data/names-remote.csv"
localQRBatchFile = "names.csv"
relative_url = "/sites/Emergency%20Response/EOCIncident/EOC%20Documents/QRCodes/names.csv"
qr_storage_file = "System_Data/qr-data.txt"  # file that contains saved session information
backup_file = "System_Data/backup.txt"  # file that contains data that couldn't be uploaded, to later be uploaded

context_auth = AuthenticationContext(url=settings['url'])
context_auth.acquire_token_for_app(client_id=settings['client_id'], client_secret=settings['client_secret'])
ctx = ClientContext(settings['url'], context_auth)

# load variables
# set store folder default, assign system ID, and wait time
storagePath = "None"
checkStorage = False  # whether system should check if there is any backed up data or previous session data
user_chose_storage = False
not_done = True
system_id = os.environ['COMPUTERNAME']
t_value = timedelta(seconds=10)
cameraSource = "a"
storageChoice = ""
special_char_bool = True

# Lists and Dictionaries used for special character handling and conversion
trouble_characters = ['\t', '\n', '\r']
bad_file_name_list = ['*', ':', '"', '<', '>', ',', '/', '|', '?', '\t', '\r', '\n', '\\']
special_characters = ["�", "�", "�", "�", "�", "�", "�", "�", "�", "�", "�", "�", "�", "�", "�", "�", "�", "�", "�",
                      "�", "�", "�", "�", "�", "�", "�", "�", "�", "�", "�", "�", "�", "�", "�", "�", "�", "�", "�",
                      "�", "�", "�", "�", "�", "�", "�", "�", "�", "�", "�", "�", "�", "�", "�", "�", "�", "�", "�",
                      "�", "�", "�", "�", "�"]
code_characters = ["!@!a1!", "!@!a2!", "!@!a3!", "!@!a4!", "!@!a5!", "!@!a6!", "!@!a7!", "!@!c1!", "!@!e1!", "!@!e2!",
                   "!@!e3!", "!@!e4!", "!@!i1!", "!@!i2!", "!@!i3!", "!@!i4!", "!@!o1!", "!@!n1!", "!@!o2!", "!@!o3!",
                   "!@!o4!", "!@!o5!", "!@!o6!", "!@!o7!", "!@!u1!", "!@!u2!", "!@!u3!", "!@!u4!", "!@!y1!", "!@!b1!",
                   "!@!y2!", "!@!A1!", "!@!A2!", "!@!A3!", "!@!A4!", "!@!A5!", "!@!A6!", "!@!A7!", "!@!C1!", "!@!E1!",
                   "!@!E2!", "!@!E3!", "!@!E4!", "!@!I1!", "!@!I2!", "!@!I3!", "!@!I4!", "!@!O1!", "!@!N1!", "!@!O2!",
                   "!@!O3!", "!@!O4!", "!@!O5!", "!@!O6!", "!@!O7!", "!@!U1!", "!@!U2!", "!@!U3!", "!@!U4!", "!@!Y1!",
                   "!@!B1!", "!@!Y2!"]
char_dict_special_to_code = {"�": "!@!a1!", "�": "!@!a2!", "�": "!@!a3!", "�": "!@!a4!", "�": "!@!a5!", "�": "!@!a6!",
                             "�": "!@!a7!", "�": "!@!c1!", "�": "!@!e1!", "�": "!@!e1!", "�": "!@!e3!", "�": "!@!e4!",
                             "�": "!@!i1!", "�": "!@!i2!", "�": "!@!i3!", "�": "!@!i4!", "�": "!@!o1!", "�": "!@!n1!",
                             "�": "!@!o2!", "�": "!@!o3!", "�": "!@!o4!", "�": "!@!o5!", "�": "!@!o6!", "�": "!@!o7!",
                             "�": "!@!u1!", "�": "!@!u2!", "�": "!@!u3!", "�": "!@!u4!", "�": "!@!y1!", "�": "!@!b1!",
                             "�": "!@!y2!", "�": "!@!A1!", "�": "!@!A2!", "�": "!@!A3!", "�": "!@!A4!", "�": "!@!A5!",
                             "�": "!@!A6!", "�": "!@!A7!", "�": "!@!C1!", "�": "!@!E1!", "�": "!@!E2!", "�": "!@!E3!",
                             "�": "!@!E4!", "�": "!@!I1!", "�": "!@!I2!", "�": "!@!I3!", "�": "!@!I4!", "�": "!@!O1!",
                             "�": "!@!N1!", "�": "!@!O2!", "�": "!@!O3!", "�": "!@!O4!", "�": "!@!O5!", "�": "!@!O6!",
                             "�": "!@!O7!", "�": "!@!U1!", "�": "!@!U2!", "�": "!@!U3!", "�": "!@!U4!", "�": "!@!Y1!",
                             "�": "!@!B1!", "�": "!@!Y2!"}
char_dict_code_to_special = {"!@!a1!": "�", "!@!a2!": "�", "!@!a3!": "�", "!@!a4!": "�", "!@!a5!": "�", "!@!a6!": "�",
                             "!@!a7!": "�", "!@!c1!": "�", "!@!e1!": "�", "!@!e2!": "�", "!@!e3!": "�", "!@!e4!": "�",
                             "!@!i1!": "�", "!@!i2!": "�", "!@!i3!": "�", "!@!i4!": "�", "!@!o1!": "�", "!@!n1!": "�",
                             "!@!o2!": "�", "!@!o3!": "�", "!@!o4!": "�", "!@!o5!": "�", "!@!o6!": "�", "!@!o7!": "�",
                             "!@!u1!": "�", "!@!u2!": "�", "!@!u3!": "�", "!@!u4!": "�", "!@!y1!": "�", "!@!b1!": "�",
                             "!@!y2!": "�", "!@!A1!": "�", "!@!A2!": "�", "!@!A3!": "�", "!@!A4!": "�", "!@!A5!": "�",
                             "!@!A6!": "�", "!@!A7!": "�", "!@!C1!": "�", "!@!E1!": "�", "!@!E2!": "�", "!@!E3!": "�",
                             "!@!E4!": "�", "!@!I1!": "�", "!@!I2!": "�", "!@!I3!": "�", "!@!I4!": "�", "!@!O1!": "�",
                             "!@!N1!": "�", "!@!O2!": "�", "!@!O3!": "�", "!@!O4!": "�", "!@!O5!": "�", "!@!O6!": "�",
                             "!@!O7!": "�", "!@!U1!": "�", "!@!U2!": "�", "!@!U3!": "�", "!@!U4!": "�", "!@!Y1!": "�",
                             "!@!B1!": "�", "!@!Y2!": "�"}
char_dict_special_to_reg = {"�": "a", "�": "a", "�": "a", "�": "a", "�": "a", "�": "a", "�": "a", "�": "c", "�": "e",
                            "�": "e", "�": "e", "�": "e", "�": "i", "�": "i", "�": "i", "�": "i", "�": "o", "�": "n",
                            "�": "o", "�": "o", "�": "o", "�": "o", "�": "o", "�": "o", "�": "u", "�": "u", "�": "u",
                            "�": "u", "�": "y", "�": "b", "�": "y", "�": "A", "�": "A", "�": "A", "�": "A", "�": "A",
                            "�": "A", "�": "A", "�": "C", "�": "E", "�": "E", "�": "E", "�": "E", "�": "I", "�": "I",
                            "�": "I", "�": "I", "�": "O", "�": "N", "�": "O", "�": "O", "�": "O", "�": "O", "�": "O",
                            "�": "O", "�": "U", "�": "U", "�": "U", "�": "U", "�": "Y", "�": "B", "�": "Y"}


"""
This function converts the passed data based on the other parameters, and returns the converted data
These conversions fall under 4 cases:
    1. Data has Special Characters that need to be converted to Code Characters (used in the video() function)
    2. Data has Special Characters that need to be converted to Regular Characters (only if uploading to SharePoint)
    3. Data has Code Characters that need to be converted to Special Characters (used for printing the data)
    4. Data has Special Characters that need to be converted to '-' so that it can be used as a file name
@param data_to_convert the data that is to be converted
@param character_list the list of characters that if found are to be converted
@param conversion_dict the dictionary of characters used for conversion
@param is_for_file_name if True, the code executes differently by replacing with '-' and printing text. Default is False

Note: For the logic to work when replacing \t,\n, \r with a space, both is_for_file_name and is_for_trouble must be 
True so that the logic results in the replacement of those chars with space rather than using a dictionary char

@return data_to_convert the changed or unchanged data
"""


def convert(main_screen, data_to_convert, character_list, conversion_dict, is_for_file_name=False, is_for_trouble=False):
    old_data = data_to_convert
    screen_label = main_screen.ids.screen_label
    setup_screen_label(screen_label)

    for char in character_list:
        if char in data_to_convert:
            data_to_convert = data_to_convert.replace(char, conversion_dict[char]) if not is_for_file_name else data_to_convert.replace(char, "-") \
                if not is_for_trouble else data_to_convert.replace(char, " ")
    if old_data != data_to_convert and is_for_file_name and is_for_trouble is not True:
        screen_label.text = screen_label.text + f"\n{bcolors.FAIL}Error saving file with name {old_data}, saved as {data_to_convert} instead.{bcolors.ENDC}"
    return data_to_convert


"""
This function handles HTTP requests, and also handles errors that occur during those attempted connections
    - If there is an error, then system tries again after 10sec, then 30sec, and then stores the data
    that was to be uploaded in a file (backup.txt), to be attempted to upload again later on
@param context the URL/HTTP request
@param connection_type the type of connection/request to make (depends on the method caller)
@param content the content of the upload
@param file_name the name of the file to be uploaded
@param location the location that the file should be uploaded to
@param duplicate whether the file/data being uploaded already exists in the backup.txt or not

@return True if connection is successful, False if not
    - Returns binary file in the case of the 'qr_batch' connection_type
"""


def connect(main_screen, context, connection_type, content=None, file_name=None, location=None, duplicate=False):
    screen_label = main_screen.ids.screen_label
    setup_screen_label(screen_label)
    i = 0
    while i < 3:
        # noinspection PyBroadException
        try:
            return_val = True
            if connection_type == 'upload':  # if a file needs to be uploaded
                upload_file(ctx, content, file_name, location)
            elif connection_type == 'execute_query':  # if list item needs to be created and added
                context.execute_query()
            elif connection_type == 'qr_batch':  # if a file from the SharePoint needs to be retrieved (names.csv)
                return_val = File.open_binary(context, relative_url)
            else:
                screen_label.text = screen_label.text + f"\n{bcolors.WARNING}Invalid connection type.{bcolors.ENDC}"
                return_val = False
            if i > 0:
                screen_label.text = screen_label.text + f"\n{bcolors.OKGREEN}Connection successful.{bcolors.ENDC}"
            return return_val
        except:
            # e = sys.exc_info()[0]  # used for error checking
            # print(e, more)
            if i == 0:
                screen_label.text = screen_label.text + f"\n{bcolors.FAIL}Connection lost. Trying again in 10 seconds.{bcolors.ENDC}"
                time.sleep(10)
            elif i == 1:
                screen_label.text = screen_label.text + f"\n{bcolors.FAIL}Reconnect failed. Trying again in 30 seconds.{bcolors.ENDC}"
                time.sleep(30)
            elif i > 1 and not duplicate and connection_type != 'qr_batch':  # if failed thrice, write to backup.txt
                screen_label.text = screen_label.text + f"\n{bcolors.FAIL}Reconnect failed again.{bcolors.ENDC}{bcolors.OKBLUE} Data will be stored locally and " \
                      f"uploaded at the next upload point, or if triggered from the menu.{bcolors.ENDC}"
                if os.path.exists(backup_file) and connection_type == 'upload':
                    with open(backup_file, "a") as backup:
                        backup.write(f"{content}\n@@@@@\n{file_name}\n@@@@@\n{location}\n----------\n")
                elif connection_type == 'upload':
                    with open(backup_file, "w") as backup:
                        backup.write(f"{content}\n@@@@@\n{file_name}\n@@@@@\n{location}\n----------\n")
                elif connection_type == 'execute_query':
                    with open(backup_file, "a") as backup:
                        backup.write(f"$$$$$\n{content}\n----------\n")
                return False
            elif i > 1 and connection_type == 'qr_batch':
                screen_label.text = screen_label.text + f"\n{bcolors.FAIL}Reconnect failed again.{bcolors.OKBLUE} Try again when you have " \
                      f"internet connection.{bcolors.ENDC}{bcolors.ENDC}"
                return False
        i += 1


"""
This function uploads the data that was stored/backed up in the backup.txt file

@param context the URL/HTTP request information for uploading
@param from_menu True if this method was triggered/called from the main menu, False otherwise

@return True if re-upload was successful, False otherwise (or if there was no data to upload)
"""


def upload_backup(context, main_screen_widget, from_menu=False):
    screen_label = main_screen_widget.ids.screen_label
    setup_screen_label(screen_label)
    if os.path.exists(backup_file):  # check if file exists, if not then return
        with open(backup_file, "r") as backup:
            screen_label.text = screen_label.text + "\nUploading backed up data..."
            content = ""  # the content of the file that will be uploaded
            file_name = ""  # the file name of the file to upload
            location = ""  # the location to upload the file to
            flag = 0  # this tells program whether we are looking at content, filename, or location information
            for line in backup:  # for each line, take the appropriate action according to what is read in
                if line == '\n': continue
                if line == '@@@@@\n': flag += 1; continue
                if line == '$$$$$\n': flag = 3; continue
                if line == '----------\n':
                    if flag == 3:  # means it was a list item
                        successful = create_list_item(main_screen_widget, context, content, True)
                    else:  # means it was a file to be uploaded
                        successful = connect(main_screen_widget, context, 'upload', content, file_name, location, True)
                    if not successful:
                        screen_label.text = screen_label.text + f"\n{bcolors.FAIL}Upload of backed up data failed.{bcolors.ENDC}{bcolors.OKBLUE} Program will " \
                                                        f"try again at next upload, or you can trigger upload manually from the menu.{bcolors.ENDC}"
                        return False
                    flag = 0
                    content = ""
                    file_name = ""
                    location = ""
                    continue
                if flag == 0 or flag == 3:
                    content = content + line
                elif flag == 1:
                    file_name = line.rstrip('\n')
                elif flag == 2:
                    location = line.rstrip('\n')
            screen_label.text = screen_label.text + f"\n{bcolors.OKGREEN}Upload complete!{bcolors.ENDC}"
        os.remove(backup_file)  # file removed if upload is successful
    elif from_menu:
        screen_label.text = screen_label.text + f"\n{bcolors.OKBLUE}No backed-up data to upload.{bcolors.ENDC}"


"""
This function Creates a list item, used with the SharePoint site and the Office365-REST-Python-Client
@param context the context of the site that is being communicated with/uploaded to
@param content the content to add as a list item
"""


def create_list_item(main_screen, context, content, duplicate=False):
    screen_label = main_screen.ids.screen_label
    setup_screen_label(screen_label)

    screen_label.text = screen_label.text + "\nCreating list item example..."
    list_object = context.web.lists.get_by_title(listTitle)
    values = content.split(",")
    sid = values[0]
    tstr = values[1]
    barstr = values[2]
    status = values[3]

    item_properties = {'__metadata': {'type': 'SP.Data.QR_x0020_TimestampsListItem'}, 'Title': barstr,
                       'QR_x0020_Terminal': sid, 'Time_x0020_Stamp': tstr, 'Info': status}
    item = list_object.add_item(item_properties)
    succeed = connect(main_screen, context, 'execute_query', content, duplicate=duplicate)
    if succeed:
        screen_label.text = screen_label.text + "\nList item '{0}' has been created.".format(item.properties["Title"])
    else:
        screen_label.text = screen_label.text + f"\n{bcolors.WARNING}List item '{item.properties['Title']}' has NOT been created.{bcolors.ENDC}"
    return succeed


"""
This function uploads the passed data to the SharePoint site in the specified sub folder with the given file name
@param context the context of the site that is being communicated with/uploaded to (URL, authorization, etc.)
@param file_content the content of the file to be uploaded
@param filename the name of the file
@param sub_folder the folder to put the file in

@return returns the reference to the file that was uploaded
"""


def upload_file(context, file_content, filename, sub_folder):
    list_title = "EOC Documents"
    library = context.web.lists.get_by_title(list_title)

    file_context = library.context
    info = FileCreationInformation()
    info.content = file_content
    info.url = filename
    info.overwrite = True

    # upload file to sub folder 'eoctest'
    target_file = library.rootFolder.folders.get_by_url(sub_folder).files.add(info)
    file_context.execute_query()

    return target_file


"""
This function creates QR codes in batches from a CSV file (defined in the global variables)
    -The function always checks and performs the QR code creation in its root folder first, and the generated codes
    are then stored in that same folder.
    -If the local choice was chosen, the codes are also stored in the location entered by the user
    -If the online/SharePoint choice was chosen, the function then also reads a CSV file (defined in global variables) 
    on the SharePoint site and generates QR Codes from that, which are stored in the same location as that CSV file
"""


def qr_batch(main_screen_widget):
    screen_label = main_screen_widget.ids.screen_label
    setup_screen_label(screen_label)
    screen_label.text = screen_label.text + "\n\nThe batch QR code function is used to automatically create multiple QR codes by referencing a .csv file." \
          "\n-If QR Toolbox is in local mode, the csv file must be stored in the root/origin folder, named 'names.csv'." \
          "\n The Tool will then automatically create QR codes for each line in the csv, and save each QR Code image to" \
          "\n the Tools root/origin folder." \
          "\n-If QR Toolbox is in online mode, the csv file must be stored on the SharePoint site where QR codes are" \
          "\n located, and must be named 'names.csv'. The Tool will then do the same as above, but will also store each" \
          "\n QR code image to the SharePoint site." \
          "\n-'names.csv' may consist of two columns 'first' & 'second'. The 'first' and 'second' columns could be " \
          "\n populated with participant's first and last names, or other information."

    # this code creates a batch of QR codes from a csv file stored in the local directory
    # QR code image size and input filename can be modified below

    success = True
    # This one creates the batch of QR codes in the same folder as this file
    if storageChoice == 'a':
        with open(localQRBatchFile) as csvfile:
            reader = csv.reader(csvfile)

            for row in reader:
                labeldata = row[0] if len(row) == 1 else row[0] + " " + row[1] if row[1] != '' else row[0]

                # convert special char to code character
                codeLabelData = convert(main_screen_widget, labeldata, special_characters, char_dict_special_to_code)

                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=10,
                    border=4)

                qr.add_data(codeLabelData)
                qr.make(fit=True)
                screen_label.text = screen_label.text + "\n\nCreating QR code: " + labeldata

                # draw QR image

                img = qr.make_image()
                qrFile = labeldata + ".jpg"
                qrFile = convert(main_screen_widget, qrFile, bad_file_name_list, None, True)  # remove special chars that can't be in filename
                img.save(qrFile)

                # open QR image and add qr data as name
                img = Image.open(qrFile)
                draw = ImageDraw.Draw(img)
                font = ImageFont.truetype("arial", 24)
                color = 0
                draw.text((37, 10), labeldata, font=font, fill=color)
                img.save(qrFile)
                if storageChoice == 'a':
                    try:
                        img.save(storagePath + "/" + qrFile)
                    except:
                        success = False
    elif storageChoice == 'b':  # For storing the new QR Codes online, if that was selected
        resp = connect(main_screen_widget, ctx, 'qr_batch')  # runs the retrieval of the names.csv file from SharePoint through connect()

        if type(resp) == bool:  # if a boolean value is returned, then the retrieval failed
            return False
        elif resp.status_code == 404:
            screen_label.text = screen_label.text + f"\n\n{bcolors.FAIL}The batch file '" + relative_url + "' doesn't exist. " \
                f"Please copy 'names.csv' to the sharepoint site.{bcolors.ENDC}"
            return False

        with open(remoteQRBatchFile, 'wb') as output_file:
            output_file.write(resp.content)

        with open(remoteQRBatchFile) as csvfile:
            reader = csv.reader(csvfile)

            for row in reader:  # get each row from the CSV file
                labeldata = row[0] if len(row) == 1 else row[0] + " " + row[1] if row[1] != '' else row[0]
                # above: gets data from 1 row or 2 rows depending on what is in each

                # Check for special char
                if special_char_bool is False:
                    skip_label = False
                    for special_char in special_characters:
                        if special_char in labeldata:
                            skip_label = True
                    if skip_label:
                        screen_label.text = screen_label.text + "\nQR Code was skipped due to special character."
                        return

                # convert special char to code character
                codeLabelData = convert(main_screen_widget, labeldata, special_characters, char_dict_special_to_code)

                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=10,
                    border=4)

                qr.add_data(codeLabelData)
                qr.make(fit=True)
                screen_label.text = screen_label.text + "\nCreating QR code: " + labeldata

                # draw QR image

                img = qr.make_image()
                qrfile = labeldata + ".jpg"
                qrfile = convert(main_screen_widget, qrfile, bad_file_name_list, None, True)  # convert chars that can't be in filename
                img.save(qrfile)

                # open QR image and add qr data as name

                img = Image.open(qrfile)
                draw = ImageDraw.Draw(img)
                font = ImageFont.truetype("arial", 18)
                color = 0
                draw.text((37, 10), labeldata, font=font, fill=color)
                img.save(qrfile)

                with open(qrfile, 'rb') as content_file:  # upload file
                    file_content = content_file.read()
                success = connect(main_screen_widget, ctx, 'upload', file_content, qrfile, qrfolder)

        os.remove(remoteQRBatchFile)

    if success:
        screen_label.text = screen_label.text + f"\n\n{bcolors.OKGREEN}Success!{bcolors.ENDC}\n"
        if storageChoice == 'b':  # if the other upload was successful, also try to upload the backed-up data
            upload_backup(ctx, main_screen_widget)
    else:
        screen_label.text = screen_label.text + f"\n{bcolors.FAIL}Some or no files were saved in {storagePath}, only in root folder.{bcolors.ENDC}" if \
            storageChoice == 'a' else screen_label.text + f"\n{bcolors.WARNING}Some or no files were saved in {storagePath}, only in root folder.{bcolors.ENDC}"



"""
This function creates a single QR code based on the text inserted by the user, which is then stored in the root folder.
    - If user chose the local option, the QR code is also stored in the location entered by the user
    - If user chose the online SharePoint option, the QR code is stored on the SharePoint site
"""


def qr_single(main_screen_widget, text):
    screen_label = main_screen_widget.ids.screen_label
    setup_screen_label(screen_label)

    if storageChoice == 'b' and special_char_bool is False:
        skip_label = False
        for special_char in special_characters:
            if special_char in text:
                skip_label = True
        if skip_label:
            screen_label.text = screen_label.text + "\nQR Code was skipped due to special character."
            return

    text_copy = text
    screen_label.text = screen_label.text + "\nCreating QR code: " + text

    # convert special char to code character
    text_copy = convert(main_screen_widget, text_copy, special_characters, char_dict_special_to_code)

    # this code creates a single QR code based on information entered into the command line.
    # The resulting QR code is stored in the current (the programs') directory
    # QR code image size and input filename can be modified below
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4)

    qr.add_data(text_copy)
    qr.make(fit=True)

    # draw label

    img = qr.make_image()
    fileName = text + ".jpg"
    fileName = convert(main_screen_widget, fileName, bad_file_name_list, None, True)  # convert chars that can't be in a file name
    img.save(fileName)

    # Open QR image and add QR data as name

    img = Image.open(fileName)
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype("arial", 24)
    color = 0
    draw.text((37, 10), text, font=font, fill=color)
    img.save(fileName)

    succeed = True
    # Store QR code locally, if that was chosen
    if storageChoice == 'a':
        try:
            img.save(storagePath + "/" + fileName)
        except:
            succeed = False
    elif storageChoice == 'b':  # Store QR code online, if chosen
        # upload file
        with open(fileName, 'rb') as content_file:
            file_content = content_file.read()
        succeed = connect(main_screen_widget, ctx, 'upload', file_content, fileName, qrfolder)

    if succeed:
        screen_label.text = screen_label.text + f"\n{bcolors.OKGREEN}Success!{bcolors.ENDC}"
        if storageChoice == 'b':
            upload_backup(ctx, main_screen_widget)  # if the other upload was successful, also try to upload the backed-up data
    else:
        screen_label.text = screen_label.text + f"\n{bcolors.FAIL}File not saved in {storagePath}, only in root folder.{bcolors.ENDC}" if \
            storageChoice == 'a' else screen_label.text + f"\n{bcolors.WARNING}Successful locally, not online.{bcolors.ENDC}"


"""
This function consolidates QR csv results into a single file. This function looks for files with QRT in the first part 
of their name. If true, all csvs within the shared folder directory that also fit this condition. A number of error
checks are built in to prevent bad things from happening
"""


def cons(main_screen_widget):
    screen_label = main_screen_widget.ids.screen_label
    setup_screen_label(screen_label)

    time_header = str(datetime.datetime.now().strftime('%Y_%m_%d_%H_%M_%S'))
    cons_filename = os.path.join(storagePath, 'Consolidated_Record_' + time_header + '.csv')
    if os.path.exists(storagePath):
        QRT_files = [fn for fn in os.listdir(storagePath) if fn.startswith('QRT')]

        if not QRT_files:
            screen_label.text = screen_label.text + "\nNo entries to combine. Check the shared directory and try again"
        else:
            try:
                with open(cons_filename, 'wb') as outfile:
                    for i, fname in enumerate(QRT_files):
                        fname = os.path.join(storagePath, fname)
                        with open(fname, 'rb') as infile:
                            shutil.copyfileobj(infile, outfile)
                            screen_label.text = screen_label.text + f"\n{fname} has been imported."
                screen_label.text = screen_label.text + f"\n{bcolors.OKGREEN}\nConsolidated file created in the specified shared drive under " \
                                                        f"the filename " + cons_filename + f"{bcolors.ENDC}\n"
            except:
                screen_label.text = screen_label.text + f"\n{bcolors.WARNING}[WARNING] Either the system was unable to write the consolidated file " \
                                                        f"to the specified shared directory or the file " + cons_filename + " is currently in use " \
                                                        f"or unavailable. The consolidated record may be incomplete.{bcolors.ENDC}\n"
    else:
        screen_label.text = screen_label.text + f"\n{bcolors.WARNING}A shared folder has not been established. Specify a shared folder using the " \
              f"Establish Share Folder option before continuing\n{bcolors.ENDC}"
        pass


# MAIN PART OF PROGRAM STARTS HERE

from kivy.uix.scatter import Scatter
from kivy.uix.label import Label
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.modalview import ModalView
from kivy.uix.scrollview import ScrollView
import kivy.core.window as window
from kivy.config import Config
from kivy.properties import ListProperty, ObjectProperty

from kivy.graphics.vertex_instructions import (Rectangle, Ellipse, Line)
from kivy.graphics.context_instructions import Color

from kivy.base import EventLoop


"""
This function allows the user to select a shared folder. If user escapes, a share folder is not created
    - Note: the Tkinter code can be finicky when displayed in IDE i.e., the file window will not show when operated in
    IDE while the root.withdraw command is turned on. Commenting out the root.withdraw command will fix, but root
    window remains; destroy() can be used to remove this. May need to search for a better solution in the future
"""


def store(main_screen, just_starting=False):
    screen_label = main_screen.ids.screen_label
    setup_screen_label(screen_label, just_starting)

    root = Tk()
    root.title('Storage Directory')
    root.withdraw()
    store_path = filedialog.askdirectory(title='Select a Network Storage Directory')
    if os.path.exists(store_path):
        screen_label.text = screen_label.text + f"\n{bcolors.OKGREEN}Storage directory established: {store_path}{bcolors.ENDC}"
    else:
        screen_label.text = screen_label.text + f"\n{bcolors.WARNING}Storage directory NOT established{bcolors.ENDC}"
    return store_path


def setup_screen_label(screen_label, just_starting=False):
    if screen_label.text == f"\n\n[size=50][u][color=#009999]QR TOOLBOX[/color][/size][/u]\n\n\n\n\n\n[size=30]QR Toolbox v1.3\n\nUSEPA Homeland Security Research Program\n\nSystem ID: {system_id}[/size]\n" and not just_starting:
        screen_label.text = ""
    elif screen_label.text == "QR Toolbox v1.3 \nAbout: The QR Toolbox is a suite a tools for creating and reading QR codes. The toolbox is platform " \
          "agnostic, lightweight, open source, and written in pure Python. This toolbox may be used to track resources," \
          " serve as a check-in capability for personnel, or customized to meet other operational needs. \n" + "Version: 1.3 \n\nCredits: The QR Toolbox consists of a number of python packages, namely: \n qrcode - " \
          "Lincoln Loop info@lincolnloop.com; \n pyzbar - Lawrence Hudson quicklizard@googlemail.com; \n OpenCV code - " \
          "Adrian Rosebrock https://www.pyimagesearch.com/author/adrian/; \n Code integration, minor enhancements, & " \
          "platform development - Timothy Boe boe.timothy@epa.gov \nContact: Timothy Boe: boe.timothy@epa.gov; or Paul Lemieux: lemieux.paul@epa.gov; USEPA Homeland Security " \
          "Research Program \n":
        screen_label.text = ""
    elif screen_label.text[0:210] == f"\n\n[size=50][u][color=#009999]QR TOOLBOX[/color][/size][/u]\n\n\n\n\n\n[size=30]QR Toolbox v1.3\n\nUSEPA Homeland Security Research Program\n\nSystem ID: {system_id}[/size]\n" + f"\n{bcolors.OKGREEN}Storage directory established":
        screen_label.text = ""

    if not just_starting:
        screen_label.halign = 'left'



class MainScreenWidget(BoxLayout):
    sys_id = os.environ["COMPUTERNAME"]


    """
    This function starts a VideoStream, and captures any QR Codes it sees (in a certain distance)
    Those codes are decoded, and written to a local CSV file along with the Computer Name, date, time, and IN/OUT
        -If local was chosen, the CSV file is also saved at the location entered by the user
        -If online was chosen, the CSV file is also saved on the SharePoint site
    """

    def video(self):
        global not_done, user_chose_storage

        while not_done:
            pass

        screen_label = self.ids.screen_label
        setup_screen_label(screen_label)
        screen_label.text = screen_label.text + f"\n{bcolors.OKBLUE}[ALERT] Starting video stream...{bcolors.ENDC}\n"
        screen_label.text = screen_label.text + f"{bcolors.OKBLUE}Press 'Q' to exit{bcolors.ENDC}"

        if user_chose_storage:
            # construct the argument parser and parse the arguments
            ap = argparse.ArgumentParser()
            ap.add_argument("-o", "--output", type=str, default="System_Data/barcodes.txt",
                            help="path to output CSV file containing barcodes")
            # ap.add_argument("-o1", "--output2", type=str, default=files_name,
            #        help="path to output CSV file containing barcodes")
            args = vars(ap.parse_args())
            # initialize time and date and make filename friendly
            time_header = str(datetime.datetime.now().strftime('%Y_%m_%d_%H_%M_%S'))
            file_name = "QRT" + "-" + system_id + "_" + time_header + ".csv"

            # initialize the video stream and allow the camera sensor to warm up

            if cameraSource == 'a':  # start correct camera based on user choice at beginning
                vs = VideoStream(src=0).start()  # for integrated/built in webcam
            elif cameraSource == 'b':
                vs = VideoStream(src=1).start()  # for separate webcam (usually USB connected)
            elif cameraSource == 'c':
                vs = VideoStream(usePiCamera=True).start()  # for mobile solution like Raspberry Pi Camera
            else:
                screen_label.text = screen_label.text + f"\n{bcolors.FAIL}An error has occurred.{bcolors.ENDC}"
                return

            time.sleep(5.0)  # give camera time

            # open the output txt file for writing and initialize the set of barcodes found thus far
            global checkStorage
            contentStrings = ""  # used to contain data recorded from qr codes, to save in files
            if os.path.isfile(args["output"]) and checkStorage:  # check if user wanted to restart prev session
                if storageChoice.lower() == 'b':  # do this only if QR Toolbox is in online-mode
                    # Write previous records back to contentStrings
                    with open(args["output"], "r") as txt:
                        screen_label.text = screen_label.text + f"\n{bcolors.OKBLUE}Restoring records...{bcolors.ENDC}"
                        for line in txt:  # get each record from the file by line
                            if line == '\n': continue  # if line is newline only then skip it
                            line_array = line.split(",")
                            last_system_id = line_array[0]
                            date_time = datetime.datetime.strptime(line_array[1], "%Y-%m-%d %H:%M:%S.%f")  # get date from file
                            date_time_online = f"{date_time.month}/{date_time.day}/{date_time.year} " \
                                               f"{date_time.hour}:{date_time.minute}"  # store in this format: "%m/%d/%Y %H:%M"

                            barcodeDataSpecial = line_array[2]  # get the QR Code from the file
                            status = line_array[3]  # get the status from the file
                            if "OUT" in status:  # if the status is OUT, also get the QRCodes' duration from the file
                                duration = line_array[4][:len(line_array[4]) - 1:]  # also remove newline char
                            else:
                                status = status[:len(status) - 1]  # else just remove the newline char from the status

                            # Convert barcodeDataSpecial's special chars to regular chars
                            barcodeDataReg = convert(self, barcodeDataSpecial, special_characters, char_dict_special_to_reg)

                            if status == "IN":  # if status is IN, use 4 params
                                contentstr = "{},{},{},{}\n".format(last_system_id, date_time_online,
                                                                    barcodeDataReg, status)  # for online CSV file
                                contentstr2 = '{},{},{},{}\n'.format(last_system_id, date_time,
                                                                     barcodeDataSpecial, status)  # for list item
                            else:  # if status is OUT, use 5 params
                                contentstr = "{},{},{},{},{}\n".format(last_system_id, date_time_online, barcodeDataReg,
                                                                       status, duration)  # for online CSV file
                                contentstr2 = '{},{},{},{},{}\n'.format(last_system_id, date_time,
                                                                        barcodeDataSpecial, status, duration)  # for list item
                            create_list_item(self, ctx, contentstr2)
                            contentStrings = contentStrings + contentstr

                txt = open(args["output"], "a", encoding="utf-8")  # reopen txt file for appending (to continue records)
                screen_label.text = screen_label.text + f"\n{bcolors.OKBLUE}Previous records restored.{bcolors.ENDC}"
            else:
                txt = open(args["output"], "w", encoding="utf-8")  # else open new file/overwrite previous
                if checkStorage:
                    screen_label.text = screen_label.text + f"\n{bcolors.WARNING}No previous records found. CSV file will not include " \
                                                            f"past records.{bcolors.ENDC}"

            # time track variables. These are used to keep track of QR codes as they enter the screen
            found = []
            found_time = []
            found_status = []
            # ctxAuth = AuthenticationContext(url=settings['url'])

            # Check if there are any stored QR codes that were scanned in in an earlier instance of the system
            if checkStorage:
                if os.path.exists(qr_storage_file):
                    with open(qr_storage_file, "r") as qr_data_file:
                        for line in qr_data_file:  # if yes, read them in line by line
                            if line == '\n': continue
                            line_array = line.split(",")
                            found.append(line_array[0])  # append file data to the found arrays
                            found_time.append(datetime.datetime.strptime(line_array[1], "%Y-%m-%d %H:%M:%S.%f"))
                            found_status.append(line_array[2][:len(line_array[2]) - 1:])
                        screen_label.text = screen_label.text + f"\n{bcolors.OKBLUE}Previous session restarted.{bcolors.ENDC}"
                else:
                    screen_label.text = screen_label.text + f"\n{bcolors.WARNING}No previous session found [qr-data.txt not found].{bcolors.ENDC}"

            # loop over the frames from the video stream
            while True:
                # grab the frame from the threaded video stream and resize it to
                # have a maximum width of 400 pixels
                frame = vs.read()
                frame = imutils.resize(frame, width=400)

                # find the barcodes in the frame and decode each of the barcodes
                barcodes = pyzbar.decode(frame, symbols=[ZBarSymbol.QRCODE])
                timestr = strftime("%m/%d/%Y %H:%M")

                # loop over the detected barcodes
                for barcode in barcodes:
                    # extract the bounding box location of the barcode and draw
                    # the bounding box surrounding the barcode on the image
                    (x, y, w, h) = barcode.rect
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)

                    # the barcode data is a bytes object so if we want to draw it
                    # on our output image we need to convert it to a string first
                    barcodeData = barcode.data.decode("utf-8")
                    barcodeType = barcode.type

                    # Convert barcodeData code chars back to special chars
                    barcodeData = convert(self, barcodeData, code_characters, char_dict_code_to_special)

                    # Draw the barcode data and barcode type on the image
                    img = Image.new('RGB', (400, 15), color='white')
                    img.putalpha(0)
                    d = ImageDraw.Draw(img)
                    textToPrint = convert(self, barcodeData, trouble_characters, None, True, True)  # replace \t,\n,\r with ' '
                    try:
                        d.text((0, 0), textToPrint + ' (' + barcodeType + ')', fill='blue')
                    except UnicodeEncodeError:
                        screen_label.text = screen_label.text + f"\n{bcolors.FAIL}[ERROR] Can't use QR Codes not generated by the system.{bcolors.ENDC}"
                        continue

                    pil_image = Image.fromarray(frame)
                    pil_image.paste(img, box=(x, y - 15), mask=img)
                    frame = np.array(pil_image)

                    # if the barcode text is currently not in our CSV file, write
                    # the timestamp + barcode to disk and update the set
                    # of barcode data has never been seen, check the user in and record id, date, and time information
                    if barcodeData not in found:
                        datetime_scanned = datetime.datetime.now()
                        txt.write("{},{},{},{}\n".format(system_id, datetime_scanned,
                                                         barcodeData, "IN"))
                        txt.flush()

                        found.append(barcodeData)
                        found_time.append(datetime_scanned)
                        found_status.append("IN")

                        # Write updated found arrays to qr_data_file so that it is up to date with the latest scan ins
                        with open(qr_storage_file, "w") as qr_data_file:
                            for i in range(len(found)):
                                code = found[i]
                                tyme = found_time[i]
                                status = found_status[i]
                                qr_data_file.write("{0},{1},{2}\n".format(code, tyme, status))

                        checked_in = True
                        if storageChoice.lower() == 'b':  # if user chose online/Sharepoint
                            # Convert barcodeData's special chars to regular chars
                            barcodeDataNew = convert(self, barcodeData, special_characters, char_dict_special_to_reg)

                            contentstr = "{},{},{},{}\n".format(system_id, timestr, barcodeDataNew, "IN")  # for online CSV file
                            contentstr2 = '{},{},{},{}\n'.format(system_id, timestr, barcodeData, "IN")  # for list item
                            checked_in = create_list_item(self, ctx, contentstr2)
                            contentStrings = contentStrings + contentstr

                        sys.stdout.write('\a')  # beeping sound
                        sys.stdout.flush()
                        if checked_in:
                            screen_label.text = screen_label.text + f"\n{barcodeData} checking IN at {str(datetime_scanned)} at location: {system_id}"

                    # if barcode information is found...
                    elif barcodeData in found:
                        # get current time and also total time passed since user checked in
                        datetime_scanned = datetime.datetime.now()
                        time_check = datetime_scanned - found_time[found.index(barcodeData)]
                        status_check = found_status[found.index(barcodeData)]

                        # if time exceeds wait period and user is checked in then check them out
                        if time_check > t_value and status_check == "IN":
                            index_loc = found.index(barcodeData)
                            found_status[index_loc] = "OUT"
                            found_time[index_loc] = datetime_scanned
                            txt.write("{},{},{},{},{}\n".format(system_id, datetime_scanned,
                                                                barcodeData, "OUT", time_check))  # write to local CSV file
                            txt.flush()

                            checked_out = True
                            if storageChoice.lower() == 'b':  # if user chose online/Sharepoint version
                                barcodeDataNew = convert(self, barcodeData, special_characters, char_dict_special_to_reg)
                                # (above) convert qr code text special chars to reg chars
                                contentstr = "{},{},{},{},{}\n".format(system_id, timestr, barcodeDataNew, "OUT", time_check)
                                contentstr2 = "{},{},{},{},{}\n".format(system_id, timestr, barcodeData, "OUT",
                                                                        time_check)

                                checked_out = create_list_item(self, ctx, contentstr2)
                                contentStrings = contentStrings + contentstr

                            sys.stdout.write('\a')  # When this letter is sent to terminal, a beep sound is emitted but no text
                            sys.stdout.flush()
                            if checked_out:
                                screen_label.text = screen_label.text + f"\n{barcodeData} checking OUT at {str(datetime_scanned)} at location: " \
                                                                        f"{system_id} for duration of {str(time_check)}"
                        # if found and check-in time is less than the specified wait time then wait
                        elif time_check < t_value and status_check == "OUT":
                            pass
                        # if found and time check exceeds specified wait time and user is checked out, delete ID and affiliated
                        # data from the list. This resets everything for said user and allows the user to check back in at a
                        # later time.
                        elif time_check > t_value and status_check == "OUT":
                            index_loc = found.index(barcodeData)
                            del found_status[index_loc]
                            del found_time[index_loc]
                            del found[index_loc]

                        # Write updated found arrays to qr_data_file so that it is up to date with the latest scan ins
                        with open(qr_storage_file, "w") as qr_data_file:
                            for i in range(len(found)):
                                code = found[i]
                                tyme = found_time[i]
                                status = found_status[i]
                                qr_data_file.write("{0},{1},{2}\n".format(code, tyme, status))
                    else:
                        screen_label.text = screen_label.text + f"\n{bcolors.FAIL}[Error] Barcode data issue in video() function.{bcolors.ENDC}"

                # show the output frame
                cv2.imshow("QR Toolbox", frame)
                key = cv2.waitKey(1) & 0xFF

                # if the `q` key was pressed, break from the loop
                if key == ord("q") or key == ord("Q"):
                    break

            # close the output CSV file and do a bit of cleanup
            screen_label.text = screen_label.text + f"\n{bcolors.OKBLUE}[ALERT] Cleaning up... \n{bcolors.ENDC}"
            txt.close()

            if os.path.exists(qr_storage_file) and os.stat(qr_storage_file).st_size == 0:
                os.remove(qr_storage_file)  # if the file is empty, delete it
            checkStorage = False  # Reset the global variable that tells code to check the qr_storage_file

            # This part is necessary to show special characters properly on any of the local CSVs
            if os.path.exists(args["output"]):
                barcodesTxt = open(args["output"], 'r', encoding="utf-8")
                newCSV = open(file_name, 'w', encoding="ANSI")

                data = barcodesTxt.read()
                newCSV.write(data)

                barcodesTxt.close()
                newCSV.close()
            else:
                data = f"\n{bcolors.FAIL}[ERROR] barcodes.txt not found as expected.{bcolors.ENDC}"
                screen_label.text = screen_label.text + data

            if storageChoice == 'a':  # if local was chosen, also store barcodes file at the location given
                if os.path.exists(storagePath):  # check if file path exists
                    with open(os.path.join(storagePath, file_name), "w", encoding="ANSI") as csv2:
                        csv2.write(data)
                else:
                    screen_label.text = screen_label.text + f"\n{bcolors.WARNING}[ALERT]: Storage folder not established or is unavailable. " \
                          f"Files will only be saved to the working directory\n{bcolors.ENDC}"
            elif storageChoice.lower() == 'b':  # if online was chosen, upload data to SharePoint as well
                success = connect(self, ctx, 'upload', contentStrings, file_name, bkcsvfolder)
                if success:
                    upload_backup(ctx, self)

            if os.path.exists(args["output"]) and os.stat(args["output"]).st_size == 0:  # delete barcodes.txt if empty
                os.remove(args["output"])  # not removed until the end in case something goes wrong above and it's needed
            vs.stop()
            vs.stream.release()
            cv2.destroyAllWindows()

            not_done = True  # set these so qr reader waits on user choice before starting video
            user_chose_storage = False


    def qr_reader(self):
        restart_session_popup = RestartSessionWidget()
        restart_session_popup.restart_popup = Popup(title="Do you want to start a new session or restart the previous one?",
                      content=restart_session_popup, size_hint=(None, None), size=(725, 170), auto_dismiss=True)
        restart_session_popup.restart_popup.open()
        restart_session_popup.main_screen = self
        threading.Thread(target=self.video, daemon=True).start()


    def qr_batch(self):
        qr_batch(self)


    def qr_single(self):
        qr_single_widget = QRSingleWidget()
        qr_single_widget.qr_single_popup = Popup(
            title="Enter text to generate a single QR Code and click OK. The resulting image will be saved in the "
                  "tool's origin folder, and selected storage location.", content=qr_single_widget,
            size_hint=(None, None), size=(327, 290), auto_dismiss=True)
        qr_single_widget.main_screen = self
        qr_single_widget.qr_single_popup.open()


    def setup(self):
        setup_popup = SetupWidget()
        setup_popup.setup_popup = Popup(title="Choose an option", content=setup_popup, size_hint=(None, None), size=(251, 475),
                                        auto_dismiss=True)
        setup_popup.main_screen = self
        setup_popup.setup_popup.open()


    """
    This function provides more information on the purpose and development of this software
    """


    def about(self):
        # displays the about screen
        text = "QR Toolbox v1.3 \n"
        text = text + "About: The QR Toolbox is a suite a tools for creating and reading QR codes. The toolbox is platform " \
              "agnostic, lightweight, open source, and written in pure Python. This toolbox may be used to track resources," \
              " serve as a check-in capability for personnel, or customized to meet other operational needs. \n"
        text = text + "Version: 1.3 \n\n"
        text = text + "Credits: The QR Toolbox consists of a number of python packages, namely: \n qrcode - " \
              "Lincoln Loop info@lincolnloop.com; \n pyzbar - Lawrence Hudson quicklizard@googlemail.com; \n OpenCV code - " \
              "Adrian Rosebrock https://www.pyimagesearch.com/author/adrian/; \n Code integration, minor enhancements, & " \
              "platform development - Timothy Boe boe.timothy@epa.gov \n"
        text = text + "Contact: Timothy Boe: boe.timothy@epa.gov; or Paul Lemieux: lemieux.paul@epa.gov; USEPA Homeland Security " \
              "Research Program \n"
        label = self.ids.screen_label
        label.text = text
        label.font_size = 18
        label.valign = 'middle'
        label.halign = 'center'


    def exit(self):
        self.get_root_window().close()
        exit(0)


class RestartSessionWidget(BoxLayout):
    restart_popup = None
    main_screen = None

    def set_check_storage(self, check):
        global not_done, user_chose_storage
        screen_label = self.main_screen.ids.screen_label
        setup_screen_label(screen_label)
        if check:
            global checkStorage
            checkStorage = True
            screen_label.text = screen_label.text + f"\n{bcolors.OKBLUE}Previous session will be restarted, if one exists.{bcolors.ENDC}"
        user_chose_storage = True
        not_done = False


class StorageWidget(BoxLayout):
    text = "Do you want data stored on Sharepoint (online) or locally? \nNote: Files are also saved in the QR-Toolbox root folder regardless."
    storage_popup = None
    main_screen = None
    just_starting = False


    def set_storage(self, storage):
        global storageChoice
        if storage:  # Local button was pressed
            global storagePath
            storageChoice = "a"
            storagePath = store(self.main_screen, self.just_starting)
        elif not storage:
            storageChoice = "b"


class CameraWidget(BoxLayout):
    text = "Which camera do you want to use?"
    camera_popup = None


    """
    This function asks the user what camera will be used to read QR Codes
    Only 3 options
        1. A - integrated/built-in webcam (the default)
        2. B - USB or connected webcam
        3. C - PiCamera (from Raspberry Pi)
    """


    def set_camera(self, camera_choice):
        global cameraSource
        cameraSource = camera_choice


class SetupWidget(BoxLayout):
    setup_popup = None
    main_screen = None
    
    
    def upload_consolidate(self):
        if storageChoice == 'a':
            cons(self.main_screen)
        else:
            upload_backup(ctx, self.main_screen)


    def change_storage_location(self):
        storage_location = StorageWidget()
        storage_location.storage_popup = Popup(title="Select a storage location", content=storage_location, size_hint=(None, None),
                                               size=(500, 400), auto_dismiss=True)
        storage_location.main_screen = self.main_screen
        storage_location.storage_popup.open()


    def change_camera_source(self):
        camera_location = CameraWidget()
        camera_location.camera_popup = Popup(title="Which camera do you want to use?", content=camera_location, size_hint=(None, None),
                                               size=(261, 375), auto_dismiss=True)
        camera_location.camera_popup.open()


    def set_special_character_conversion(self):
        special_char_widget = AskSpecialCharConversionWidget()
        special_char_widget.special_char_popup = Popup(title="Do you want to allow conversion of QR Codes with special characters? (Only affects QR "
        "Creator functions when using Sharepoint storage.)", content=special_char_widget, size_hint=(None, None), size=(375, 300), auto_dismiss=True)
        special_char_widget.special_char_popup.open()


class QRSingleWidget(BoxLayout):
    qr_single_popup = None
    main_screen = None

    def setup_qr_single(self, text):
        qr_single(self.main_screen, text)


class AskSpecialCharConversionWidget(BoxLayout):
    special_char_popup = None


    def set_special_char_bool(self, ask_bool):
        global special_char_bool
        special_char_bool = ask_bool  # True if user says yes, False if user says no


class ScreenWidget(ScrollView):
    pass


class QRToolboxApp(App):
    main_screen = None


    def build(self):
        self.main_screen = MainScreenWidget()
        return self.main_screen


    def on_start(self):
        storage_location = StorageWidget()
        storage_location.storage_popup = Popup(title="Select a storage location", content=storage_location, size_hint=(None, None),
                                               size=(500, 400), auto_dismiss=False)
        storage_location.main_screen = self.main_screen
        storage_location.just_starting = True
        storage_location.storage_popup.open()
        pass


if __name__ == '__main__':
    check_versions()  # Check Python and module versions
    QRToolboxApp().run()
