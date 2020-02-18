# -*- coding: windows-1252 -*-
# Name: QR Toolbox v2a
# Description: The QR Toolbox is a suite a tools for creating and reading QR codes. See the About screen for more
# information
# Author(s): Code integration, minor enhancements, & platform development - Timothy Boe boe.timothy@epa.gov;
# qrcode - Lincoln Loop info@lincolnloop.com; pyzbar - Lawrence Hudson quicklizard@googlemail.com;
# OpenCV code - Adrian Rosebrock https://www.pyimagesearch.com/author/adrian/;
# Contact: Timothy Boe boe.timothy@epa.gov
# Requirements: Python 3, pyzbar, imutils, opencv-python, qrcode[pil]

# import the necessary packages
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

from settings import settings

# Sharepoint related variables
listTitle = "QR Timestamps"
qrfolder = "QRCodes"
bkcsvfolder = "HXWTEST"
remoteQRBatchFile = "names-remote.csv"
localQRBatchFile = "names.csv"
relative_url = "/sites/Emergency%20Response/EOCIncident/EOC%20Documents/QRCodes/names_test.csv"

context_auth = AuthenticationContext(url=settings['url'])
context_auth.acquire_token_for_app(client_id=settings['client_id'], client_secret=settings['client_secret'])
ctx = ClientContext(settings['url'], context_auth)

# load variables
# set store folder default, assign system ID, and wait time
storagePath = "None"
system_id = os.environ['COMPUTERNAME']
t_value = timedelta(seconds=10)

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

# display landing screen

print("     _/_/      _/_/_/        _/_/_/_/_/                    _/  _/                   ")
print("  _/    _/    _/    _/          _/      _/_/      _/_/    _/  _/_/_/      _/_/    _/    _/")
print(" _/  _/_/    _/_/_/            _/    _/    _/  _/    _/  _/  _/    _/  _/    _/    _/_/  ")
print("_/    _/    _/    _/          _/    _/    _/  _/    _/  _/  _/    _/  _/    _/  _/    _/  ")
print(" _/_/  _/  _/    _/          _/      _/_/      _/_/    _/  _/_/_/      _/_/    _/    _/ \n")
print("QR Toolbox v2a \n")
print("The QR Toolbox is a suite a tools for creating and reading QR codes.\n")
print("USEPA Homeland Security Research Program \n")
print("System ID: " + system_id + "\n")

"""
This function starts a VideoStream, and captures any QR Codes it sees (in a certain distance)
Those codes are decoded, and written to a local CSV file along with the Computer Name, date, time, and IN/OUT
    -If local was chosen, the CSV file is also saved at the location entered by the user
    -If online was chosen, the CSV file is also saved on the SharePoint site
"""


