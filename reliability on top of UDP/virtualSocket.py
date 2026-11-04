from socket import socket
import random
import time

class virtualSocket(socket):
    
    pDrop = 0
    pDelay = 0
    pError = 0.2
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
    def recvfrom(self,bufsize, flags=0, receiver = False):
        received = False
        while received == False:
            packet, sender_address = super().recvfrom(bufsize, flags)
            if random.random() <= self.pDrop:
                print("Dropped packet")
                return [None, None]
            elif random.random() <= self.pDelay:
                print("Added delay")
                time.sleep(1)
                received = True
                return [packet, sender_address]
            elif random.random() <= self.pError:
                print("Bit changed")
                packetBytes=bytearray(packet)
                byteIndex = random.randint(0,len(packetBytes)) -1
                bitIndex = random.randint(0,7)
                byte = packetBytes[byteIndex]
                bit = (byte >> bitIndex) & 1
                opposite = bit ^1
                packetBytes[byteIndex] = (byte & ~(1 << bitIndex)) | (opposite << bitIndex)
                
                received = True
                changedPacket = bytes(packetBytes)
                return [changedPacket, sender_address]
            else:
                received = True
                return [packet, sender_address]

        
        