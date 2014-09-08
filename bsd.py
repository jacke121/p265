import bsb
import vps
import sps
import pps
import nalu

class BitStreamDecoder:
    def __init__(self, bs):
        self.bs = bs
        self.nalu = nalu.Nalu(bs)

    def parse(self):
        while True:
            self.bs.search_start_code()
            self.bs.report_position()

            self.nalu.naluh.parse()
            nalu_type = self.nalu.naluh.nal_unit_type

            if nalu_type == 32:
                self.nalu.vps.parse()
                self.bs.report_position()
            elif nalu_type == 33:
                self.nalu.sps.parse()
                self.bs.report_position()
            elif nalu_type == 34:
                self.nalu.pps.parse()
                self.bs.report_position()
            elif nalu_type == 19:
                self.nalu.slice.parse()
                self.bs.report_position()
            else:
                print "Error: unimplemeted NALU type = %d." % nalu_type
                raise "Intensional raise"

if __name__ == "__main__":
    bs = bsb.BitStreamBuffer("str.bin")
    annexb = BitStreamDecoder(bs)
    annexb.parse()
