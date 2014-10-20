import math
import exception
import log

#TODO: use get_byte() instead of directly accessing bytes list
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

        self.byte_idx = 0
        self.bit_idx = 0
        self.length = len(self.bytes)

    def report_position(self):
        log.main.debug("Bit stream position: byte_idx = %d, bit_idx = %d, addr = 0x%x, colum = %d" % (self.byte_idx, self.bit_idx, (self.byte_idx / 16) << 4, (self.byte_idx % 16 )))

    def reset(self):
        self.bit_idx = 0
        self.byte_idx = 0

    def print_buf(self, idx, len):
        for i in range(idx, idx+len):
            print "0x%02x" % self.bytes[i]

    def byte_alignment(self):
        alignment_bit_equal_to_one = self.read_bits(1)
        assert alignment_bit_equal_to_one == 1

        while not self.byte_aligned():
            alignment_bit_equal_to_zero = self.read_bits(1)
            assert alignment_bit_equal_to_zero == 0

        #if self.bit_idx==0:
        #    return
        #else:
        #    self.byte_idx += 1
        #    self.bit_idx = 0
    
    def byte_aligned(self):
        return self.bit_idx == 0

    def get_byte(self, idx):
        if idx >= self.length:
            raise exception.EndOfBitStreamFileError
        else:
            return self.bytes[idx]

    def search_start_code(self):
        watch_dog_counter = 0
        while True:
            try:
                byte0 = self.get_byte(self.byte_idx)
                byte1 = self.get_byte(self.byte_idx - 1) if self.byte_idx >= 2 else 0xff
                byte2 = self.get_byte(self.byte_idx - 2) if self.byte_idx >= 2 else 0xff
            except exception.EndOfBitStreamFileError:
                log.main.info("End of bitstream file when searching start code. Stopped.")
                exit()

            self.byte_idx += 1
            if (byte2==0x00 and byte1==0x00 and byte0==0x01):
                self.bit_idx = 0
                break
            watch_dog_counter += 1
            if (watch_dog_counter == 1024):
                raise exception.WatchDogTimerError("Can not find start code after 1024 bytes were searched, stopped.")
    
    def read_bits(self, n):
        spare_bits_cnt = 8 - self.bit_idx

        if (8-self.bit_idx) > n:
            mask = (1 << (8 - self.bit_idx)) - 1
            bits = mask & self.bytes[self.byte_idx]
            bits = bits >> (8- self.bit_idx - n)
            self.bit_idx += n
            return bits
        elif (8-self.bit_idx) == n:
            mask = (1 << (8 - self.bit_idx)) - 1
            bits = mask & self.bytes[self.byte_idx]
            self.byte_idx += 1
            self.bit_idx = 0
            byte0 = self.bytes[self.byte_idx]
            byte1 = self.bytes[self.byte_idx - 1]
            byte2 = self.bytes[self.byte_idx - 2]
            if byte2==0x00 and byte1==0x00 and byte0==0x03:
                self.byte_idx += 1
        else:
            mask = (1 << (8 - self.bit_idx)) - 1
            bits = mask & self.bytes[self.byte_idx]
            self.byte_idx += 1
            self.bit_idx = 0
            byte0 = self.bytes[self.byte_idx]
            byte1 = self.bytes[self.byte_idx - 1]
            byte2 = self.bytes[self.byte_idx - 2]
            if byte2==0x00 and byte1==0x00 and byte0==0x03:
                self.byte_idx += 1
            
            bit_cnt = spare_bits_cnt
            while bit_cnt < n:
                bits = (bits << 8) | self.bytes[self.byte_idx]
                bit_cnt += 8
                self.byte_idx += 1
                self.bit_idx = 0
                byte0 = self.bytes[self.byte_idx]
                byte1 = self.bytes[self.byte_idx - 1]
                byte2 = self.bytes[self.byte_idx - 2]
                if byte2==0x00 and byte1==0x00 and byte0==0x03:
                    self.byte_idx += 1

            if ((bit_cnt - n) > 0):
                self.bit_idx = (8 - (bit_cnt - n)) % 8
                self.byte_idx -= 1
                byte0 = self.bytes[self.byte_idx]
                byte1 = self.bytes[self.byte_idx - 1]
                byte2 = self.bytes[self.byte_idx - 2]
                if byte2==0x00 and byte1==0x00 and byte0==0x03:
                    self.byte_idx -= 1
                
            bits = bits >> (bit_cnt - n)

        return bits
    
    def next_bits(self, n):
        saved_byte_idx = self.byte_idx
        saved_bit_idx = self.bit_idx

        bits = self.read_bits(n)

        self.byte_idx = saved_byte_idx
        self.bit_idx = saved_bit_idx

        return bits

    def f(self, n, name):
        bits = self.read_bits(n)
        log.syntax.info("%s = %d" % (name, bits))
        return bits

    def u(self, n, name):
        bits = self.read_bits(n)
        log.syntax.info("%s = %d" % (name, bits))
        return bits

    def se(self, name):
        k = self.ue(name, True)
        code_num = ((-1)**(k+1)) * int(math.ceil(float(k)/2))
        log.syntax.info("%s = %d" % (name, code_num))
        return code_num
   
    def ue(self, name, no_print = False):
        leading_zero_bits = 0
        while self.read_bits(1) == 0:
            leading_zero_bits += 1

        code_num = 2**leading_zero_bits - 1 + self.read_bits(leading_zero_bits)    
        if not no_print:
            log.syntax.info("%s = %d" % (name, code_num))

        return code_num

    def more_rbsp_data(self):
        raise "Not implemeted yet"

    def rbsp_trailing_bits(self):
        raise "Not implemeted yet"

if __name__ == '__main__':
    def check(actual, expected, id):
        if (expected == actual): 
            print "[%d] PASS act=0x%x exp=0x%x" % (id, actual, expected)
        else:
            print "[%d] ***FAIL*** act=0x%x exp=0x%x" % (id, actual, expected)

    bsb = BitStreamBuffer([0x78, 0x25, 0x32, 0x12, 0x88, 0x21])
    bsb.print_buf(0, 4)

    print "======== Testing read_bits() =========="
    check(bsb.read_bits(16), 0x7825, 0)
    check(bsb.read_bits(3), 0b001, 1)
    check(bsb.read_bits(2), 0b10, 2)
    check(bsb.read_bits(4), 0b0100, 3)
    check(bsb.read_bits(3), 0b001, 4)
    check(bsb.read_bits(5), 0b00101, 5)
    check(bsb.read_bits(4), 0b0001, 6)
    check(bsb.read_bits(3), 0b000, 7)

    print "======== Testing next_bits() =========="
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

    print "======== Testing read_bits() with 0x000003 =========="
    bsb = BitStreamBuffer([0x78, 0x00, 0x00, 0x03, 0x82, 0x12, 0x88, 0x21])
    bsb.print_buf(0, 4)
    bsb.reset()
    check(bsb.read_bits(24), 0x780000, 18)
    check(bsb.read_bits(8), 0x82, 19)
    bsb.reset()
    check(bsb.read_bits(23), 0x780000 >> 1, 19)
    check(bsb.read_bits(5), 0b01000, 20)
    check(bsb.read_bits(5), 0b00100, 21)
    check(bsb.read_bits(15), 0x1288, 22)

    print "======== Testing search_start_code() =========="
    bsb = BitStreamBuffer([0x00, 0x00, 0x01, 0x03, 0x82, 0x12, 0x88])
    bsb.search_start_code()
    check(bsb.byte_idx, 3, 23)
    check(bsb.bit_idx, 0, 24)

    print "Cong! All checking passed."
