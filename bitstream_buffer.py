class BitStreamBuffer:
    def __init__(self, bit_stream = None):
        self.bytes = []
        if isinstance(bit_stream, str):
            with open(bit_stream, 'rb') as f:
                while True:
                    byte = f.read(1)
                    if not byte: break
                    self.bytes.append(ord(byte))
        elif isinstance(bit_stream, list):
            self.bytes = bit_stream
        else:
            raise "Error: either a file name or a list object must be supplied"
        
        self.length = len(self.bytes)
        self.bit_idx = 0 
        self.byte_idx = 0 # points to the current byte being processed
    
    def reset(self):
        self.bit_idx = 0
        self.byte_idx = 0

    def get_byte(self, idx):
        if (idx < self.length):
            return self.bytes[idx]
        else:
            print "Error: indexing a position exceeding bit stream length"
            exit(1)

    def print_buf(self, idx, len):
        for i in range(idx, idx+len):
            print "0x%02x" % self.get_byte(i)
    
    def spare_bits(self):
        mask = (1 << (8 - self.bit_idx)) - 1
        bits =  mask & self.get_byte(self.byte_idx)
        return bits

    def next_bits(self, n):
        saved_byte_idx = self.byte_idx
        saved_bit_idx = self.bit_idx
        bits = self.read_bits(n)
        self.byte_idx = saved_byte_idx
        self.bit_idx = saved_bit_idx

        return bits

    def read_bits(self, n):
        spare_bits_cnt = 8 - self.bit_idx

        if spare_bits_cnt > n:
            bits = self.spare_bits() >> (spare_bits_cnt - n)
            self.bit_idx += n
        elif spare_bits_cnt == n:
            bits = self.spare_bits()
            self.byte_idx += 1
            self.bit_idx = 0
        else:
            bits = self.spare_bits()
            bit_cnt = spare_bits_cnt
            self.byte_idx += 1
            self.bit_idx = 0
            while bit_cnt < n:
                bits = (bits << 8) | self.get_byte(self.byte_idx)
                bit_cnt += 8
                self.byte_idx += 1
                self.bit_idx = 0
            spare_bits_cnt = bit_cnt - n
            if (spare_bits_cnt > 0):
                self.bit_idx = (8 - spare_bits_cnt) % 8
                self.byte_idx -= 1
            bits = bits >> spare_bits_cnt

        return bits
            
if __name__ == '__main__':
    def check(actual, expected, id):
        if (expected == actual): 
            print "[%d] PASS act=0x%x exp=0x%x" % (id, actual, expected)
        else:
            print "[%d] ***FAIL*** act=0x%x exp=0x%x" % (id, actual, expected)
            exit(1)

    bsb = BitStreamBuffer([0x78, 0x25, 0x32, 0x12, 0x88])
    bsb.print_buf(0, 4)

    check(bsb.read_bits(16), 0x7825, 0)
    check(bsb.read_bits(3), 0b001, 1)
    check(bsb.read_bits(2), 0b10, 2)
    check(bsb.read_bits(4), 0b0100, 3)
    check(bsb.read_bits(3), 0b001, 4)
    check(bsb.read_bits(5), 0b00101, 5)
    check(bsb.read_bits(4), 0b0001, 6)
    check(bsb.read_bits(3), 0b000, 7)

    bsb.reset()

    check(bsb.read_bits(16), 0x7825, 8)
    check(bsb.next_bits(16), 0x3212, 9)
    check(bsb.read_bits(3), 0b001, 10)
    check(bsb.next_bits(1), 0b1, 11)
    check(bsb.read_bits(2), 0b10, 12)
    check(bsb.read_bits(4), 0b0100, 13)
    check(bsb.read_bits(3), 0b001, 14)
    check(bsb.read_bits(5), 0b00101, 15)
    check(bsb.read_bits(4), 0b0001, 16)
    check(bsb.read_bits(3), 0b000, 17)

    print "Cong! All checking passed."
