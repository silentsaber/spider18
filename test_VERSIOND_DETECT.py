#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Dec  4 12:32:27 2018

@author: zhangnaifu
"""

# import the necessary packages
from imutils.video import VideoStream
from pyzbar import pyzbar
import argparse
import datetime
import imutils
import time
import math
import cv2

# construct the argument parser and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-o", "--output", type=str, default="barcodes.csv",
                help="path to output CSV file containing barcodes")
args = vars(ap.parse_args())


####################找出最大的轮廓
def getAreaMaxContour(contours) :
        contour_area_temp = 0
        contour_area_max = 0
        area_max_contour = None;

        for c in contours : #历便所有轮廓
            contour_area_temp = math.fabs(cv2.contourArea(c)) #计算面积
            if contour_area_temp > contour_area_max :
                contour_area_max = contour_area_temp
                if contour_area_temp > 50:  #限制最小面积
                    area_max_contour = c
                    MaxArea=contour_area_max

        return area_max_contour  #返回最大面积

###############################
global cX
global cY
global MaxArea
def detect():
    MaxArea=0
    # initialize the video stream and allow the camera sensor to warm up
    print("[INFO] starting video stream...")
    vs = VideoStream(src=0).start()
    #    vs = VideoStream(usePiCamera=True).start()
    time.sleep(2.0)

    # open the output CSV file for writing and initialize the set of
    # barcodes found thus far
    csv = open(args["output"], "w")
    found = set()
    ###
    count = 0
    runTime = 500
    ###
    while count <= runTime:

    # loop over the frames from the video stream
    # while True:
        # grab the frame from the threaded video stream and resize it to
        # have a maximum width of 400 pixels
        frame = vs.read()
        frame = imutils.resize(frame, width=400)

        ########################################  find the center of white area
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
#        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        ret, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
        (contours, hierarchy) = cv2.findContours(binary, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        maxcounter = getAreaMaxContour(contours)  # 最大轮廓
        
        if maxcounter != None:
#            print(MaxArea)
            M = cv2.moments(maxcounter)
            cX = int(M["m10"] / M["m00"])
            cY = int(M["m01"] / M["m00"])
            print(cX)
            print("!")
            print(cY)
        ########################################

        # find the barcodes in the frame and decode each of the barcodes
        barcodes = pyzbar.decode(frame)

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

            # draw the barcode data and barcode type on the image
            text = "{} ({})".format(barcodeData, barcodeType)
            cv2.putText(frame, text, (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

            # if the barcode text is currently not in our CSV file, write
            # the timestamp + barcode to disk and update the set
            if barcodeData not in found:
                csv.write("{},{}\n".format(datetime.datetime.now(),
                                           barcodeData))
                csv.flush()
                found.add(barcodeData)



        # show the output frame
        cv2.imshow("Barcode Scanner", gray)
        key = cv2.waitKey(1) & 0xFF
###
        count += 1

        # save every 16th frame
        if count % 16 == 0:
             cv2.imwrite("capture{0}.jpg".format(count), binary)
###
        # if the `q` key was pressed, break from the loop
        if key == ord("q"):
            break

    # close the output CSV file do a bit of cleanup
    print("[INFO] cleaning up...")
    csv.close()
    cv2.destroyAllWindows()
    vs.stop()
detect()