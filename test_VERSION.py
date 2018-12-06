#!/usr/bin/python2
# coding=utf-8

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

from test_VERSIOND_DETECT import cX
from test_VERSIOND_DETECT import cY
from test_VERSIOND_DETECT import MaxArea
import simple_barcode_detection
import test_VERSIOND_DETECT as detect_qr

ip_port_sonar = ('127.0.0.1', 9030)
sock_sonar = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock_sonar.connect(ip_port_sonar)  # 连接到超声波距离服务器以获取距离

ip_port_sonarx = ('127.0.0.1', 9090)
sock_sonarx = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock_sonarx.connect(ip_port_sonarx)  # 连接到超声波距离服务器以获取距离

distance = 0.0
step = -1
Running = True

lsc = LSC_Client()


##lscx = LSC_Client.LSC_Client()  #摄像头

### create a reader
##scanner = zbar.ImageScanner()
##
### configure the reader
##scanner.parse_config('enable')
##font=cv2.FONT_HERSHEY_SIMPLEX
##camera = cv2.VideoCapture("http://127.0.0.1:8080/?action=stream?dummy=param.mjpg")
##camera = urllib.urlopen("http://127.0.0.1:8080/?action=stream?dummy=param.mjpg")
##bytes = ''
##pic = 0
##start_time1 = 0
##start_time2 = 0

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
                st = rcv.strip()  # 去除空格
                try:
                    distance = float(st)  # 将字符串转为浮点数
                except Exception as e:
                    print(e)
                    distance = 0.0


# 启动距离更新线程
th1 = threading.Thread(target=updateDistance)
th1.setDaemon(True)
th1.start()



#################从服务器接收超声波距离的数据
def updateDistancex():
    global sock_sonar
    global DISTANCE

    while True:
        rcv = sock_sonarx.recv(1024)
        if rcv == b'':
            DISTANCE = 0.0
            break;
        else:
            if Running is True:
                st = rcv.strip()  # 去除空格
                try:
                    DISTANCE = float(st)  # 将字符串转为浮点数
                except Exception as e:
                    print(e)
                    DISTANCE = 0.0


# 启动距离更新线程
th10 = threading.Thread(target=updateDistancex)
th10.setDaemon(True)
th10.start()
##################################


# 心跳，
def Heartbeat():
    while True:
        time.sleep(3)
        try:
            sock_sonar.sendall("3")
        except:
            continue


# 启动心跳线程
th2 = threading.Thread(target=Heartbeat)
th2.setDaemon(True)
th2.start()


def runDetect():
    detect_qr.detect()


th3 = threading.Thread(target=runDetect)
th3.setDaemon(True)
th3.start()

##time_start = time.time()

lsc.RunActionGroup(0, 1)
pitch = 1500
yaw = 1500
lsc.MoveServo(19, 2500, 1000)  # 让摄像头云台的两个舵机都转动到中间位置
lsc.MoveServo(20, 1500, 1000)

while True:
    if Running is True:
        ##    time_elapsed = time.time() - time_start
        ##    if time_elapsed > 500:
        ##        print(time_elapsed)
        ##        Running = False
        ##        break
        ##    else:
        try:

            ####################先前动作，定位
            if step == -1:
                #寻找
                if MaxArea > 5000:
                    ##面积适中，找到白色区域
                    #调整蜘蛛六足
                    while True:
                        lsc.RunActionGroup(4, 1)  #执行一次右转，然后继续判定MaxArea是否超过50，否的话停止
                        lsc.WaitForFinish(3000)  # 等待执行完毕
                        if MaxArea<=5000:
                            break
                        time.sleep(0.1)
                    step=0
                else :
                    lsc.RunActionGroup(4, 2)  # 运行4号动作在，低姿态右转动作执行16次
                    lsc.WaitForFinish(5000)  # 等待执行完毕
                    step=-1
            #######################

            if step == 0:
                lsc.RunActionGroup(1, 0)  # 动作组1, 低姿态前进
                step = 1  # 转到步骤1

            # back or not?
            elif step == 1:
                if distance > 15 and distance <= 40:  # 超声波距离小于30CM
                    lsc.StopActionGroup()  # 停止正在执行的动作组
                    step = 2  # 转到步骤2
                elif distance <= 15 and distance > 0:  # back and stay step1
                    lsc.StopActionGroup()  # 停止正在执行的动作组
                    time.sleep(0.1)
                    lsc.RunActionGroup(2, 1)  # 小于15就后退，去远离目标
                    lsc.WaitForFinish(3000)  # 等待执行完毕
                    step = 1  # 转到步骤1
            elif step == 2:
                lsc.RunActionGroup(4, 11)  # 运行4号动作在，低姿态右转动作执行16次
                lsc.WaitForFinish(20000)  # 等待执行完毕
                step = 3  # 转到步骤3
            elif step == 3:
                step = 0  # 回到步骤0
            else:
                pass
            time.sleep(0.1)
        except Exception as e:
            print(e)
            break
    else:  # Running 是False, 程序被暂停，什么都不做
        time.sleep(0.1)