def video():
    # construct the argument parser and parse the arguments
    ap = argparse.ArgumentParser()
    ap.add_argument("-o", "--output", type=str, default="barcodes.txt",
                    help="path to output CSV file containing barcodes")
    # ap.add_argument("-o1", "--output2", type=str, default=files_name,
    #        help="path to output CSV file containing barcodes")
    args = vars(ap.parse_args())
    # initialize time and date and make filename friendly
    time_header = str(datetime.datetime.now().strftime('%Y_%m_%d_%H_%M_%S'))
    file_name = "QRT" + "-" + system_id + "_" + time_header + ".csv"

    # initialize the video stream and allow the camera sensor to warm up
    print("[ALERT] starting video stream...")
    print("Press 'Q' to exit")

    if cameraChoice == 'a':  # start correct camera based on user choice at beginning
        vs = VideoStream(src=0).start()  # for integrated/built in webcam
    elif cameraChoice == 'b':
        vs = VideoStream(src=1).start()  # for separate webcam (usually USB connected)
    elif cameraChoice == 'c':
        vs = VideoStream(usePiCamera=True).start()  # for mobile solution like Raspberry Pi Camera
    else:
        print("An error has occurred.")
        return

    time.sleep(5.0)  # give camera time

    # open the output CSV file for writing and initialize the set of barcodes found thus far
    csv = open(args["output"], "w", encoding="utf-8")

    # time track variables. These are used to keep track of QR codes as they enter the screen
    found = []
    found_time = []
    found_status = []
    # ctxAuth = AuthenticationContext(url=settings['url'])

    contentStrings = ""  # Used to contain data recorded from video stream

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
            barcodeData = convert(barcodeData, code_characters, char_dict_code_to_special)

            # Draw the barcode data and barcode type on the image
            img = Image.new('RGB', (400, 15), color='white')
            img.putalpha(0)
            d = ImageDraw.Draw(img)
            textToPrint = convert(barcodeData, trouble_characters, None, True, True)  # replace \t,\n,\r with ' '
            try:
                d.text((0, 0), textToPrint + ' (' + barcodeType + ')', fill='blue')
            except UnicodeEncodeError:
                print("[ERROR] Can't use QR Codes not generated by the system.")
                # continue
                # or  ASK WHICH ONE WE SHOULD USE
                # close the output CSV file do a bit of cleanup
                print("[ALERT] Cleaning up... \n")
                csv.close()

                # This part is necessary to show special characters properly on any of the local CSVs
                barcodesTxt = open(args["output"], 'r', encoding="utf-8")
                newCSV = open(file_name, 'w', encoding="ANSI")

                data = barcodesTxt.read()
                newCSV.write(data)

                barcodesTxt.close()
                newCSV.close()
                os.remove(args["output"])

                if storageChoice == 'a':  # if local was chosen, also store barcodes file at the location given
                    if os.path.exists(storagePath):  # check if file path exists
                        csv2 = open(os.path.join(storagePath, file_name), "w",
                                    encoding="ANSI")
                        csv2.write(data)
                        csv2.close()
                    else:
                        print("Alert: Storage folder not established or is unavailable. Files will only be saved to the"
                            " working directory\n")

                elif storageChoice.lower() == 'b':  # if online was chosen, upload data to SharePoint as well
                    upload_file(ctx, contentStrings, file_name, bkcsvfolder)

                vs.stop()
                vs.stream.release()
                cv2.destroyAllWindows()
                return

            pil_image = Image.fromarray(frame)
            pil_image.paste(img, box=(x, y - 15), mask=img)
            frame = np.array(pil_image)

            # if the barcode text is currently not in our CSV file, write
            # the timestamp + barcode to disk and update the set
            # of barcode data has never been seen, check the user in and record id, date, and time information
            if barcodeData not in found:
                csv.write("{},{},{},{}\n".format(system_id, datetime.datetime.now(),
                                                 barcodeData, "IN"))
                csv.flush()
                if storageChoice.lower() == 'b':  # if user chose online/Sharepoint
                    # Convert barcodeData's special chars to regular chars
                    barcodeDataNew = convert(barcodeData, special_characters, char_dict_special_to_reg)

                    contentstr = "{},{},{},{}\n".format(system_id, timestr, barcodeDataNew, "IN")  # for online CSV file
                    contentstr2 = '{},{},{},{}\n'.format(system_id, timestr, barcodeData, "IN")  # for list item
                    create_list_item(ctx, contentstr2)
                    contentStrings = contentStrings + contentstr

                found.append(barcodeData)
                found_time.append(datetime.datetime.now())
                found_status.append("IN")
                sys.stdout.write('\a')  # beeping sound
                sys.stdout.flush()
                print(barcodeData + " checking IN at " + str(datetime.datetime.now()) + " at location: " + system_id)

            # if barcode information is found...
            elif barcodeData in found:
                # get current time and also total time passed since user checked in
                time_check = datetime.datetime.now() - found_time[found.index(barcodeData)]
                status_check = found_status[found.index(barcodeData)]

                # if time exceeds wait period and user is checked in then check them out
                if time_check > t_value and status_check == "IN":
                    index_loc = found.index(barcodeData)
                    found_status[index_loc] = "OUT"
                    found_time[index_loc] = datetime.datetime.now()
                    csv.write("{},{},{},{},{}\n".format(system_id, datetime.datetime.now(),
                                                        barcodeData, "OUT", time_check))  # write to local CSV file
                    csv.flush()

                    if storageChoice.lower() == 'b':  # if user chose online/Sharepoint version
                        barcodeDataNew = convert(barcodeData, special_characters, char_dict_special_to_reg)
                        # (above) convert qr code text special chars to reg chars
                        contentstr = "{},{},{},{},{}\n".format(system_id, timestr, barcodeDataNew, "OUT", time_check)
                        contentstr2 = "{},{},{},{},{}\n".format(system_id, timestr, barcodeData, "OUT",
                                                                time_check)

                        create_list_item(ctx, contentstr2)
                        contentStrings = contentStrings + contentstr

                    sys.stdout.write('\a')  # When this letter is sent to terminal, a beep sound is emitted but no text
                    sys.stdout.flush()
                    print(barcodeData + " checking OUT at " + str(
                        datetime.datetime.now()) + " at location: " + system_id + " for duration of " + str(time_check))
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
            else:
                print("Something happened... error")

        # show the output frame
        cv2.imshow("QR Toolbox", frame)
        key = cv2.waitKey(1) & 0xFF

        # if the `q` key was pressed, break from the loop
        if key == ord("q") or key == ord("Q"):
            break

    # close the output CSV file do a bit of cleanup
    print("[ALERT] Cleaning up... \n")
    csv.close()

    # This part is necessary to show special characters properly on any of the local CSVs
    barcodesTxt = open(args["output"], 'r', encoding="utf-8")
    newCSV = open(file_name, 'w', encoding="ANSI")

    data = barcodesTxt.read()
    newCSV.write(data)

    barcodesTxt.close()
    newCSV.close()
    os.remove(args["output"])

    if storageChoice == 'a':  # if local was chosen, also store barcodes file at the location given
        if os.path.exists(storagePath):  # check if file path exists
            csv2 = open(os.path.join(storagePath, file_name), "w",
                        encoding="ANSI")
            csv2.write(data)
            csv2.close()
        else:
            print("Alert: Storage folder not established or is unavailable. Files will only be saved to the working "
                "directory\n")

    elif storageChoice.lower() == 'b':  # if online was chosen, upload data to SharePoint as well
        upload_file(ctx, contentStrings, file_name, bkcsvfolder)

    vs.stop()
    vs.stream.release()
    cv2.destroyAllWindows()


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


