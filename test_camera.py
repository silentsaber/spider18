#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Dec  5 12:32:27 2018

@author: zhangnaifu
"""

from picamera.array import PiRGBArray
from picamera import PiCamera
import time
import cv2

camera = PiCamera()
rawCapture = PiRGBArray(camera)

time.sleep(0.1)

camera.capture(rawCapture, format="bgr")
image = rawCapture.array

cv2.imshow("Image", image)
cv2.waitKey(0)
