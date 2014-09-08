import vps
import sps
import pps
import slice

class NaluHeader:
    def __init__(self, bs):
        self.bs = bs

        self.TRAIL_N =0
        self.TRAIL_R =1
        self.TSA_N = 2
        self.TSA_R = 3
        self.STSA_N = 4
        self.STSA_R = 5
        self.RADL_N = 6
        self.RADL_R = 7
        self.RASL_N = 8
        self.RASL_R = 9
        self.RSV_VCL_N10 = 10
        self.RSV_VCL_N12 = 12
        self.RSV_VCL_N14 = 14
        self.RSV_VCL_R11 = 11
        self.RSV_VCL_R13 = 13
        self.RSV_VCL_R15 = 15
        self.BLA_W_LP = 16     # BLA = broken link access
        self.BLA_W_RADL = 17
        self.BLA_N_LP = 18
        self.IDR_W_RADL = 19
        self.IDR_N_LP = 20
        self.CRA_NUT = 21     # CRA = clean random access
        self.RSV_IRAP_VCL22 = 22
        self.RSV_IRAP_VCL23 = 23
        self.RSV_VCL24 = 24
        self.RSV_VCL25 = 25
        self.RSV_VCL26 = 26
        self.RSV_VCL27 = 27
        self.RSV_VCL28 = 28
        self.RSV_VCL29 = 29
        self.RSV_VCL30 = 30
        self.RSV_VCL31 = 31
        self.VPS_NUT = 32
        self.SPS_NUT = 33
        self.PPS_NUT = 34
        self.AUD_NUT = 35
        self.EOS_NUT = 36
        self.EOB_NUT = 37
        self.FD_NUT = 38
        self.PREFIX_SEI_NUT = 39
        self.SUFFIX_SEI_NUT = 40
        self.RSV_NVCL41 = 41
        self.RSV_NVCL42 = 42
        self.RSV_NVCL43 = 43
        self.RSV_NVCL44 = 44
        self.RSV_NVCL45 = 45
        self.RSV_NVCL46 = 46
        self.RSV_NVCL47 = 47
        self.UNDEFINED = 255

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
        self.pps = pps.Pps(bs)
        self.slice = slice.SliceSegment(bs, self.naluh, self.vps, self.sps, self.pps)

