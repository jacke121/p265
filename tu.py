import tree

class Tu(tree.Tree):
    def __init__(self, x, y, log2size, depth=0, parent=None):
        tree.Tree.__init__(self, x, y, log2size, depth, parent)

    def decode(self, ctx, cu):
        self.ctx = ctx
        self.cu = cu
        if self.log2size <= self.ctx.sps.log2_max_transform_block_size and \
                self.log2size > self.ctx.sps.log2_min_transform_block_size and \
                self.depth < self.cu.max_transform_depth and \
                not (self.cu.intra_split_flag == 1 and self.depth == 0)
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

    def decode_leaf(self):
        if self.cbf_luma or self.cbf_cb or self.cbf_cr:
            if self.ctx.pps.cu_qp_delta_enabled_flag and not self.cu.is_cu_qp_delta_coded:
                self.cu_qp_delta_abs = self.decode_cu_qp_delta_abs()
                if self.cu_qp_delta_abs:
                    self.cu_qp_delta_sign_flag = self.decode_cu_qp_delta_sign_flag()
            if self.cbf_luma:
                self.decode_residual_coding()
            
            #TODO
            '''
            if self.log2size > 2:
                if self.cbf_cb:
                    self.decode_redidual_coding()
                if self.cbf_cr:
                    self.decode_redidual_coding()
            elif self.idx == 3:
            '''

