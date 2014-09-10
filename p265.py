import bsb
import naluh
import vps
import sps
import pps
import slice
import image

class P265:
    def __init__(self, bit_stream = "str.bin"):
        self.img = image.Image()
        self.bs = bsb.BitStreamBuffer(bit_stream)
        self.naluh = naluh.NaluHeader(self.bs)
        self.vps = [0] * 256 # TODO: make the size precise
        self.sps = [0] * 256
        self.pps = [0] * 256
        self.slice = slice.SliceSegment(self.bs, self.naluh, self.vps, self.sps, self.pps, self.img)

    def decode_nal_units(self):
        while True:
            self.bs.search_start_code()
            self.bs.report_position()

            self.naluh.decode()
            nalu_type = self.naluh.nal_unit_type

            if nalu_type == 32:
                self.decode_vps()
            elif nalu_type == 33:
                self.decode_sps()
            elif nalu_type == 34:
                self.decode_pps()
            elif nalu_type == 19:
                self.decode_slice()
            else:
                print "Error: unimplemeted NALU type = %d." % nalu_type
                raise "Intensional raise"
    
    def decode_slice(self):
        self.slice.decode()

    def decode_vps(self):
        v = vps.Vps(self.bs)
        v.parse()
        self.vps[v.vps_video_parameter_set_id] = v

    def decode_sps(self):
        s = sps.Sps(self.bs)
        s.parse()
        self.sps[s.sps_seq_parameter_set_id] = s

    def decode_pps(self):
        p = pps.Pps(self.bs)
        p.parse()
        self.pps[p.pps_pic_parameter_set_id] = p


if __name__ == "__main__":
    p265 = P265("str.bin")
    p265.decode_nal_units()