def convert(data_to_convert, character_list, conversion_dict, is_for_file_name=False, is_for_trouble=False):
    old_data = data_to_convert

    for char in character_list:
        if char in data_to_convert:
            data_to_convert = data_to_convert.replace(char, conversion_dict[char]) if not \
                is_for_file_name else data_to_convert.replace(char, "-") if not is_for_trouble \
                else data_to_convert.replace(char, " ")
    if old_data != data_to_convert and is_for_file_name and is_for_trouble is not True:
        print("Error saving file with name {}, saved as {} instead.".format(old_data, data_to_convert))
    return data_to_convert


"""
This function first checks if passed data has a Special Character, then asks the user if they want to convert it.
    -If no, the user is returned to the main menu
    -If yes, the prior operation is continued and the data is converted as needed
@param label the text to check to see if it has Special Characters

@return True if it does and user answers Yes, or if no Special Character is found. False if no.
"""


def ask_special_char_conversion(label):
    for special_char in special_characters:
        if special_char in label:
            # Has special char, so ask if they want to convert or return to main menu
            while True:
                print("\nYour text has a special character(s), do you want to convert it to a regular character(s)?")
                print("A. Yes (Only for the SharePoint version)")
                print("B. No (This one will be skipped)")
                answer = input("Enter your selection: ")
                answer = answer.lower()
                if answer == 'a':
                    return True
                elif answer == 'b':
                    return False
                else:
                    print("Invalid choice \n")
    return True


"""
This function Creates a list item, used with the SharePoint site and the Office365-REST-Python-Client
@param context the context of the site that is being communicated with/uploaded to
@param content the content to add as a list item
"""


