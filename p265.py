import bsb
import nalu
import vps
import sps
import pps
import slice
import image
import context

import logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

class P265:
    def __init__(self, bs= "str.bin"):
        self.ctx = context.Context(bs)
        self.bs = self.ctx.bs
        self.nalu = nalu.Nalu(self.ctx)

    def decode(self):
        while True:
            self.bs.search_start_code()
            self.bs.report_position()

            self.ctx.naluh = self.nalu.decode_naluh()
            nalu_type = self.ctx.naluh.nal_unit_type

            if nalu_type == 32:
                self.nalu.decode_vps()
            elif nalu_type == 33:
                self.nalu.decode_sps()
            elif nalu_type == 34:
                self.nalu.decode_pps()
            elif nalu_type == 19:
                self.nalu.decode_slice_seg()
            else:
                log.error("Unimplemeted NALU type = %d." % nalu_type)
                raise "Intensional raise"

if __name__ == "__main__":
    p265 = P265("str.bin")
    p265.decode()
