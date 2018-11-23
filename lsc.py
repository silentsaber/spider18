#!/usr/bin/python3
import serial
import time
import threading
import socketserver

DEBUG = False

serialHandle = serial.Serial("/dev/ttyAMA0", 9600)  #初始化串口， 波特率为115200
client_socket = []
##
##向所有客户端发送串口接收到的数据
##
def serialReceiver():
    global client_socket
    global serialHandle
    while True:
        count = serialHandle.inWaiting()  #获取缓存长度
        if count > 0:
            data = serialHandle.read(count) #读取串口缓存
            for client in client_socket:  #历遍所有客户端发送数据
                try:
                    client.sendall(data)
                except Exception as e:
                    print(e)
                    continue
        time.sleep(0.01)

class LobotServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True  #允许地址重用

class LobotServerHandler(socketserver.BaseRequestHandler):
    global client_socket
    ip = ""
    port = None

    def setup(self):
        self.ip = self.client_address[0].strip()
        self.port = self.client_address[1]
        print("connected\tIP:"+self.ip+"\tPort:"+str(self.port))
        client_socket.append(self.request) #将此连接加入客户端列表
        self.request.settimeout(6) #超时时间为6秒

    def handle(self):
        conn = self.request
        recv_data = b''
        Flag = True
        while Flag:
            try:
                buf = conn.recv(1024)
                if buf == b'':
                    Flag = False;
                else:
                    recv_data = recv_data + buf
                    #解决断包问题，接收到完整命令后才发送到串口,防止出错
                    while True:
                        try:
                            index = recv_data.index(b'\x55\x55')  #搜索数据中的0x55 0x55 
                            if len(recv_data) >= index+3:  #缓存中的数据长度是否足够
                                recv_data = recv_data[index:]
                                if recv_data[2]  + 2 <= len(recv_data):  #缓存中的数据长度是否足够
                                    cmd = recv_data[0:recv_data[2]+2]   #取出命令
                                    recv_data = recv_data[recv_data[2]+3:] #去除已经取出的命令
                                    serialHandle.write(cmd) #将命令通过串口发送
                                    if DEBUG is True:
                                        print(cmd)
                                else:
                                    break
                            else:
                                break
                        except Exception as e:  #在recv_data 中搜不到 '\x55\x55'子串
                            break;
            except Exception as e:
                print(e)
                Flag = False
                break
    def finish(self):
        client_socket.remove(self.request) #从客户端列表中剔除此连接
        print("disconnected\tIP:"+self.ip+"\tPort:"+str(self.port))


if __name__ == "__main__":
    server = LobotServer(("",9029), LobotServerHandler) #建立服务器
    threading.Thread(target=serialReceiver, daemon=True).start() #向各客户端发送串口接收到的数据
    try:
        server.serve_forever()  #开始服务器循环
    except Exception as e:
        print(e)
        serialHandle.close()
        server.shutdown()
        server.server_close()