def create_list_item(context, content):
    print("Creating list item example...")
    list_object = context.web.lists.get_by_title(listTitle)
    values = content.split(",")
    sid = values[0]
    tstr = values[1]
    barstr = values[2]
    status = values[3]

    item_properties = {'__metadata': {'type': 'SP.Data.QR_x0020_TimestampsListItem'}, 'Title': barstr,
                       'QR_x0020_Terminal': sid, 'Time_x0020_Stamp': tstr, 'Info': status}
    item = list_object.add_item(item_properties)
    context.execute_query()
    print("List item '{0}' has been created.".format(item.properties["Title"]))


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
    target_file = library.root_folder.folders.get_by_url(sub_folder).files.add(info)
    file_context.execute_query()

    return target_file


""" ******* NOT IN USE (FOR NOW) *******
"""
# This function updates the contents of the given target_file with the updated_content
# @param context the context of the site that is being communicated with/uploaded to (URL, authorization, etc.)
# @param updated_content the new content to update the target file with
# @param target_file the file that is to be updated

# @return target_file a reference to the file that was updated
"""


def update_file(context, updated_content, target_file):
    list_title = "EOC Documents"
    library = context.web.lists.get_by_title(list_title)

    filecontext = library.context

    list_item = target_file.listitem_allfields # get associated list item
    list_item.set_property("Title", "TEST")
    list_item.set_property("Author", "Taha")
    list_item.set_property("Contents", updated_content)

    filecontext.execute_query()
    return target_file
"""

"""
This function creates QR codes in batches from a CSV file (defined in the global variables)
    -The function always checks and performs the QR code creation in its root folder first, and the generated codes
    are then stored in that same folder.
    -If the local choice was chosen, the codes are also stored in the location entered by the user
    -If the online/SharePoint choice was chosen, the function then also reads a CSV file (defined in global variables) 
    on the SharePoint site and generates QR Codes from that, which are stored in the same location as that CSV file
"""


def qr_batch():
    print("")
    print("The batch QR code tool is used to automatically create multiple QR codes by referencing a .csv file. "
          "The csv file must be stored in the tools origin folder, named 'names.csv', and consist of two columns "
          "'first' & 'last'. The 'first' and 'last' columns should be populated with participant's first and last "
          "names. The tool will automatically create QR codes for each participant's full name and save each QR image "
          "to the tools origin folder. \n")
    input("Press Enter to Continue \n")
    # this code creates a batch of QR codes from a csv file stored in the local directory
    # QR code image size and input filename can be modified below

    # This one creates the batch of QR codes in the same folder as this file
    with open(localQRBatchFile) as csvfile:
        reader = csv.reader(csvfile)

        for row in reader:
            labeldata = row[0] if len(row) == 1 else row[0] + " " + row[1] if row[1] != '' else row[0]

            # Check for special char, ask if user wants to convert
            if storageChoice == 'b' and not ask_special_char_conversion(labeldata):
                continue  # if user doesn't want to convert (returns False), then this text/row is skipped

            # convert special char to code character
            codeLabelData = convert(labeldata, special_characters, char_dict_special_to_code)

            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4)

            qr.add_data(codeLabelData)
            qr.make(fit=True)
            print("Creating QR code: " + labeldata)

            # draw QR image

            img = qr.make_image()
            qrFile = labeldata + ".jpg"
            qrFile = convert(qrFile, bad_file_name_list, None, True)  # remove special chars that can't be in filename
            img.save(qrFile)

            # open QR image and add qr data as name
            img = Image.open(qrFile)
            draw = ImageDraw.Draw(img)
            font = ImageFont.truetype("arial", 24)
            color = 0
            draw.text((37, 10), labeldata, font=font, fill=color)
            img.save(qrFile)
            if storageChoice == 'a':
                img.save(storagePath + "/" + qrFile)

    # For storing the new QR Codes online, if that was selected
    if storageChoice == 'b':
        resp = File.open_binary(ctx, relative_url)
        status = resp.status_code

        if status == 404:
            print(
                "The batch file '" + relative_url + "' doesn't exist. Please copy 'names.csv' to the sharepoint site.")
            return False

        with open(remoteQRBatchFile, 'wb') as output_file:
            output_file.write(resp.content)

        with open(remoteQRBatchFile) as csvfile:
            reader = csv.reader(csvfile)

            for row in reader:  # get each row from the CSV file
                labeldata = row[0] if len(row) == 1 else row[0] + " " + row[1] if row[1] != '' else row[0]
                # above: gets data from 1 row or 2 rows depending on what is in each
                if not ask_special_char_conversion(labeldata):  # Check if text has a special char, ask to convert
                    continue  # if False, skip this text (user doesn't want to convert special char)

                # convert special char to code character
                codeLabelData = convert(labeldata, special_characters, char_dict_special_to_code)

                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=10,
                    border=4)

                qr.add_data(codeLabelData)
                qr.make(fit=True)
                print("Creating QR code: " + labeldata)

                # draw QR image

                img = qr.make_image()
                qrfile = labeldata + ".jpg"
                qrfile = convert(qrfile, bad_file_name_list, None, True)  # convert chars that can't be in filename
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
                upload_file(ctx, file_content, qrfile, qrfolder)
                os.remove(qrfile)
    print("Success! \n")


