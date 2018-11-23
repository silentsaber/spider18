#coding=utf8
#
# 实现功能， 检测摄像头前是哪种颜色的物体，然后根据颜色作出对于动作
#
import cv2
import numpy as np
import pickle
import matplotlib.pyplot as plt
import time
import math
import urllib
import socket
import pigpio
import threading
import signal
import LSC_Client

color = 0
rR = 0
rG = 0
rB = 0
rBL = 0
rW = 0
radius = 0

stream = None
bytes = ''
Running = False

lsc = LSC_Client.LSC_Client()

#暂停信号的回调
def Stop(signum, frame):
    global Running

    print("Stop: CV颜色识别")
    if Running is True:
        Running = False

#继续信号的回调
def Continue(signum, frame):
    global stream
    global Running

    print("Continue: CV颜色识别")
    if Running is False:
        #开关一下连接
        if stream:
            stream.close()
        stream = urllib.urlopen("http://127.0.0.1:8080/?action=stream?dummy=param.mjpg")
        bytes = ''
        Running = True

#注册信号回调
signal.signal(signal.SIGTSTP, Stop)
signal.signal(signal.SIGCONT, Continue)


#数值映射
#将一个数从一个范围映射到另一个范围
def leMap(x, in_min, in_max, out_min, out_max):
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min


#找出面积最大的轮廓
#参数为要比较的轮廓的列表
def getAreaMaxContour(contours) :
        contour_area_temp = 0
        contour_area_max = 0
        area_max_contour = None;

        for c in contours : #历遍所有轮廓
            contour_area_temp = math.fabs(cv2.contourArea(c)) #计算轮廓面积
            if contour_area_temp > contour_area_max :
                contour_area_max = contour_area_temp
                if contour_area_temp > 300:  #只有在面积大于300时，最大面积的轮廓才是有效的，以过滤干扰
                    area_max_contour = c

        return area_max_contour #返回最大的轮廓

action = 9999
actionTime = 0

def runAction():
    global action
    global actionTime
    while True:
        if action != 9999:       
            lsc.RunActionGroup(action,actionTime) #发送运行动作组的指令
            lsc.WaitForFinish(20000) #等待动作组执行完毕
            action = 9999
        else:
            time.sleep(0.01)
            
#启动动作在运行线程
th2 = threading.Thread(target=runAction)
th2.setDaemon(True)
th2.start()


#设置要运行的动作组
#num为要运行的动作组， num1为要运行的次数
def setAction(num,num1 = 1):
    global action
    global actionTime

    if action == 9999:  #动作在是否是9999, 是9999就是当前没有正在运行的动作组
        action = num   #将要运行的动作组号数赋值给action
        actionTime = num1
        return action #成功，返回将要运行的动作组号
    else:
        return None  #失败返回None

#stream = urllib.urlopen("http://127.0.0.1:8080/?action=stream?dummy=param.mjpg")
while True:
    if Running:
      orgFrame = None
      try:
          bytes += stream.read(4096) #接收数据
          a = bytes.find('\xff\xd8') #找到帧头
          b = bytes.find('\xff\xd9') #找到帧尾
          if a != -1 and b != -1:
              jpg = bytes[a:b+2]  #取出图片数据
              bytes = bytes[b+2:] #去除已经取出的数据
              orgFrame = cv2.imdecode(np.fromstring(jpg, dtype=np.uint8), cv2.CV_LOAD_IMAGE_COLOR) #对图片进行解码
              orgFrame = cv2.resize(orgFrame, (320,240), interpolation = cv2.INTER_CUBIC) #将图片缩放到 320*240
    
      except Exception as e:
          print(e)
          continue
      if orgFrame is not None:  
        height,width = orgFrame.shape[:2]     
        frame = orgFrame
        frame = cv2.GaussianBlur(frame, (3,3), 0);
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV);  #将图片转换到HSV空间
    
        #分离出各个HSV通道
        h, s, v = cv2.split(frame)
        v = cv2.equalizeHist(v)
        rame = cv2.merge((h,s,v))
        #每一帧检测一种颜色，三帧结合判断是哪种颜色
        #分三帧可以降低CPU占用

        if color == 0:
            #frame = cv2.inRange(frame, (110,43,46), (124, 255, 255))#蓝
            frame = cv2.inRange(frame, (0,80,46), (6, 255, 255))#红
            #frame = cv2.inRange(frame, (35,43,46), (77, 255, 255))绿
            #frame = cv2.inRange(frame, (0,0,20), (180, 100,46))#黑
            #frame = cv2.inRange(frame, (0,0,221), (180, 30,255))#白
        elif color == 1:
            frame = cv2.inRange(frame, (35,43,46), (77, 255, 255))#绿
        else:
            frame = cv2.inRange(frame, (110,43,46), (124, 255, 255))#蓝
        '''
        elif color == 3:
            frame = cv2.inRange(frame, (0,0,20), (180, 100,46))#黑色
        else:         
            frame = cv2.inRange(frame, (0,0,221), (180, 30,255))#白色
        '''
        frame = cv2.morphologyEx(frame, cv2.MORPH_CLOSE, (4,4))

        (contours, hierarchy) = cv2.findContours(frame, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE,(0,0)) #获取所有轮廓
        areaMaxContour = getAreaMaxContour(contours) #找出面积最大的轮廓
    
        centerX = 0
        centerY = 0 
        rad = 0
        radius = 0
        if areaMaxContour is not None:
            (cen, rad), radius = cv2.minEnclosingCircle(areaMaxContour) #获取最小外接圆
            cen = (int(cen), int(rad))
            radius = int(radius)
            #cv2.circle(orgFrame, cen, radius, (0, 255, 0), 2)
        #cv2.imshow("orgFrame", orgFrame)
        #cv2.waitKey(10)
        #根据每次要检测的颜色，将检测到的颜色保存起来
        #print(radius)
        if color == 0:
            rR = radius
            color = 1
        elif color == 1:
            rG = radius
            color = 2
        else:
            rB = radius
            color = 0
        '''
        elif color == 3:
            rBL = radius
            color = 4
        else:
            rW = radius
            color = 0
        '''
        #根据颜色运行对于动作组

        if rR > rG and rR > rB and rR > rBL and rR > rW and rR >= 100: #红色最大
            setAction(51,1)
        elif rG > rR and rG > rB and rG > rBL and rG > rW and rG >= 100: #绿色最大
            setAction(50,1)
        elif rB > rR and rB > rG and rB > rBL and rB > rW and rB >= 100:  #蓝色最大
            setAction(50,1)
        else:
            pass
        '''
        elif rBL > rR and rBL > rB and rBL > rG and rBL > rW and rBL >= 100: #黑色最大
            setAction(52,1)
        elif rW > rR and rW > rG and rW > rBL and rW > rB and rW >= 100:  #白色最大
            setAction(53,1)
        '''


    else:
        bytes = ''
        time.sleep(0.1)
#cv2.destroyAllWindows()


