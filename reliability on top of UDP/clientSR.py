import time
import socket
import msvcrt
from virtualSocketSR import virtualSocket
from reliableLayerSR import reliableLayer


sock = virtualSocket(socket.AF_INET, socket.SOCK_DGRAM)
server_addr = ('localhost', 8080)

reliableLayer = reliableLayer(sock)
current_buffer = ""

print('Write your message: ')

while True:
    reliableLayer.loopsocket()
    if msvcrt.kbhit():
        char = msvcrt.getwch()
        if char == "\r" or char == "\n":
            if current_buffer.strip() != "":
                print(f"\nSending: {current_buffer}")
                reliableLayer.rdt_send(current_buffer, server_addr)
            current_buffer = ""
            print("Write your message: ")
        else: 
            current_buffer += char
    time.sleep(0.01)
        