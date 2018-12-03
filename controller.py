#!/usr/bin/python3
#coding:utf8
#
# ##实现功能: 实现一个服务器来提供切换各个玩法的功能
#
import subprocess
import time
import threading
import socketserver
import re
import signal

lastMode = 0

ChildSonarLed = subprocess.Popen(["python2", "/home/pi/spider/sonar_led.py"])  #根据距离控制LED 
ChildSonar = subprocess.Popen(["python2", "/home/pi/spider/spider_bz.py"])    #超声波避障碍
ChildCvColor = subprocess.Popen(["python2", "/home/pi/spider/cv_color_stream.py"]) #颜色识别
ChildCvTrack = subprocess.Popen(["python2", "/home/pi/spider/cv_track_stream.py"]) #摄像头跟踪

ChildCvDistance = subprocess.Popen(["python2", "/home/pi/spider/cv_distance_stream.py"]) #摄像头距离检测
ChildCvFind = subprocess.Popen(["python2", "/home/pi/spider/cv_find_stream.py"])  #六足跟踪


#
#暂停未被启用的功能
#
def modeReset():  
    if lastMode != 1:
        ChildSonarLed.send_signal(signal.SIGTSTP)  #向 控制LED的子进程发出暂停信号
    if lastMode != 2:
        ChildSonar.send_signal(signal.SIGTSTP)  #向超声波避障 子进程发出暂停信号
    if lastMode != 3:
        ChildCvColor.send_signal(signal.SIGTSTP)
    if lastMode != 4:
        ChildCvTrack.send_signal(signal.SIGTSTP) 
    if lastMode != 5:
        ChildCvDistance.send_signal(signal.SIGTSTP) 
    if lastMode != 6:
        ChildCvFind.send_signal(signal.SIGTSTP) 

class LobotServer(socketserver.TCPServer):
    allow_reuse_address = True  #地址重用

class LobotServerHandler(socketserver.BaseRequestHandler):
    ip = ""
    port = None
    buf = ""

    def setup(self):
        self.ip = self.client_address[0].strip()  #获取客户端的ip
        self.port = self.client_address[1] #获取客户端的端口
        print("connected\tIP:" + self.ip + "\tPort:" + str(self.port))
        self.request.settimeout(20)  #连接超时设为20秒

    def handle(self):
        global lastMode
        Flag = True
        while Flag:
            try:
                recv = self.request.recv(128)  #接收数据v
                if recv == b'':
                    Flag = False  #空则推出
                else:
                    self.buf += recv.decode()  #解码
                    #print(self.buf)
                    self.buf = re.sub(r'333333','',self.buf, 10)  #约定客户端通过发送'3'来进行心跳， 删除字符串中的3
                    s = re.search(r'mode=\d{1,2}', self.buf, re.I) #查找字符串中的 MODE=数字  格式的字串
                    if s:
                        self.buf=""   #只要找到一个就将所有的缓存清除
                        Mode = int(s.group()[5:])  #从字串中获取mode的数值
                        print(Mode)


                        #根据Mode的数值 向 对于的子进程发送继续运行信号，对应的子进程运行，产生效果
                        if Mode == 0:
                            if lastMode != Mode: #只有在最后的一次和当前的模式不一样才要转换
                                lastMode = Mode   
                                modeReset()
                            self.request.sendall("OK".encode())   #向客户端发送“OK"
                        elif Mode == 1:
                            if lastMode != Mode:
                                lastMode = Mode
                                modeReset()
                                ChildSonarLed.send_signal(signal.SIGCONT)
                            self.request.sendall("OK".encode())
                        elif Mode == 2:
                            if lastMode != Mode:
                                lastMode = Mode
                                modeReset()
                                ChildSonar.send_signal(signal.SIGCONT)
                            self.request.sendall("OK".encode())
                        elif Mode == 3:
                            if lastMode != Mode:
                                lastMode = Mode
                                modeReset()
                                ChildCvColor.send_signal(signal.SIGCONT)
                            self.request.sendall("OK".encode())
                        elif Mode == 4:
                            if lastMode != Mode:
                                lastMode = Mode
                                modeReset()
                                ChildCvTrack.send_signal(signal.SIGCONT)
                            self.request.sendall("OK".encode())
                        elif Mode == 5:
                            if lastMode != Mode:
                                lastMode = Mode
                                modeReset()
                                ChildCvDistance.send_signal(signal.SIGCONT)
                            self.request.sendall("OK".encode())
                        elif Mode == 6:
                            if lastMode != Mode:
                                lastMode = Mode
                                modeReset()
                                ChildCvFind.send_signal(signal.SIGCONT)
                            self.request.sendall("OK".encode())
                        else:
                            lastMode = 0
                            modeReset()
                            self.request.sendall("Failed".encode())
                            pass
            except Exception as e:
                print(e)
                Flag = False

    def finish(self):
        lastMode = 0
        modeReset()
        print("disconnected\tIP:" + self.ip + "\tPort:" + str(self.port))


server = LobotServer(("",9040), LobotServerHandler)  
server.serve_forever()#启动服务器

