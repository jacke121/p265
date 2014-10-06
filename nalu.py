import slice
import vps
import sps
import pps
import log

class NaluHeader:
    TRAIL_N =0
    TRAIL_R =1
    TSA_N = 2
    TSA_R = 3
    STSA_N = 4
    STSA_R = 5
    RADL_N = 6
    RADL_R = 7
    RASL_N = 8
    RASL_R = 9
    RSV_VCL_N10 = 10
    RSV_VCL_N12 = 12
    RSV_VCL_N14 = 14
    RSV_VCL_R11 = 11
    RSV_VCL_R13 = 13
    RSV_VCL_R15 = 15
    BLA_W_LP = 16
    BLA_W_RADL = 17
    BLA_N_LP = 18
    IDR_W_RADL = 19
    IDR_N_LP = 20
    CRA_NUT = 21
    RSV_IRAP_VCL22 = 22
    RSV_IRAP_VCL23 = 23
    RSV_VCL24 = 24
    RSV_VCL25 = 25
    RSV_VCL26 = 26
    RSV_VCL27 = 27
    RSV_VCL28 = 28
    RSV_VCL29 = 29
    RSV_VCL30 = 30
    RSV_VCL31 = 31
    VPS_NUT = 32
    SPS_NUT = 33
    PPS_NUT = 34
    AUD_NUT = 35
    EOS_NUT = 36
    EOB_NUT = 37
    FD_NUT = 38
    PREFIX_SEI_NUT = 39
    SUFFIX_SEI_NUT = 40
    RSV_NVCL41 = 41
    RSV_NVCL42 = 42
    RSV_NVCL43 = 43
    RSV_NVCL44 = 44
    RSV_NVCL45 = 45
    RSV_NVCL46 = 46
    RSV_NVCL47 = 47
    UNSPEC48 = 48
    UNSPEC49 = 49
    UNSPEC50 = 50
    UNSPEC51 = 51
    UNSPEC52 = 52
    UNSPEC53 = 53
    UNSPEC54 = 54
    UNSPEC55 = 55
    UNSPEC56 = 56
    UNSPEC57 = 57
    UNSPEC58 = 58
    UNSPEC59 = 59
    UNSPEC60 = 60
    UNSPEC61 = 61
    UNSPEC62 = 62
    UNSPEC63 = 63

    def __init__(self, bs):
        self.bs = bs

    def decode(self):
        log.main.info("============= NALU Header =============")

        self.forbidden_zero_bit = self.bs.u(1, "forbidden_zero_bit")
        assert(self.forbidden_zero_bit == 0)

        self.nal_unit_type = self.bs.u(6, "nal_unit_type")
        self.nuh_layer_id = self.bs.u(6, "nuh_layer_id")

        self.nuh_temporal_id_plus1 = self.bs.u(3, "nuh_temporal_id_plus1")
        self.nuh_temporal_id = self.nuh_temporal_id_plus1 - 1

class Nalu:
    def __init__(self, ctx):
        self.ctx = ctx
        self.bs = self.ctx.bs

        self.slice_seg = slice.SliceSegment(self.ctx)

    def decode_naluh(self):
        naluh = NaluHeader(self.bs)
        naluh.decode()
        return naluh

    def decode_slice_seg(self):
        self.slice_seg.decode()

    def decode_vps(self):
        v = vps.Vps(self.ctx)
        v.parse()
        self.ctx.vps_list[v.vps_video_parameter_set_id] = v

    def decode_sps(self):
        s = sps.Sps(self.ctx)
        s.parse()
        self.ctx.sps_list[s.sps_seq_parameter_set_id] = s

    def decode_pps(self):
        p = pps.Pps(self.ctx)
        p.parse()
        self.ctx.pps_list[p.pps_pic_parameter_set_id] = p

    def decode_aud(self):
        raise ValueError("Unsupported NALU type - AUD_NUT")

    def decode_eos(self):
        raise ValueError("Unsupported NALU type - EOS_NUT")

    def decode_eob(self):
        raise ValueError("Unsupported NALU type - EOB_NUT")

    def decode_fd(self):
        raise ValueError("Unsupported NALU type - FD_NUT")

    def decode_sei(self):
        raise ValueError("Unsupported NALU type - SEI_NUT")
