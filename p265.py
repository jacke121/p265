#!/usr/bin/python -B

import nalu
import context
import log

class P265:
    def __init__(self, bs_file= "str.bin"):
        self.ctx = context.Context(bs_file)
        self.nalu = nalu.Nalu(self.ctx)

    def decode(self):
        while True:
            self.ctx.bs.search_start_code()
            self.ctx.bs.report_position()

            self.ctx.naluh = self.nalu.decode_naluh()
            nalu_type = self.ctx.naluh.nal_unit_type

            if nalu_type == nalu.NaluHeader.TRAIL_N:
                self.nalu.decode_slice_seg()
            elif nalu_type == nalu.NaluHeader.TRAIL_R:
                self.nalu.decode_slice_seg()
            elif nalu_type == nalu.NaluHeader.TSA_N:
                self.nalu.decode_slice_seg()
            elif nalu_type == nalu.NaluHeader.TSA_R:
                self.nalu.decode_slice_seg()
            elif nalu_type == nalu.NaluHeader.STSA_N:
                self.nalu.decode_slice_seg()
            elif nalu_type == nalu.NaluHeader.STSA_R:
                self.nalu.decode_slice_seg()
            elif nalu_type == nalu.NaluHeader.RADL_N:
                self.nalu.decode_slice_seg()
            elif nalu_type == nalu.NaluHeader.RADL_R:
                self.nalu.decode_slice_seg()
            elif nalu_type == nalu.NaluHeader.RASL_N:
                self.nalu.decode_slice_seg()
            elif nalu_type == nalu.NaluHeader.RASL_R:
                self.nalu.decode_slice_seg()
            elif nalu_type in range(nalu.NaluHeader.RSV_VCL_N10, nalu.NaluHeader.RSV_VCL_R15+1):
                log.main.error("Reserved NALU type - RSV_VCL_N10~RSV_VCL_R15.")
            elif nalu_type == nalu.NaluHeader.BLA_W_LP:
                self.nalu.decode_slice_seg()
            elif nalu_type == nalu.NaluHeader.BLA_W_RADL:
                self.nalu.decode_slice_seg()
            elif nalu_type == nalu.NaluHeader.BLA_N_LP:
                self.nalu.decode_slice_seg()
            elif nalu_type == nalu.NaluHeader.IDR_W_RADL:
                self.nalu.decode_slice_seg()
            elif nalu_type == nalu.NaluHeader.IDR_N_LP:
                self.nalu.decode_slice_seg()
            elif nalu_type == nalu.NaluHeader.CRA_NUT:
                self.nalu.decode_slice_seg()
            elif nalu_type in range(nalu.NaluHeader.RSV_IRAP_VCL22, nalu.NaluHeader.RSV_IRAP_VCL23+1):
                log.main.error("Reserved NALU type - RSV_IRAP_VCL22~RSV_IRAP_VCL23.")
            elif nalu_type in range(nalu.NaluHeader.RSV_VCL24, nalu.NaluHeader.RSV_VCL31+1):
                log.main.error("Reserved NALU type - RSV_VCL24~RSV_VCL31.")
            elif nalu_type == nalu.NaluHeader.VPS_NUT:
                self.nalu.decode_vps()
            elif nalu_type == nalu.NaluHeader.SPS_NUT:
                self.nalu.decode_sps()
            elif nalu_type == nalu.NaluHeader.PPS_NUT:
                self.nalu.decode_pps()
            elif nalu_type == nalu.NaluHeader.AUD_NUT:
                self.nalu.decode_aud()
            elif nalu_type == nalu.NaluHeader.EOS_NUT:
                self.nalu.decode_eos()
            elif nalu_type == nalu.NaluHeader.EOB_NUT:
                self.nalu.decode_eob()
            elif nalu_type == nalu.NaluHeader.FD_NUT:
                self.nalu.decode_fd()
            elif nalu_type == nalu.NaluHeader.PREFIX_SEI_NUT:
                self.nalu.decode_sei()
            elif nalu_type == nalu.NaluHeader.SUFFIX_SEI_NUT:
                self.nalu.decode_sei()
            elif nalu_type in range(nalu.NaluHeader.RSV_NVCL41, nalu.NaluHeader.RSV_NVCL47+1):
                log.main.error("Reserved NALU type -- RSV_NVCL41~RSV_NVCL47.")
            elif nalu_type in range(nalu.NaluHeader.UNSPEC48, nalu.NaluHeader.UNSPEC63+1):
                log.main.error("Reserved NALU type -- RSV_UNSPEC48~RSV_UNSPEC49.")
            else:
                log.main.error("NALU type should be within 0~63, but got %d." % nalu_type)

if __name__ == "__main__":
    p265 = P265("str.bin")
    p265.decode()
