import numpy as np
import log

class Sao:
    def __init__(self, ctx):
        self.ctx = ctx

        self.cabac = self.ctx.cabac

        self.img = self.ctx.img

        self.pps = self.ctx.pps
        self.sps = self.ctx.sps

    def parse(self):
        self.slice_hdr = self.img.slice_hdr
        self.slice_hdrs = self.img.slice_hdrs

        self.ctu = self.img.ctu
        self.ctus = self.img.ctus

        rx = self.ctu.x_ctb
        ry = self.ctu.y_ctb

        # Decode sao_merge_left_flag
        if rx > 0:
            left_ctb_in_slice_seg = self.ctu.addr_rs > self.ctu.slice_addr
            left_ctb_in_tile =  self.pps.tile_id[self.ctu.addr_ts] ==  self.pps.tile_id[self.pps.ctb_addr_rs2ts[self.ctu.addr_rs-1]]
            if left_ctb_in_slice_seg and left_ctb_in_tile:
                self.sao_merge_left_flag = self.parse__sao_merge_left_flag()
        else:
            self.sao_merge_left_flag = 0
        
        # Decode sao_merge_up_flag
        if ry > 0 and (not self.sao_merge_left_flag):
            up_ctb_in_slice_seg = (self.ctu.addr_rs - self.sps.pic_width_in_ctbs_y) >= self.ctu.slice_addr
            up_ctb_in_tile = self.pps.tile_id[self.ctu.addr_ts] == self.pps.tile_id[self.pps.ctb_addr_rs2ts[self.ctu.addr_rs - self.sps.pic_width_in_ctbs_y]]
            if up_ctb_in_slice_seg and up_ctb_in_tile:
                self.sao_merge_up_flag = self.parse__sao_merge_up_flag()
        else:
            self.sao_merge_up_flag = 0
        
        self.sao_type_idx = np.zeros(3, int) #[0] * 3
        self.sao_offset_abs = np.zeros((3, 4), int) #[[0] * 4] * 3
        self.sao_offset_sign = np.zeros((3, 4), int) #[[0] * 4] * 3
        self.sao_band_position = np.zeros(3, int) #[0] * 3
        self.sao_eo_class = np.zeros(3, int) #[0] * 3

        #TODO: check default value assignments
        if (not self.sao_merge_up_flag) and (not self.sao_merge_left_flag):
            for c_idx in range(3):
                if (self.slice_hdr.slice_sao_luma_flag and c_idx == 0) or (self.slice_hdr.slice_sao_chroma_flag and c_idx > 0):
                    if c_idx == 0:
                        self.sao_type_idx_luma = self.parse__sao_type_idx_luma()
                        self.sao_type_idx[0] = self.sao_type_idx_luma
                    elif c_idx == 1:
                        self.sao_type_idx_chroma = self.parse__sao_type_idx_chroma()
                        self.sao_type_idx[1] = self.sao_type_idx_chroma
                        self.sao_type_idx[2] = self.sao_type_idx_chroma
                   
                    if self.sao_type_idx[c_idx] != 0:
                        for i in range(4):
                            self.sao_offset_abs[c_idx][i] = self.parse__sao_offset_abs(c_idx, i)

                        if self.sao_type_idx[c_idx] == 1:
                            for i in range(4):
                                if self.sao_offset_abs[c_idx][i] != 0:
                                    self.sao_offset_sign[c_idx][i] = self.parse__sao_offset_sign(c_idx, i)
                            self.sao_band_position[c_idx] = self.parse__sao_band_position(c_idx)
                        else:
                            if c_idx == 0:
                                self.sao_eo_class_luma = self.parse__sao_eo_class_luma()
                                self.sao_eo_class[0] = self.sao_eo_class_luma
                            elif c_idx == 1:
                                self.sao_eo_class_chroma = self.parse__sao_eo_class_chroma()
                                self.sao_eo_class[1] = self.sao_eo_class_chroma
                                self.sao_eo_class[2] = self.sao_eo_class_chroma
        else:
            if self.sao_merge_left_flag:
                left_addr = self.ctu.addr_rs - 1 #(rx - 1) + ry * self.ctx.sps.pic_width_in_ctbs_y
                assert left_addr in self.ctx.img.ctus

            if self.sao_merge_up_flag:
                up_addr = self.ctu.addr_rs - self.ctx.sps.pic_width_in_ctbs_y #rx + (ry - 1) * self.ctx.sps.pic_width_in_ctbs_y
                assert up_addr in self.ctx.img.ctus

            # Set default value of sao_type_idx
            for c_idx in range(3):
                if self.sao_merge_left_flag:
                    self.sao_type_idx[c_idx] = self.ctx.img.ctus[left_addr].sao.sao_type_idx[c_idx]
                elif self.sao_merge_up_flag:
                    self.sao_type_idx[c_idx] = self.ctx.img.ctus[up_addr].sao.sao_type_idx[c_idx]
                else:
                    self.sao_type_idx[c_idx] = 0

            # Set default value of sao_offset_abs
            for c_idx in range(3):
                if self.sao_merge_left_flag:
                    self.sao_offset_abs[c_idx] = self.ctx.img.ctus[left_addr].sao.sao_offset_abs[c_idx]
                elif self.sao_merge_up_flag:
                    self.sao_offset_abs[c_idx] = self.ctx.img.ctus[up_addr].sao.sao_offset_abs[c_idx]
                else:
                    self.sao_offset_abs[c_idx] = [0] * 4

            # Set default value of sao_offset_sign
            for c_idx in range(3):
                if self.sao_merge_left_flag:
                    self.sao_offset_sign[c_idx] = self.ctx.img.ctus[left_addr].sao.sao_offset_sign[c_idx]
                elif self.sao_merge_up_flag:
                    self.sao_offset_sign[c_idx] = self.ctx.img.ctus[up_addr].sao.sao_offset_sign[c_idx]
                elif self.sao_type_idx[c_idx] == 2:
                    for i in range(4):
                        if i == 0 or i == 1:
                            self.sao_offset_sign[c_idx][i] = 0
                        else:
                            self.sao_offset_sign[c_idx][i] = 1
                else:
                    self.sao_offset_sign[c_idx] = [0] * 4

            # Set defualt value of sao_band_position
            for c_idx in range(3):
                if self.sao_merge_left_flag:
                    self.sao_band_position[c_idx] = self.ctx.img.ctus[left_addr].sao.sao_band_position[c_idx]
                elif self.sao_merge_up_flag:
                    self.sao_band_position[c_idx] = self.ctx.img.ctus[up_addr].sao.sao_band_position[c_idx]
                else:
                    self.sao_band_position[c_idx] = 0
            
            # Set default value of sao_eo_class
            for c_idx in range(3):
                if self.sao_merge_left_flag:
                    self.sao_eo_class[c_idx] = self.ctx.img.ctus[left_addr].sao.sao_eo_class[c_idx]
                elif self.sao_merge_up_flag:
                    self.sao_eo_class[c_idx] = self.ctx.img.ctus[up_addr].sao.sao_eo_class[c_idx]
                else:
                    self.sao_eo_class[c_idx] = 0

    def parse__sao_merge_left_flag(self):
        bit = self.cabac.decode_decision("sao_merge_leftup_flag", 0)
        log.syntax.info("sao_merge_left_flag = %d" % bit)
        return bit

    def parse__sao_merge_up_flag(self):
        bit = self.cabac.decode_decision("sao_merge_leftup_flag", 0)
        log.syntax.info("sao_merge_up_flag = %d" % bit)
        return bit

    def parse__sao_type_idx(self, table):
        bit0 = self.cabac.decode_decision(table, 0)

        if bit0 == 0:
            value = 0
        else:
            bit1 = self.cabac.decode_bypass()
            if bit1 == 0:
                value = 1
            else:
                value = 2

        return value
    
    def parse__sao_type_idx_luma(self):
        value = self.parse__sao_type_idx("sao_type_idx_lumachroma_flag")
        log.syntax.info("sao_type_idx_luma = %d" % value)
        return value

    def parse__sao_type_idx_chroma(self):
        value = self.parse__sao_type_idx("sao_type_idx_lumachroma_flag")
        log.syntax.info("sao_type_idx_chroma = %d" % value)
        return value

    def parse__sao_offset_abs(self, c_idx, i):
        if c_idx == 0: 
            bit_depth = self.sps.bit_depth_y
        else:
            bit_depth = self.sps.bit_depth_c

        c_max = (1 << (min(bit_depth, 10) - 5)) - 1
        if c_max == 0:
            value = 0
        else:
            k = 0
            while True:
                bit = self.cabac.decode_bypass()
                if bit == 0: break
                k += 1
                if k == c_max: break
            value = k
                
        log.syntax.info("sao_offset_abs[%s][%d] = %d" % ("luma" if c_idx==0 else "chroma", i, value))
        return value
    
    def parse__sao_offset_sign(self, c_idx, i):
        bit = self.cabac.decode_bypass()
        log.syntax.info("sao_offset_sign[%s][%d] = %d" % ("luma" if c_idx==0 else "chroma", i, bit))
        return bit

    def parse__sao_band_position(self, c_idx):
        value = self.cabac.decode_bypass()

        for i in range(4):
            value = (value << 1) | self.cabac.decode_bypass()
        
        log.syntax.info("sao_band_position[%s] = %d" % ("luma" if c_idx==0 else "chroma", value))
        return value

    def parse__sao_eo_class(self):
        value = self.cabac.decode_bypass() << 1
        value |= self.cabac.decode_bypass()
        return value

    def parse__sao_eo_class_luma(self):
        value = self.parse__sao_eo_class()
        log.syntax.info("sao_eo_class_luma = %d" % value)
        return value
    
    def parse__sao_eo_class_chroma(self):
        value = self.parse__sao_eo_class()
        log.syntax.info("sao_eo_class_chroma = %d" % value)
        return value

