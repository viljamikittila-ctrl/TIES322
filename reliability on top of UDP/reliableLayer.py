from socket import socket
import time
import select

class reliableLayer(socket):
    def __init__(self, virtual_socket):
        self.sock = virtual_socket
        self.senderseq = 0
        self.start_time = 0
        self.sndpkt ={}
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
    
    def make_pkt(self, seq, data, addr = None):
            pkt =  {'msg': str(seq).encode() +  data + bytes([self.calcCrc8(str(seq).encode() + data+ b"\x00")])}
            if addr != None:
                pkt['addr'] = addr
            return pkt
    
    def get_seq(self, msg):
        msg = msg.decode('latin1')
        return int(msg[:1])
        
    def updateSeq(self, seq):
        if seq == 0:
            return 1
        else:
            return 0
    
    def timeout(self):
        print('resending')
        self.sock.sendto(self.sndpkt['msg'], self.sndpkt['addr'])
        self.start_time = time.time()
        
    def extract(self,data):
        data = data.decode('latin1')[:-1][1:]
        return data
    def check_seq(self, msg):
        oldSeq = self.get_seq(msg)
        return oldSeq == self.senderseq
        
    def rdt_recv(self):
        data, client_address = self.sock.recvfrom(256, 0, True)
        if data == None:
            return None
        print(data)
        crc8 = self.calcCrc8(data)
        if crc8 == 0:
            receivedSeq = self.get_seq(data)
            if self.receiverSeq == receivedSeq:
                ackMsg= self.make_pkt(self.receiverSeq, b'ACK')
                self.sock.sendto(ackMsg['msg'], client_address)
                self.receiverSeq = self.updateSeq(self.receiverSeq)
                data = self.extract(data)
                return data
            else:
                ackMsg= self.make_pkt(self.receiverSeq, b'ACK')
                self.sock.sendto(ackMsg['msg'], client_address)
        else:
            ackMsg = self.make_pkt(self.receiverSeq, b'ACK')
            self.sock.sendto(ackMsg['msg'], client_address)
            return None
            
    def rdt_send(self, message, addr):
        self.sndpkt = self.make_pkt(self.senderseq, message.encode(), addr)
        timeout = 0.7
        self.start_time = time.time()
        self.sock.sendto(self.sndpkt['msg'], self.sndpkt['addr'])
        ackrcvd = False
        while ackrcvd == False:
            if self.start_time > 0 and time.time() - self.start_time > timeout:
                self.timeout()
            ready, _, _ = select.select([self.sock], [], [], 0.0)
            if ready:
                data, addr = self.sock.recvfrom(265)
                if data != None:
                    crc8 = self.calcCrc8(data)
                    if crc8 == 0:
                        ackrcvd = True
                        print('ACK' + str(self.senderseq))
                        self.senderseq = self.updateSeq(self.senderseq)
                        self.start_time = 0
            