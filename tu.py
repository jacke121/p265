import tree
import log

class Tu(tree.Tree):
    def __init__(self, x, y, log2size, depth=0, parent=None):
        tree.Tree.__init__(self, x, y, log2size, depth, parent)

    def decode(self, ctx, cu):
        self.ctx = ctx
        self.cu = cu
        if self.log2size <= self.ctx.sps.log2_max_transform_block_size and \
                self.log2size > self.ctx.sps.log2_min_transform_block_size and \
                self.depth < self.cu.max_transform_depth and \
                not (self.cu.intra_split_flag == 1 and self.depth == 0):
            self.split_transform_flag = self.decode_split_transform_flag()
        
        if self.log2size > 2:
            if self.depth == 0 or self.parent.cbf_cb == 1:
                self.cbf_cb = self.decode_cbf_cb()
            if self.depth == 0 or self.parent.cbf_cr == 1:
                self.cbf_cr = self.decode_cbf_cr()

        if self.split_transform_flag:
            x0 = self.x
            y0 = self.y
            x1 = x0 + (1 << self.log2size)
            y1 = y0 + (1 << self.log2size)

            sub_tu = [None] * 4
            sub_tu[0] = Tu(x0, y0, self.log2size-1, self.depth+1, self)
            sub_tu[1] = Tu(x1, y0, self.log2size-1, self.depth+1, self)
            sub_tu[2] = Tu(x0, y1, self.log2size-1, self.depth+1, self)
            sub_tu[3] = Tu(x1, y1, self.log2size-1, self.depth+1, self)

            for i in range(4):
                sub_tu[i].idx = i

            for i in sub_tu:
                self.add_child(i)

            for child in self.children:
                child.decode()
        else:
            if self.cu.pred_mode == self.cu.MODE_INTRA or self.depth != 0 or self.cbf_cb or self.cbf_cr:
                self.cbf_luma = self.decode_cbf_luma()
            self.decode_leaf()
    
    def decode_split_transform_flag(self):
        if self.ctx.img.slice_hdr.init_type == 0:
            ctx_offset = 0
        elif self.ctx.img.slice_hdr.init_type == 1:
            ctx_offset = 3
        elif self.ctx.img.slice_hdr.init_type == 2:
            ctx_offset = 6
        else:
            raise ValueError("Unexpected init_type.")
        
        ctx_inc = 5 - self.log2size
        ctx_idx = ctx_offset + ctx_inc
        bit = self.ctx.cabac.decode_decision("split_transform_flag", ctx_idx)
        log.syntax.info("split_transform_flag = %d", bit)
        return bit
    
    def decode_cbf_chroma(self, component):
        ctx_inc = self.depth
        if self.ctx.img.slice_hdr.init_type == 0:
            ctx_offset = 0
        elif self.ctx.img.slice_hdr.init_type == 1:
            ctx_offset = 4
        elif self.ctx.img.slice_hdr.init_type == 2:
            ctx_offset = 8
        else:
            raise ValueError("Unexpected init_type.")

        ctx_idx = ctx_offset + ctx_inc
        bit = self.ctx.cabac.decode_decision("cbf_chroma", ctx_idx)
        log.syntax.info("cbf_%s = %d", component, bit)
        return bit

    def decode_cbf_cb(self):
        return self.decode_cbf_chroma("cb")

    def decode_cbf_cr(self):
        return self.decode_cbf_chroma("cr")

    def decode_cbf_luma(self):
        ctx_inc = 1 if self.depth==0 else 0
        if self.ctx.img.slice_hdr.init_type == 0:
            ctx_offset = 0
        elif self.ctx.img.slice_hdr.init_type == 1:
            ctx_offset = 2
        elif self.ctx.img.slice_hdr.init_type == 2:
            ctx_offset = 4
        else:
            raise ValueError("Unexpected init_type.")

        ctx_idx = ctx_offset + ctx_inc
        bit = self.ctx.cabac.decode_decision("cbf_luma", ctx_idx)
        log.syntax.info("cbf_luma = %d", bit)
        return bit

    def decode_leaf(self):
        assert self.is_leaf() == True
        if self.cbf_luma or self.cbf_cb or self.cbf_cr:
            if self.ctx.pps.cu_qp_delta_enabled_flag and not self.cu.is_cu_qp_delta_coded:
                self.cu_qp_delta_abs = self.decode_cu_qp_delta_abs()
                if self.cu_qp_delta_abs:
                    self.cu_qp_delta_sign_flag = self.decode_cu_qp_delta_sign_flag()

            if self.cbf_luma:
                self.decode_residual_coding(self.x, self.y, self.log2size, 0)
            
            if self.log2size > 2:
                if self.cbf_cb:
                    self.decode_residual_coding(self.x, self.y, self.log2size-1, 1)
                if self.cbf_cr:
                    self.decode_residual_coding(self.x, self.y, self.log2size-1, 2)
            elif self.idx == 3:
                sisters  = self.get_sisters()
                if sisters[0].cbf_cb:
                    self.decode_residual_coding(sister[0].x, sister[0].y, self.log2size, 1)
                if sisters[0].cbf_cr:
                    self.decode_redidual_coding(sister[0].x, sister[0].y, self.log2size, 2)
    
    def decode_residual_coding(self, x0, y0, log2size, c_idx):
        if self.ctx.pps.transform_skip_enabled_flag and (not self.cu.cu_transquant_bypass_flag) and (log2size==2):
            self.transform_skip_flag[c_idx] = self.decode_transform_skip_flag(c_idx)

        self.last_sig_coeff_x_prefix = self.decode_last_sig_coeff_x_prefix(log2size, c_idx)
        self.last_sig_coeff_y_prefix = self.decode_last_sig_coeff_y_prefix(log2size, c_idx)

        raise "over"

    def decode_transform_skip_flag(c_idx):
        ctx_inc = 0

        if c_idx == 0:
            if self.ctx.img.slice_hdr.init_type == 0:
                ctx_offset = 0
            elif self.ctx.img.slice_hdr.init_type == 1:
                ctx_offset = 1
            elif self.ctx.img.slice_hdr.init_type == 2:
                ctx_offset = 2
            else:
                raise ValueError("Unexpected init_type.")
        else:# c_idx == 1 or c_idx == 2:
            if self.ctx.img.slice_hdr.init_type == 0:
                ctx_offset = 3
            elif self.ctx.img.slice_hdr.init_type == 1:
                ctx_offset = 4
            elif self.ctx.img.slice_hdr.init_type == 2:
                ctx_offset = 5
            else:
                raise ValueError("Unexpected init_type.")

        ctx_idx = ctx_offset + ctx_inc

        bit = self.ctx.cabac.decode_decision("transform_skip_flag", ctx_idx)
        log.syntax.info("transform_skip = %d", bit)
        return bit

    def decode_last_sig_coeff_xy_prefix(self, log2size, c_idx, xy):
        if self.ctx.img.slice_hdr.init_type == 0:
            ctx_offset = 0
        elif self.ctx.img.slice_hdr.init_type == 1:
            ctx_offset = 18
        elif self.ctx.img.slice_hdr.init_type == 2:
            ctx_offset = 36
        else:
            raise ValueError("Unexpected init_type.")

        if c_idx == 0:
            offset = 3 * (log2size -2) + ((log2size - 1) >> 2)
            shift = (log2size + 1) >> 2
        else:
            offset = 15
            shift = log2size - 2
        
        i = 0
        ctx_table = "last_sig_coeff_%s_prefix" % xy
        while i < ((log2size << 1) - 1) and self.ctx.cabac.decode_decision(ctx_table, ctx_offset + ((i >> shift) + offset)):
            i += 1

        value = i 
        log.syntax.info("last_sig_coeff_%s_prefix = %d", xy, value)
        return value
     
    def decode_last_sig_coeff_x_prefix(self, log2size, c_idx):
        return self.decode_last_sig_coeff_xy_prefix(log2size, c_idx, 'x')

    def decode_last_sig_coeff_y_prefix(self, log2size, c_idx):
        return self.decode_last_sig_coeff_xy_prefix(log2size, c_idx, 'y')
