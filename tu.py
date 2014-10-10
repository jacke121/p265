import tree
import scan
import log

class Tu(tree.Tree):
    def __init__(self, x, y, log2size, depth=0, parent=None):
        tree.Tree.__init__(self, x, y, log2size, depth, parent)

    def decode(self):
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
                sub_tu[i].ctx = self.ctx
                sub_tu[i].cu = self.cu

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
                raise "I am here!"
                sisters  = self.get_sisters()
                if sisters[0].cbf_cb:
                    self.decode_residual_coding(sister[0].x, sister[0].y, self.log2size, 1)
                if sisters[0].cbf_cr:
                    self.decode_redidual_coding(sister[0].x, sister[0].y, self.log2size, 2)
    
    def decode_residual_coding(self, x0, y0, log2size, c_idx):
        if self.ctx.pps.transform_skip_enabled_flag and (not self.cu.cu_transquant_bypass_flag) and (log2size==2):
            self.transform_skip_flag = self.decode_transform_skip_flag(c_idx)

        self.last_sig_coeff_x_prefix = self.decode_last_sig_coeff_x_prefix(log2size, c_idx)
        self.last_sig_coeff_y_prefix = self.decode_last_sig_coeff_y_prefix(log2size, c_idx)
        assert self.last_sig_coeff_x_prefix in range(0, log2size<<1)
        assert self.last_sig_coeff_y_prefix in range(0, log2size<<1)
        
        if self.last_sig_coeff_x_prefix > 3:
            self.last_sig_coeff_x_suffix = self.decode_last_sig_coeff_x_suffix()
            assert self.last_sig_coeff_x_suffix in range(0, 1<<((self.last_sig_coeff_x_prefix>>1)-1))
            last_significant_coeff_x = (1<<((self.last_sig_coeff_x_prefix>>1)-1)) * (2+(self.last_sig_coeff_x_prefix&1)) + last_sig_coeff_x_suffix
        else:
            last_significant_coeff_x = self.last_sig_coeff_x_prefix

        if self.last_sig_coeff_y_prefix > 3:
            self.last_sig_coeff_y_suffix = self.decode_last_sig_coeff_y_suffix()
            assert self.last_sig_coeff_y_suffix in range(0, 1<<((self.last_sig_coeff_y_prefix>>1)-1))
            last_significant_coeff_y = (1<<((self.last_sig_coeff_y_prefix>>1)-1)) * (2+(self.last_sig_coeff_y_prefix&1)) + last_sig_coeff_y_suffix
        else:
            last_significant_coeff_y = self.last_sig_coeff_y_prefix
        
        log.main.info("log2size = %d", log2size)

        if self.cu.pred_mode == self.cu.MODE_INTRA and (log2size == 2 or (log2size == 3 and c_idx == 0)):
            pred_mode_intra = self.cu.intra_pred_mode_y
        else:
            pred_mode_intra = self.cu.intra_pred_mode_c

        if pred_mode_intra in range(6, 14 + 1):
            scan_idx = 2
            scan_array = scan.get_vertical_scan_order_array
            (last_significant_coeff_x, last_significant_coeff_y) = (last_significant_coeff_y, last_significant_coeff_x)
        elif pred_mode_intra in range(22, 30 + 1):
            scan_idx = 1
            scan_array = scan.get_horizontal_scan_order_array
        else:
            scan_idx = 0
            scan_array = scan.get_upright_diagnoal_scan_order_array
        
        scan_order_subblock = scan_array(log2size - 2)
        scan_order_4x4 = scan_array(2)

        last_scan_pos = 16
        last_sub_block = (1 << (log2size - 2)) * (1 << (log2size - 2)) - 1
        while True:
            if last_scan_pos == 0:
                last_scan_pos = 16
                last_sub_block -= 1
            last_scan_pos -= 1
            xs = scan_order_subblock[last_sub_block][0]
            ys = scan_order_subblock[last_sub_block][1]
            xc = (xs << 2) + scan_order_4x4[last_scan_pos][0]
            yc = (ys << 2) + scan_order_4x4[last_scan_pos][1]
            if not ((xc != last_significant_coeff_x) or (yc != last_significant_coeff_y)):
                break

        for i in reversed(range(last_sub_block + 1)):
            xs = scan_order_subblock[i][0]
            ys = scan_order_subblock[i][1]
            infer_sb_dc_sig_coeff_flag = 0
            if i < last_sub_block and i > 0:
                self.decode_coded_sub_block_flag(xs, ys)
                infer_sb_dc_sig_coeff_flag = 1

            for n in reversed(range(((last_scan_pos - 1) if (i == last_sub_block) else 15) + 1)):
                xc = (xs << 2) + scan_order_4x4[n][0]
                yc = (ys << 2) + scan_order_4x4[n][1]
                if self.coded_sub_block_flag and (n > 0 or (not infer_sb_dc_sig_coeff_flag)):
                    self.sig_coeff_flag = self.decode_sig_coeff_flag(xc, yc)
                    if self.sig_coeff_flag:
                        infer_sb_dc_sig_coeff_flag = 0

            first_sig_scan_pos = 16
            last_sig_scan_pos = -1
            num_greater1_flag = 0
            last_greater1_scan_pos = -1
            for n in reversed(range(15 + 1)):
                xc = (xs << 2) + scan_order_4x4[n][0]
                yc = (ys << 2) + scan_order_4x4[n][1]
                if self.sig_coeff_flag:
                    if num_greater1_flag < 8:
                        self.coeff_abs_level_greater1_flag = self.decode_coeff_abs_level_greater1_flag()
                        num_greater1_flag += 1
                        if self.coeff_abs_level_greater1_flag and (last_greater1_scan_pos == -1):
                            last_greater1_scan_pos = n
                    if last_sig_scan_pos == -1:
                        last_sig_scan_pos = n
                    first_sig_scan_pos = n
            sign_hidden = (last_sig_scan_pos - first_sig_scan_pos > 3) and (not self.cu.cu_transquant_bypass_flag)
            if last_greater1_scan_pos != -1:
                self.coeff_abs_level_greater2_flag = self.decode_coeff_abs_level_greater2_flag()
            
            for n in reversed(range(15 + 1)):
                xc = (xs << 2) + scan_order_4x4[n][0]
                yc = (ys << 2) + scan_order_4x4[n][1]
                if self.sig_coeff_flag and ((not self.sign_data_hiding_enabled_flag) or (not sign_hidden) or (n != first_sig_scan_pos)):
                    self.coeff_sign_flag = self.decode_coeff_sign_flag()

            num_sig_coeff = 0
            sum_abs_level = 0
            for n in reversed(range(15 + 1)):
                xc = (xs << 2) + scan_order_4x4[n][0]
                yc = (ys << 2) + scan_order_4x4[n][1]
                if self.sig_coeff_flag:
                    base_level = 1 + self.coeff_abs_level_greater1_flag + self.coeff_abs_level_greater2_flag
                    if base_level == ((3 if n == last_greater1_scan_pos else 2) if num_sig_coeff < 8 else 1):
                        self.coeff_abs_remaining = self.decode_coeff_abs_remaining()
                    self.trans_coeff_level[xc][yc] = (self.coeff_abs_level_remaining + base_level) * (1 - (2 * self.coeff_sign_flag))
                    if self.sign_data_hiding_enabled_flag and sign_hidden:
                        sum_abs_level += self.coeff_abs_level_remaining + base_level
                        if n == first_sig_scan_pos and ((sum_abs_level % 2) == 1):
                            self.trans_coeff_level[xc][yc]  = -self.trans_coeff_level[xc][yc]
                    num_sig_coeff += 1

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
