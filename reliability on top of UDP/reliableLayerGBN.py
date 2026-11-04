from socket import socket
import time
import select
# comment on what receiver does

# Comment on what sender does 

class reliableLayer(socket):
    def __init__(self, virtual_socket):
        self.sock = virtual_socket
        self.nextseqnum = 1
        self.expectedseq = 1
        self.base = 1
        self.N = 4
        self.start_time = 0
        self.sndpkt = {}
        self.timeoutlimit = 12

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
    
    def make_pkt(self, seq, msg, addr = None):
        pkt =  {'msg': str(seq).encode() + b':'+  msg + bytes([self.calcCrc8(str(seq).encode() + b':' + msg+ b"\x00")])}
        if addr != False:
            #If addr is set this is receivers pkt and we have to add extra data
            pkt['addr'] = addr
        return pkt
    
    def get_seq(self, msg):
        msg = msg.decode('latin1')
        seq_part,_ = msg.split(':',1)
        return int(seq_part)
    def extract(self,data):
        numlen = len(str(abs(self.expectedseq))) +1
        data = data.decode('latin1')[:-1][numlen:]
        return data
        
    def rdt_recv(self):
        data, client_address = self.sock.recvfrom(256, 0, True)
        #print(data)
        crc8 = self.calcCrc8(data)
        if crc8 == 0:
            receivedSeq = self.get_seq(data)
            if receivedSeq == self.expectedseq:  
                ackMsg= self.make_pkt(self.expectedseq,b'ACK')
                data = self.extract(data)
                self.sock.sendto(ackMsg['msg'], client_address)
                self.expectedseq += 1
                return data
            else:
                ackMsg= self.make_pkt(self.expectedseq -1,b'ACK')
                self.sock.sendto(ackMsg['msg'], client_address)
                return None
        else:
            ackMsg= self.make_pkt(self.expectedseq - 1,b'ACK')
            self.sock.sendto(ackMsg['msg'], client_address)
            return None
            
    def rdt_send(self, data, addr):
        if self.nextseqnum < self.base + self.N: 
            self.sndpkt[self.nextseqnum] = self.make_pkt(self.nextseqnum, data.encode(), addr)
            self.sock.sendto(self.sndpkt[self.nextseqnum]['msg'], self.sndpkt[self.nextseqnum]['addr'])
            if self.base == self.nextseqnum:
                self.start_time = time.time()
            self.nextseqnum += 1
        else:
            print('Queque full, please wait...')

    def timeout(self):
        self.start_time = time.time()
        basevar = self.base
        while basevar < self.nextseqnum:
            self.sock.sendto(self.sndpkt[basevar]['msg'],self.sndpkt[basevar]['addr'])
            basevar += 1
    def loopsocket(self):
        #Check for acks and timeout, update queque if received, resend if timer runs out or if receiving duplicates
        if self.start_time > 0 and time.time() - self.start_time > self.timeoutlimit:
            self.timeout()
        ready, _, _ = select.select([self.sock], [], [], 0.0)
        if ready:
            data, addr = self.sock.recvfrom(265)
            crc8 = self.calcCrc8(data)
            if crc8 == 0:
                self.base = self.get_seq(data) + 1
                print('ACK' + str(self.base - 1))
                if self.base == self.nextseqnum:
                    self.start_time = 0
                else:
                    self.start_time = time.time()
            