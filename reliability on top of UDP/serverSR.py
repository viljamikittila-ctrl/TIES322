import socket
from virtualSocketSR import virtualSocket
from reliableLayerSR import reliableLayer


UDP_IP = "localhost"
UDP_PORT = 8080

sock = virtualSocket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))

reliableLayer = reliableLayer(sock)

data = ''
            
        

while True:
    try:
        data = reliableLayer.rdt_recv()
        if data != None:
            for msg in data:
                print (msg)
    except socket.error as e:
        print('socket error!')
        break