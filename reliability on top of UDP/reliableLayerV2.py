from socket import socket
import select

class reliableLayer(socket):
    def __init__(self, virtual_socket):
        self.sock = virtual_socket
        self.senderSeq = 0
        self.receiverSeq = 0

    def calcCrc8(self, newBytes):
        register = 0x00
        masks = [0x01, 0x02, 0x04, 0x08, 0x10, 0x20, 0x40, 0x80]
    
        for i in range(len(newBytes)):
            for j in range(7,-1,-1):
                positions = []
                registerMSB = ((register & 0x80) >> 7)
            
                position2 = (registerMSB ^ ((register & 0x02) >> 1))
                position1 = (registerMSB ^ ((register & 0x01)))
                position0 = (registerMSB ^ ((newBytes[i] & masks[j]) >> j))
                positions.append(position0)
                positions.append(position1)
                positions.append(position2)
            
                register = (register << 1) & 0xFF
            
                for bit in range(3):
                    register = (register & ~masks[bit]) | (positions[bit] << bit)
        return register
    
    def make_pkt(self, msg, seq = None):
        if seq != None:
            seq = str(seq)
            return seq.encode() +  msg + bytes([self.calcCrc8(seq.encode() + msg+ b"\x00")])
        else:
            return msg + bytes([self.calcCrc8(msg+ b"\x00")])
        
    
    def get_seq(self, msg):
        return int(msg[:1])
        
        
    def updateSeq(self, seq):
        if seq == 0:
            return 1
        else:
            return 0
    
    def extract(self,data):
        data = data.decode('latin1')[:-1][1:]
        return data
    def isAck(self,data):
        seq = self.get_seq(data)
        data = data.decode('latin1')[:-1]
        print(data)
        print(str(self.senderSeq)+'ACK')
        return data == str(self.senderSeq)+'ACK'
        
    def rdt_recv(self):
        data, client_address = self.sock.recvfrom(256)
        crc8 = self.calcCrc8(data)
        if crc8 == 0:
            receivedSeq = self.get_seq(data)
            if receivedSeq == self.receiverSeq:
                data = self.extract(data)
                ackMsg= self.make_pkt(b'ACK', receivedSeq)
                self.receiverSeq = self.updateSeq(self.receiverSeq)
                self.sock.sendto(ackMsg, client_address)
                return data
            else:
                lastrecvdSeq = self.updateSeq(self.receiverSeq)
                ackMsg = self.make_pkt(b'ACK', lastrecvdSeq)
                self.sock.sendto(ackMsg, client_address)
                return None
        else:
            lastrecvdSeq = self.updateSeq(self.receiverSeq)
            ackMsg = self.make_pkt(b'ACK', lastrecvdSeq)
            self.sock.sendto(ackMsg, client_address)
            return None
            
    def rdt_send(self, data, destination_address):
        sndpkt = self.make_pkt(data.encode(), self.senderSeq)
        self.sock.sendto(sndpkt, destination_address)
        ack = False
        while ack == False:
            ready, _, _ = select.select([self.sock], [], [], 0.0)
            if ready:
                data,destination_address = self.sock.recvfrom(256)
                crc8 = self.calcCrc8(data)
                if crc8 == 0:
                    ack = self.isAck(data)
                    if ack:
                        self.senderSeq = self.updateSeq(self.senderSeq)
                    else:
                        self.sock.sendto(sndpkt, destination_address)
                else:
                    self.sock.sendto(sndpkt, destination_address)
                
            