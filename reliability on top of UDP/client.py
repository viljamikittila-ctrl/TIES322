import socket
from virtualSocket import virtualSocket
from reliableLayerV3 import reliableLayer


sock = virtualSocket(socket.AF_INET, socket.SOCK_DGRAM)
server_addr = ('localhost', 8080)

reliableLayer = reliableLayer(sock)

while True:
    message = input("Write your message: ")
    if message != '':
        print('Sending...')
        reliableLayer.rdt_send(message, server_addr)
        