"""
This function creates a single QR code based on the text inserted by the user, which is then stored in the root folder.
    - If user chose the local option, the QR code is also stored in the location entered by the user
    - If user chose the online SharePoint option, the QR code is stored on the SharePoint site
"""


def qr_single():
    print("\nEnter text to generate a single QR code and press Enter. The resulting QR image will be saved in the "
          "tool's origin folder. \n")
    custom_labeldata = input("QR Text: ")

    if storageChoice == 'b' and not ask_special_char_conversion(custom_labeldata):  # Check if text has a special char
        return  # if False, return to main menu (user doesn't want to convert special char)

    copy_labeldata = custom_labeldata
    print("Creating QR code...")

    # convert special char to code character
    copy_labeldata = convert(copy_labeldata, special_characters, char_dict_special_to_code)

    # this code creates a single QR code based on information entered into the command line.
    # The resulting QR code is stored in the current (the programs') directory
    # QR code image size and input filename can be modified below
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4)

    qr.add_data(copy_labeldata)
    qr.make(fit=True)

    # draw label

    img = qr.make_image()
    fileName = custom_labeldata + ".jpg"
    fileName = convert(fileName, bad_file_name_list, None, True)  # convert chars that can't be in a file name
    img.save(fileName)

    # Open QR image and add QR data as name

    img = Image.open(fileName)
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype("arial", 24)
    color = 0
    draw.text((37, 10), custom_labeldata, font=font, fill=color)
    img.save(fileName)

    # Store QR code locally, if that was chosen
    if storageChoice == 'a':
        img.save(storagePath + "/" + fileName)
    elif storageChoice == 'b':  # Store QR code online, if chosen
        # upload file
        with open(fileName, 'rb') as content_file:
            file_content = content_file.read()
        upload_file(ctx, file_content, fileName, qrfolder)

    print("Success! \n")


"""
This function provides more information on the purpose and development of this software
"""


def about():
    # displays the about screen
    print("\nQR Toolbox v2a \n")
    print("About: The QR Toolbox is a suite a tools for creating and reading QR codes. The toolbox is platform "
          "agnostic, lightweight, open source, and written in pure Python. This toolbox may be used to track resources,"
          " serve as a check-in capability for personnel, or customized to meet other operational needs. \n")
    print("Version: 2.0a \n")
    print("Credits: The QR Toolbox consists of a number of python packages, namely: \n qrcode - "
          "Lincoln Loop info@lincolnloop.com; \n pyzbar - Lawrence Hudson quicklizard@googlemail.com; \n OpenCV code - "
          "Adrian Rosebrock https://www.pyimagesearch.com/author/adrian/; \n Code integration, minor enhancements, & "
          "platform development - Timothy Boe boe.timothy@epa.gov \n")
    print("Contact: Timothy Boe: boe.timothy@epa.gov; or Paul Lemieux: lemieux.paul@epa.gov; USEPA Homeland Security "
          "Research Program \n")


