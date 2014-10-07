import sys
import random
import math
import sao
import tree
import log

class IntraPartMode:
    PART_2Nx2N = 0
    PART_NXN = 1

class InterPartMode:
    PART_2Nx2N = 0
    PART_2NxN = 1
    PART_Nx2N = 2
    PART_NxN = 3
    PART_2NxnU = 4
    PART_2NxnD = 5
    PART_nLx2N = 6
    PART_nRx2N = 7

class Cu(tree.Tree):
    def __init__(self, x, y, log2size, depth=0, parent=None):
        tree.Tree.__init__(self, x, y, log2size, depth, parent)

        self.MODE_INTER = 0
        self.MODE_INTRA = 1
        self.MODE_SKIP = 2

    def decode_leaf(self):
        assert self.is_leaf() == True

        if self.ctx.pps.transquant_bypass_enabled_flag:
            self.cu_transquant_bypass_flag = self.decode_cu_transquant_bypass_flag()

        if not self.ctx.img.slice_hdr.is_I_slice():
            self.cu_skip_flag = self.decode_cu_skip_flag()

        if self.cu_skip_flag:
            self.decode_prediction_unit()
            self.pred_mode = self.MODE_SKIP
        else:
            if self.ctx.img.slice_hdr.is_I_slice():
                self.pred_mode = self.MODE_INTRA
            else:
                self.pred_mode_flag = self.decode_pred_mode_flag()
                if self.pred_mode_flag == 0:
                    self.pred_mode = self.MODE_INTER
                else:
                    self.pred_mode = self.MODE_INTRA

            if self.pred_mode != self.MODE_INTRA or self.log2size == self.ctx.sps.min_cb_log2_size_y:
                self.decode_part_mode()
                if self.pred_mode == self.MODE_INTRA:
                    if self.part_mode == IntraPartMode.PART_2Nx2N:
                        self.intra_split_flag = 0
                    else:
                        self.intra_split_flag = 1
            else:
                self.part_mode = 0
                self.intra_split_flag = 0

            if self.pred_mode == self.MODE_INTRA:
                if self.part_mode == IntraPartMode.PART_2Nx2N and self.ctx.sps.pcm_enabled_flag == 1 and self.log2size >= self.ctx.sps.log2_min_pcm_luma_coding_block_size and self.log2size <= self.ctx.sps.log2_max_pcm_luma_coding_block_size:
                    self.pcm_flag = self.decode_pcm_flag()
                else:
                    self.pcm_flag = 0

                if self.pcm_flag == 1:
                     while not self.ctx.bs.byte_aligned():
                         self.pcm_alignment_zero_bit = self.ctx.bs.f(1, "pcm_alignment_zero_bit")
                         assert self.pcm_alignment_zero_bit == 0
                     self.decode_pcm_sample()
                else:
                    self.intra_pred_mode()
            else:
                self.decode_inter_pred_info()

            if self.pcm_flag == 0:
                if self.pred_mode != self.MODE_INTRA and not(self.part_mode == InterPartMode.PART.2Nx2N and self.merge_flag == 1):
                    self.rqt_root_cbf = self.decode_rqt_root_cbf()
                if self.rqt_root_cbf:
                    if self.pred_mode == self.MODE_INTRA:
                        self.max_transform_depth = self.ctx.sps.max_transform_hierarchy_depth_intra + self.intra_split_flag
                    else:
                        self.max_transform_depth = self.ctx.sps.max_transform_hierarchy_depth_inter
                    self.tu = Tu(self.x, self.y, self.log2size, depth=0, parent=None)
                    self.tu.decode(self.ctxi, self)
    
    def decode_inter_pred_info(self):
        if self.part_mode == InterPartMode.PART_2Nx2N:
            self.decode_prediction_unit(self.x, self.y, self.size, self.size)
        elif self.part_mode == InterPartMode.PART_2NxN:
            self.decode_prediction_unit(self.x, self.y, self.size, self.size/2)
            self.decode_prediction_unit(self.x, self.y+self.size/2, self.size, self.size/2)
        elif self.part_mode == InterPartMode.PART_Nx2N:
            self.decode_prediction_unit(self.x, self.y, self.size/2, self.size)
            self.decode_prediction_unit(self.x+self.size/2, self.y, self.size/2, self.size)
        elif self.part_mode == InterPartMode.PART_2NxnN:
            self.decode_prediction_unit(self.x, self.y, self.size, self.size/4)
            self.decode_prediction_unit(self.x, self.y+self.size/4, self.size, self.size*3/4)
        elif self.part_mode == InterPartMode.PART_2NxnD:
            self.decode_prediction_unit(self.x, self.y, self.size, self.size*3/4)
            self.decode_prediction_unit(self.x, self.y+(self.size*3/4), self.size, self.size/4)
        elif self.part_mode == InterPartMode.PART_nLx2N:
            self.decode_prediction_unit(self.x, self.y, self.size/4, self.size)
            self.decode_prediction_unit(self.x+self.size/4, self.y, self.size*3/4, self.size)
        elif self.part_mode == InterPartMode.PART_nRx2N:
            self.decode_prediction_unit(self.x, self.y, self.size*3/4, self.size)
            self.decode_prediction_unit(self.x+self.size*3/4, self.y, self.size/4, self.size)
        else: #PART_NxN
            self.decode_prediction_unit(self.x, self.y, self.size/2, self.size/2)
            self.decode_prediction_unit(self.x+self.size/2, self.y, self.size/2, self.size/2)
            self.decode_prediction_unit(self.x, self.y+self.size/2, self.size/2, self.size/2)
            self.decode_prediction_unit(self.x+self.size/2, self.y+self.size/2, self.size/2, self.size/2)

    def decode_coding_quadtree(self):
        right_boundary_within_pic_flag = (self.x + (1 << self.log2size)) <= self.ctx.sps.pic_width_in_luma_samples
        bottom_boundary_within_pic_flag = (self.y + (1 << self.log2size)) <= self.ctx.sps.pic_height_in_luma_samples
        minimum_cb_flag = self.log2size <= self.ctx.sps.min_cb_log2_size_y

        if right_boundary_within_pic_flag and bottom_boundary_within_pic_flag and (not minimum_cb_flag):
            self.decode_split_cu_flag()
        else:
            if log2size > self.ctx.sps.min_cb_log2_size_y:
                self.split_cu_flag = 1
            else:
                self.split_cu_flag = 0
        
        #TODO
        """
        if cu_qp_delta_enabled_flag and ...:
            is_cu_qp_delta_coded = 0
            cu_qp_delta_val = 0
        """
        
        if self.split_cu_flag:
            x0 = self.x
            y0 = self.y
            x1 = self.x + (1 << self.log2size)
            y1 = self.y + (1 << self.log2size)

            sub_cu = [None] * 4
            sub_cu[0] = Cu(x0, y0, self.log2size-1, self.depth+1, self); 
            sub_cu[1] = Cu(x1, y0, self.log2size-1, self.depth+1, self); 
            sub_cu[2] = Cu(x0, y1, self.log2size-1, self.depth+1, self); 
            sub_cu[3] = Cu(x1, y1, self.log2size-1, self.depth+1, self); 

            for i in range(4):
                sub_cu[i].ctx = self.ctx

            sub_cu[0].within_boundary_flag = True
            sub_cu[1].within_boundary_flag = x1 < self.ctx.sps.pic_width_in_luma_samples
            sub_cu[2].within_boundary_flag = y1 < self.ctx.sps.pic_height_in_luma_samples
            sub_cu[3].within_boundary_flag = x1 < self.ctx.sps.pic_width_in_luma_samples and y1 < self.ctx.sps.pic_height_in_luma_samples

            for i in range(4):
                self.add_child(sub_cu[i])

            for child in self.children:
                child.decode_coding_quadtree()
        else:
            self.decode_leaf()

    def decode_split_cu_flag(self):
        x0 = self.x
        y0 = self.y
        depth = self.depth

        available_left  = self.ctx.img.check_availability(x0, y0, x0-1, y0)
        available_above = self.ctx.img.check_availability(x0, y0, x0, y0-1)

        cond_left = 1 if available_left  and self.ctx.img.get_cqt_depth(x0-1, y0) > depth else 0
        cond_above= 1 if available_above and self.ctx.img.get_cqt_depth(x0, y0-1) > depth else 0

        context_inc = cond_left + cond_above

        if self.ctx.img.slice_hdr.init_type == 0:
            context_offset = 0
        elif self.ctx.img.slice_hdr.init_type == 1:
            context_offset = 3
        elif self.ctx.img.slice_hdr.init_type == 2:
            context_offset = 6
        else:
            raise ValueError("Unexpected init type.")

        context_idx = context_offset + context_inc

        self.split_cu_flag = self.ctx.cabac.decode_bin("split_cu_flag", context_idx, 0)
        log.syntax.info("split_cu_flag = %d" % self.split_cu_flag)
    
    def check_part_mode(self):
        if self.pred_mode == self.MODE_INTRA:
            assert self.part_mode in (0, 1)
        else:
            if self.log2size > self.ctx.sps.min_cb_log2_size_y and self.ctx.sps.amp_enabled_flag == 1:
                assert self.part_mode in (0,1,2,4,5,6,7)
            elif (self.log2size > self.ctx.sps.min_cb_log2_size_y and self.ctx.sps.amp_enabled_flag == 0) or self.log2size == 3:
                assert self.part_mode in (0,1,2)
            else:
                assert self.part_mode in (0,1,2,3)

    def decode_part_mode(self):
        self.check_part_mode()
        pass

