#!/usr/bin/python2
#coding=utf8
import pickle
import time
import urllib
import socket
import threading
import signal
from LSC_Client import LSC_Client

ip_port_sonar = ('127.0.0.1', 9030)
sock_sonar = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock_sonar.connect(ip_port_sonar)  #连接到超声波距离服务器以获取距离

distance = 0.0
step = 0
Running = False
centerX = 0
centerY = 0
xc = False

lsc = LSC_Client()

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


#暂停信号的回调
def Stop(signum, frame):
    global Running
    global step

    print("Stop: 超声波避障")
    if Running is True:
        Running = False
        lsc.StopActionGroup()  #暂停时要将正在运行的动作组停下来
        step = 0
        centerX = 0
        count = 0
        rads = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        lastR = 0
        xc = False

#继续信号的回调
def Continue(signum, frame):
    global Running
    global step
    global stream
    print("Continue: 超声波避障")
    if Running is False:
        step = 0
        if stream:
            stream.close()
        stream = urllib.urlopen("http://127.0.0.1:8080/?action=stream?dummy=param.mjpg")
        bytes = ''
        Running = True

#注册信号回调
signal.signal(signal.SIGTSTP, Stop)
signal.signal(signal.SIGCONT, Continue)

#数值映射
def leMap(x, in_min, in_max, out_min, out_max):
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

#找出最大的轮廓
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

        return area_max_contour  #返回最大面积


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
lsc.MoveServo(6, 1500,1000)  #先让摄像头云台舵机转到对于中间位置
lsc.MoveServo(7, 1500,1000)
while True:
  if Running is True:
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
    if orgFrame is not None:
        height,width = orgFrame.shape[:2]
        frame = orgFrame
        frame = cv2.GaussianBlur(frame, (5,5), 0); #高斯模糊
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV); #将图片转换到HSV空间

        #分离出各个HSV通道
        h, s, v = cv2.split(frame)
        v = cv2.equalizeHist(v)
        frame = cv2.merge((h,s,v))

        frame = cv2.inRange(frame, (0,0,221), (180,30,255))  #根据目标的颜色对图片进行二值化
        frame = cv2.morphologyEx(frame, cv2.MORPH_CLOSE, (4,4)) #闭操作
        (contours, hierarchy) = cv2.findContours(frame, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE,(0,0)) #找到所有的轮廓
        areaMaxContour = getAreaMaxContour(contours)  #找到其中最大的轮廓
    try:

        if step == 0:
            lsc.RunActionGroup(1,0)  #动作组1, 低姿态前进
            step = 1 #转到步骤1
        elif step == 1:
            if distance > 0 and distance <= 30:  # 超声波距离小于30CM
                lsc.StopActionGroup() #停止正在执行的动作组
                step = 2 #转到步骤2
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