"""
This function allows the user to select a shared folder. If user escapes, a share folder is not created
    - Note: the Tkinter code can be finicky when displayed in IDE i.e., the file window will not show when operated in
    IDE while the root.withdraw command is turned on. Commenting out the root.withdraw command will fix, but root
    window remains; destroy() can be used to remove this. May need to search for a better solution in the future
"""


def store():
    print("")
    root = Tk()
    root.title('Storage Directory')
    root.withdraw()
    store_path = filedialog.askdirectory(title='Select a Network Storage Directory')
    if os.path.exists(store_path):
        print("Storage directory established: " + store_path)
    else:
        print("Storage directory NOT established")
    print("")
    return store_path


"""
This function consolidates QR csv results into a single file. This function looks for files with QRT in the first part 
of their name. If true, all csvs within the shared folder directory that also fit this condition. A number of error
checks are built in to prevent bad things from happening
"""


def cons():
    time_header = str(datetime.datetime.now().strftime('%Y_%m_%d_%H_%M_%S'))
    cons_filename = os.path.join(storagePath, 'Consolidated_Record_' + time_header + '.csv')
    if os.path.exists(storagePath):
        QRT_files = [fn for fn in os.listdir(storagePath) if fn.startswith('QRT')]

        if not QRT_files:
            print("No entries to combine. Check the shared directory and try again")
        else:
            try:
                with open(cons_filename, 'wb') as outfile:
                    for i, fname in enumerate(QRT_files):
                        fname = os.path.join(storagePath, fname)
                        with open(fname, 'rb') as infile:
                            shutil.copyfileobj(infile, outfile)
                            print(fname + " has been imported.")
                print(
                    "\nConsolidated file created in the specified shared drive under the filename " + cons_filename + "\n")
            except:
                print("\nWARNING: Either the system was unable to write the consolidated file to the specified shared "
                      "directory or the file " + cons_filename + " is currently in use or unavailable. The consolidated"
                                                                 " record may be incomplete. \n")
    else:
        print("\nA shared folder has not been established. Specify a shared folder using the Establish Share Folder "
              "option before continuing \n")
        pass


""" THIS SECTION COMES AFTER THE LANDING SCREEN """

# Determine which camera to use
while True:
    print("Which camera do you want to use?")
    print("A. Integrated webcam")
    print("B. Separate webcam")
    print("C. PiCamera")
    cameraChoice = input("Enter your selection: ")
    cameraChoice = cameraChoice.lower()
    if cameraChoice != 'a' and cameraChoice != 'b' and cameraChoice != 'c':
        print("Invalid choice \n")
    else:
        print("\n")
        break

# Determine where to store data that is captured/recorded
while True:
    print("Do you want data stored on Sharepoint (online) or locally?")
    print("Note: Files are also saved in the QR-Toolbox root folder regardless.")
    print("A. Local (Specify a location on the computer)")
    print("B. Sharepoint (Online)")
    storageChoice = input("Enter your selection: ")
    if storageChoice.lower() == 'a':
        storagePath = store()
        break
    elif storageChoice.lower() == 'b':
        break
    else:
        print("Invalid choice \n")

# main menu

while True:
    print("\n==============|  MENU  |===============")
    print("A. QR Reader")
    print("B. QR Creator - Batch")
    print("C. QR Creator - Single")
    print("D. Consolidate Records") if storageChoice == 'a' else ""
    print("E. About/Credits" if storageChoice == 'a' else "D. About/Credits")
    print("F. Exit \n" if storageChoice == 'a' else "E. Exit \n")
    choice = input("Enter your selection: ")
    if choice.lower() == 'a':
        video()
    elif choice.lower() == 'b':
        qr_batch()
    elif choice.lower() == 'c':
        qr_single()
    elif choice.lower() == 'd':
        cons() if storageChoice == 'a' else about()
    elif choice.lower() == 'e':
        if storageChoice == 'a':
            about()
        else:
            break
    elif choice.lower() == 'f' and storageChoice == 'a':
        break
    else:
        print("Invalid choice \n")