class Ctu(Cu):
    def __init__(self, ctx, addr_rs):
        x = (addr_rs % ctx.sps.pic_width_in_ctbs_y) << ctx.sps.ctb_log2_size_y
        y = (addr_rs / ctx.sps.pic_width_in_ctbs_y) << ctx.sps.ctb_log2_size_y
        Cu.__init__(self, x, y, ctx.sps.ctb_log2_size_y, depth=0, parent=None)

        self.ctx = ctx

        self.slice_addr = 0
        self.sps = self.ctx.sps
        self.pps = self.ctx.pps
        self.addr_rs = addr_rs

        self.x_ctb = self.x >> self.ctx.sps.ctb_log2_size_y
        self.y_ctb = self.y >> self.ctx.sps.ctb_log2_size_y

        self.sao = sao.Sao(self.ctx, self.x_ctb, self.y_ctb)

    def decode(self):
        if self.ctx.img.slice_hdr.slice_sao_luma_flag or self.ctx.img.slice_hdr.slice_sao_chroma_flag:
            self.sao.decode()
        
        self.decode_coding_quadtree()

        print(self)

if __name__ == "__main__":
    class Sps:
        def __init__(self, pic_width_in_ctbs, pic_width_in_min_cbs, ctb_log2_size, min_cb_log2_size):
            self.pic_width_in_ctbs_y = pic_width_in_ctbs
            self.pic_width_in_min_cbs_y = pic_width_in_min_cbs
            self.ctb_log2_size_y = ctb_log2_size
            self.min_cb_log2_size_y = min_cb_log2_size
            self.ctb_size_y = 1 << self.ctb_log2_size_y
            self.min_cb_size_y = 1 << self.min_cb_log2_size_y

            self.pic_height_in_ctbs_y = self.pic_width_in_ctbs_y
            self.pic_height_in_min_cbs_y = self.pic_width_in_min_cbs_y

    ctb1 = Ctb(addr=3, sps=Sps(2, 16, 6, 3))
    if ctb1.addr != 3: raise 

    ctb1.set_cqt_depth(64, 64, 5, 1)
    ctb1.set_cqt_depth(0xc*8, 0xc*8, 4, 1)
