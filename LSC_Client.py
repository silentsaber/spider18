#coding:utf-8
import socket
import threading
import time

class LSC_Client(object):

    ip_port = ('127.0.0.1', 9029)
    sock = None
    th1 = None
    Stop = False

    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect(self.ip_port)
        self.th1 = threading.Thread(target=LSC_Client.Heartbeat, args=(self,))
        self.th1.setDaemon(True)
        self.th1.start()

    def __del__(self):
        self.Stop = True
        self.th1.join()
        self.sock.shutdown(socket.SHUT_RDWR)
        self.sock.close()

    def MoveServo(self, servoId, pos, time):
        buf = bytearray(b'\x55\x55\x08\x03\x01')
        buf.extend([(0xff & time), (0xff & (time >> 8))])
        buf.append((0xff & servoId))
        buf.extend([(0xff & pos), (0xff & (pos >> 8))])
        self.sock.sendall(buf)

    def RunActionGroup(self,actNum, num):
        buf = bytearray(b'\x55\x55\x05\x06')
        buf.append(0xff & actNum)
        buf.extend([(0xff & num), (0xff & (num >> 8))])
        self.sock.sendall(buf)

    def StopActionGroup(self):
        self.sock.sendall(b'\x55\x55\x02\x07')

    def Heartbeat(self):
        count = 0
        while True:
            if self.Stop is True:
                break
            time.sleep(0.1)
            count += 1
            if count >= 30:
                count = 0
                try:
                    self.sock.sendall('3')
                except:
                    continue

    def flush(self):
        self.sock.settimeout(0.0000001)
        while True:
            try:
                self.sock.recv(8192)
            except:
                break

    def WaitForFinish(self, timeout):
        self.flush()

        buf = bytearray()
        timeout = time.time() + (float(timeout) / 1000)
        self.sock.settimeout(0.005)
        while True:
            if time.time() > timeout:
                return False
            try:
                rcv  = self.sock.recv(128)
                if rcv is not None:
                    buf += rcv
                    while True:
                        try:
                            index = buf.index(b'\x55\x55')
                            if len(buf) >= index + 3:
                                buf = buf[index:]  #将帧头前面不符合的部分剔除
                                if (buf[2] + 2) <= len(buf): #缓存中的数据数据是否完整
                                    cmd = buf[0: (buf[2]+2)] #将命令取出 print("OK")
                                    buf = buf[buf[2]+3:]
                                    if cmd[3] == 0x08 or cmd[3] == 0x07:
                                        return True
                        except:
                            break
            except socket.timeout:
                continue
            except:
                return False


