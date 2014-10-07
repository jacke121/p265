import sys
import random
import math
import sao
import tree
import log

class Cu(tree.Tree):
    def __init__(self, x, y, log2size, depth=0, parent=None):
        tree.Tree.__init__(self, x, y, log2size, depth, parent)

    def decode(self):
        assert self.is_leaf() == True

        if self.ctx.pps.transquant_bypass_enabled_flag:
            self.decode_cu_transquant_bypass_flag()

        if self.ctx.img.slice_hdr.slice_type != self.ctx.img.slice_hdr.I_SLICE:
            self.decode_cu_skip_flag()

        #if self.cu_skip_flag
        raise "Unimplemented yet." 

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

            cu = [None] * 4
            cu[0] = Cu(x0, y0, self.log2size-1, self.depth+1, self); 
            cu[1] = Cu(x1, y0, self.log2size-1, self.depth+1, self); 
            cu[2] = Cu(x0, y1, self.log2size-1, self.depth+1, self); 
            cu[3] = Cu(x1, y1, self.log2size-1, self.depth+1, self); 

            for i in range(4):
                cu[i].ctx = self.ctx

            cu[0].within_boundary_flag = True
            cu[1].within_boundary_flag = x1 < self.ctx.sps.pic_width_in_luma_samples
            cu[2].within_boundary_flag = y1 < self.ctx.sps.pic_height_in_luma_samples
            cu[3].within_boundary_flag = x1 < self.ctx.sps.pic_width_in_luma_samples and y1 < self.ctx.sps.pic_height_in_luma_samples

            for i in range(4):
                self.add_child(cu[i])

            for child in self.children:
                child.decode_coding_quadtree()
        else:
            if self.parent is None:
                super(Ctu, self).decode()
            else:
                self.decode()

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
