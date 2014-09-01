import vps
import sps

class NaluHeader:
    def __init__(self, bs):
        self.bs = bs

    def parse(self):
        print >>self.bs.log, "============= NALU Header ============="
        self.forbidden_zero_bit = self.bs.u(1, "forbidden_zero_bit")
        assert(self.forbidden_zero_bit == 0)
        self.nal_unit_type = self.bs.u(6, "nal_unit_type")
        self.nuh_layer_id = self.bs.u(6, "nuh_layer_id")
        self.nuh_temporal_id_plus1 = self.bs.u(3, "nuh_temporal_id_plus1")

class Nalu:
    def __init__(self, bs):
        self.bs = bs
        self.naluh = NaluHeader(bs)
        self.vps = vps.Vps(bs)
        self.sps = sps.Sps(bs)

