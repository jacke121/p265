#!/usr/bin/python -B

import decoder.nalu as nalu
import decoder.context as context
import decoder.log as log

class Decoder:
    def __init__(self, bs_file= "str.bin"):
        self.ctx = context.Context(bs_file)
        self.nalu = nalu.Nalu(self.ctx)
        self.frame_cnt = 0
        log.main.disabled = True
        log.syntax.disabled = True
        log.cabac.disabled = True
        log.location.disabled = True

    def decode(self):
        while True:
            self.ctx.bs.search_start_code()
            self.ctx.bs.report_position()

            self.ctx.naluh = self.nalu.decode_naluh()
            nalu_type = self.ctx.naluh.nal_unit_type

            if nalu_type == nalu.NaluHeader.TRAIL_N or \
                    nalu_type == nalu.NaluHeader.TRAIL_R or \
                    nalu_type == nalu.NaluHeader.TSA_N or \
                    nalu_type == nalu.NaluHeader.TSA_R or \
                    nalu_type == nalu.NaluHeader.STSA_N or \
                    nalu_type == nalu.NaluHeader.STSA_R or \
                    nalu_type == nalu.NaluHeader.RADL_N or \
                    nalu_type == nalu.NaluHeader.RADL_R or \
                    nalu_type == nalu.NaluHeader.RASL_N or \
                    nalu_type == nalu.NaluHeader.RASL_R or \
                    nalu_type == nalu.NaluHeader.BLA_W_LP or \
                    nalu_type == nalu.NaluHeader.BLA_W_RADL or \
                    nalu_type == nalu.NaluHeader.BLA_N_LP or \
                    nalu_type == nalu.NaluHeader.IDR_W_RADL or \
                    nalu_type == nalu.NaluHeader.IDR_N_LP or \
                    nalu_type == nalu.NaluHeader.CRA_NUT:
                end_of_picture_flag = self.nalu.decode_slice_seg()
                if end_of_picture_flag:
                    log.main.disabled = False
                    log.syntax.disabled = False
                    log.cabac.disabled = False
                    log.location.disabled = False
                    log.location.info("Frame %d decoded" % self.frame_cnt)
                    #raise ValueError("Congratulations! The first frame decoded!")
                    self.frame_cnt += 1
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
            elif nalu_type in range(nalu.NaluHeader.RSV_VCL_N10, nalu.NaluHeader.RSV_VCL_R15+1):
                log.main.error("Reserved NALU type - RSV_VCL_N10~RSV_VCL_R15.")
            elif nalu_type in range(nalu.NaluHeader.RSV_IRAP_VCL22, nalu.NaluHeader.RSV_IRAP_VCL23+1):
                log.main.error("Reserved NALU type - RSV_IRAP_VCL22~RSV_IRAP_VCL23.")
            elif nalu_type in range(nalu.NaluHeader.RSV_VCL24, nalu.NaluHeader.RSV_VCL31+1):
                log.main.error("Reserved NALU type - RSV_VCL24~RSV_VCL31.")
            elif nalu_type in range(nalu.NaluHeader.RSV_NVCL41, nalu.NaluHeader.RSV_NVCL47+1):
                log.main.error("Reserved NALU type -- RSV_NVCL41~RSV_NVCL47.")
            elif nalu_type in range(nalu.NaluHeader.UNSPEC48, nalu.NaluHeader.UNSPEC63+1):
                log.main.error("Reserved NALU type -- RSV_UNSPEC48~RSV_UNSPEC49.")
            else:
                log.main.error("NALU type should be within 0~63, but got %d." % nalu_type)

if __name__ == "__main__":
    d = Decoder("str.bin")
    d.decode()
