#!/usr/bin/python2
#coding=utf-8

import cv2
from pyzbar import pyzbar
import zbar
import numpy as np
import pickle
import matplotlib.pyplot as plt
import time
import math
import urllib
import socket
import signal
import threading
##import LSC_Client
import PIL
import Image
from LSC_Client import LSC_Client

ip_port_sonar = ('127.0.0.1', 9030)
sock_sonar = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock_sonar.connect(ip_port_sonar)  #连接到超声波距离服务器以获取距离

distance = 0.0
step = 0
Running = True

lsc = LSC_Client()


##lscx = LSC_Client.LSC_Client()  #摄像头


stream = urllib.urlopen("http://127.0.0.1:8080/?action=stream?dummy=param.mjpg")
bytes = ''

# 数值映射
def leMap(x, in_min, in_max, out_min, out_max):
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min



##从服务器接收超声波距离的数据
def updateDistance():
    global sock_sonar
    global distance

    while True:
        rcv = sock_sonar.recv(1024)
        if rcv == b'':
            distance = 0.0
            break;
        else:
            if Running is True:
                st =  rcv.strip() #去除空格
                try:
                    distance = float(st)  #将字符串转为浮点数
                except Exception as e:
                    print(e)
                    distance = 0.0

#启动距离更新线程
th1 = threading.Thread(target=updateDistance)
th1.setDaemon(True)
th1.start()




#心跳，
def Heartbeat():
    while True:
        time.sleep(3)
        try:
            sock_sonar.sendall("3")
        except:
            continue

#启动心跳线程
th2 = threading.Thread(target=Heartbeat)
th2.setDaemon(True)
th2.start()


lsc.RunActionGroup(0,1)
pitch = 1500
yaw = 1500
lsc.MoveServo(19, 1800,1000)  #让摄像头云台的两个舵机都转动到中间位置
lsc.MoveServo(20, 1500,1000)
  

##while True:
##  if Running is True:
##    try:
##        ###### camera code
##        orgFrame = None
##        try:
##            bytes += stream.read(4096)  # 接收数据v
##            a = bytes.find('\xff\xd8')  # 找到帧头
##            b = bytes.find('\xff\xd9')  # 找到帧尾
##            if a != -1 and b != -1:
##                jpg = bytes[a:b + 2]  # 取出数据
##                bytes = bytes[b + 2:]
##
##                # 解码图片
##                orgFrame = cv2.imdecode(np.fromstring(jpg, dtype=np.uint8), cv2.CV_LOAD_IMAGE_COLOR)
##                # 将图片缩放到320*240
##                orgFrame = cv2.resize(orgFrame, (320, 240), interpolation=cv2.INTER_CUBIC)
##        except Exception as e:
##            print(e)
##            continue
##
##        if orgFrame is not None:
##
##            frame = orgFrame
##            pil = Image.fromarray(frame.astype('uint8')).convert('RGB')  # 转numpy->PIL
##            width, height = pil.size
##            barcodes = pyzbar.decode(pil)
##            for barcode in barcodes:
##                barcodeData = barcode.data.decode('utf-8')
##                barcodeType = barcode.type
##                print("[info] Found {} barcode: {}".format(barcodeType, barcodeData))
##        ###### camera code
##                
##        if step == 0:
##            lsc.RunActionGroup(1,0)  #动作组1, 低姿态前进
##            step = 1 #转到步骤1
##        elif step == 1:
##            if distance > 0 and distance <= 50:  # 超声波距离小于50CM
##                lsc.StopActionGroup() #停止正在执行的动作组
##                step = 2 #转到步骤2
##        elif step == 2:
##            lsc.RunActionGroup(4,11)  #运行4号动作在，低姿态右转动作执行16次
##            lsc.WaitForFinish(20000)  #等待执行完毕
##            step = 3 #转到步骤3
##        elif step == 3:
##            step = 0 #回到步骤0
##        else:
##            pass
##        time.sleep(0.1)
##    except Exception as e:
##        print(e)
##        break
##  else: #Running 是False, 程序被暂停，什么都不做
##      time.sleep(0.1)



time_start = time.time()

while True:
  if Running is True:
    time_elapsed = time.time() - time_start
    if time_elapsed > 500:
        print(time_elapsed)
        Running = False
        break
    else:
        try:
            ###### camera code
            orgFrame = None
            try:
                bytes += stream.read(4096)  # 接收数据v
                a = bytes.find('\xff\xd8')  # 找到帧头
                b = bytes.find('\xff\xd9')  # 找到帧尾
                if a != -1 and b != -1:
                    jpg = bytes[a:b + 2]  # 取出数据
                    bytes = bytes[b + 2:]

                    # 解码图片
                    orgFrame = cv2.imdecode(np.fromstring(jpg, dtype=np.uint8), cv2.CV_LOAD_IMAGE_COLOR)
                    # 将图片缩放到320*240
                    orgFrame = cv2.resize(orgFrame, (320, 240), interpolation=cv2.INTER_CUBIC)
            except Exception as e:
                print(e)
                continue

            if orgFrame is not None:

                frame = orgFrame
                pil = Image.fromarray(frame.astype('uint8')).convert('RGB')  # 转numpy->PIL
                width, height = pil.size
                barcodes = pyzbar.decode(pil)
                for barcode in barcodes:
                    barcodeData = barcode.data.decode('utf-8')
                    barcodeType = barcode.type
##                    print("[info] Found {} barcode: {}".format(barcodeType, barcodeData))
                    print(barcodeData)

###### camera code
            if step == 0:
                lsc.RunActionGroup(9,0)  #动作组1, 低姿态前进
                step = 1 #转到步骤1
##            if step == 6:
##                lsc.StopActionGroup() 
##                lsc.MoveServo(19, 2500,1000)
##                lsc.WaitForFinish(20000)
##                lsc.MoveServo(19, 500,1000)
##                lsc.WaitForFinish(20000)
##                lsc.MoveServo(19, 1500,1000)
##                lsc.WaitForFinish(20000)time.sleep(0.1)
##                step = 1
                
                #back or not?
            elif step == 1:
                if distance > 20 and distance <= 50:  # 超声波距离小于30CM
                    lsc.StopActionGroup() #停止正在执行的动作组
                    step = 2 #转到步骤2
                elif distance <= 20 and distance > 0:#back and stay step1
                    lsc.StopActionGroup() #停止正在执行的动作组
                    time.sleep(0.1)
                    lsc.RunActionGroup(2,1)  #小于15就后退，去远离目标
                    lsc.WaitForFinish(3000)  #等待执行完毕
                    step = 1 #转到步骤1
            elif step == 2:
                lsc.RunActionGroup(4,11)  #运行4号动作在，低姿态右转动作执行16次
                lsc.WaitForFinish(20000)  #等待执行完毕
                step = 3 #转到步骤3
            elif step == 3: 
                step = 0 #回到步骤0
            else:
                pass
            time.sleep(0.1)
        except Exception as e:
            print(e)
            break
  else: #Running 是False, 程序被暂停，什么都不做
      time.sleep(0.1)
