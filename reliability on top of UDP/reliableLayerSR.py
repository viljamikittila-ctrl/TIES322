from socket import socket
import time
import select
# comment on what receiver does

# Comment on what sender does 

class reliableLayer(socket):
    def __init__(self, virtual_socket):
        self.sock = virtual_socket
        self.base = 1
        self.nextseqnum = 1
        self.expectedseq = 1
        self.senderN = 4
        self.receiverN = 4
        self.start_times = {}
        self.sndpkt = {}
        self.buffered = {}
        self.timeoutlimit = 12
        self.MAX_SEQ_S = 8
        self.MAX_SEQ_R = 8
        self.datatodeliver = []

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
    
    def make_pkt(self, seq, msg, addr= False):
        pkt =  {'msg': str(seq).encode() +  msg + bytes([self.calcCrc8(str(seq).encode() + msg+ b"\x00")])}
        if addr != False:
            #If addr is set this is receivers pkt and we have to add extra data
            pkt['addr'] = addr
            pkt['ackd'] = False
        return pkt
    
    def start_timer(self, seq):
        self.start_times[seq] = time.time()
    
    def stop_timer(self, seq):
        del self.start_times[seq]
        
    def markackd(self, seq):
        self.sndpkt[seq]['ackd'] = True
        
    
    def timeout(self, timeoutseqnum):
       self.start_timer(timeoutseqnum)
       self.sock.sendto(self.sndpkt[timeoutseqnum]['msg'], self.sndpkt[timeoutseqnum]['addr'])
       
    def buffer(self, seq, data):
       self.buffered[seq] = data
    
    def getbuffered(self, seq):
        return self.buffered[seq]
    
    def getseq(self, msg, receiver = False):
        seq_part = msg[:1]
        return int(seq_part)
    
    def extract(self,data):
        data = data.decode('latin1')[:-1][1:]
        return data
        
    def rdt_recv(self):
        rcvpkt, client_address = self.sock.recvfrom(256, 0, True)
        crc8 = self.calcCrc8(rcvpkt)
        if crc8 == 0:
            seq = self.getseq(rcvpkt)
            if (seq - self.expectedseq) % self.MAX_SEQ_R < self.receiverN:
                data = self.extract(rcvpkt)
                self.buffer(seq, data)
                sndpkt = self.make_pkt(seq, b'ACK')
                self.sock.sendto(sndpkt['msg'], client_address)
            elif (self.expectedseq - seq) % self.MAX_SEQ_R > 0 and (self.expectedseq - seq) % self.MAX_SEQ_R <= self.receiverN:
                sndpkt = self.make_pkt(seq, b'ACK')
                self.sock.sendto(sndpkt['msg'], client_address)
            if seq == self.expectedseq:
                while self.buffered.get(self.expectedseq) is not None:
                    data = self.getbuffered(self.expectedseq)
                    self.datatodeliver.append(data)
                    del self.buffered[self.expectedseq]
                    self.expectedseq = (self.expectedseq + 1) % self.MAX_SEQ_R
                deliverlist = self.datatodeliver
                self.datatodeliver = []
                return deliverlist
            
            
    def rdt_send(self, data, addr):
        if len(self.sndpkt) < self.senderN:
            self.sndpkt[self.nextseqnum] = self.make_pkt(self.nextseqnum, data.encode(), addr)
            self.sock.sendto(self.sndpkt[self.nextseqnum]['msg'], self.sndpkt[self.nextseqnum]['addr'])
            self.start_timer(self.nextseqnum)
            self.nextseqnum = (self.nextseqnum + 1) % self.MAX_SEQ_S
        else:
            print('Queque full, please wait...')
            
    def loopsocket(self):
        #Check for acks and timeout, update queque if received, resend if timer runs out or if receiving duplicates
        if len(self.start_times) > 0:
            for seq, start_time in self.start_times.items():
                if start_time > 0 and time.time() - start_time > self.timeoutlimit:
                    self.timeout(seq)
        ready, _, _ = select.select([self.sock], [], [], 0.0)
        if ready:
            data, addr = self.sock.recvfrom(265)
            crc8 = self.calcCrc8(data)
            if crc8 == 0:
                seq = self.getseq(data)
                if seq in self.sndpkt:
                    self.markackd(seq)
                    self.stop_timer(seq)
                if seq == self.base:
                    while self.base in self.sndpkt and self.sndpkt[self.base]['ackd']:
                        del self.sndpkt[self.base]
                        self.base = (self.base + 1) % self.MAX_SEQ_S
        
            