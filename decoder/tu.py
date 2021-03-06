import numpy
import tree
import scan
import log
#import pdb

class Tu(tree.Tree):
    def __init__(self, x, y, log2size, depth=0, parent=None):
        tree.Tree.__init__(self, x, y, log2size, depth, parent)

    def parse(self):
        log.location.debug("Start decoding TU: (x, y) = (%d, %d), size = %d, depth = %d", self.x, self.y, self.size, self.depth)

        #if self.x==184 and self.y==48 and self.size==4 and self.depth==2:
        #    pdb.set_trace()

        if self.ctx.sps.max_transform_hierarchy_depth_inter == 0 and \
                self.cu.pred_mode == self.MODE_INTER and \
                self.cu.part_mode != InterPartMode.PART_2Nx2N and \
                self.depth == 0:
            self.inter_split_flag = 1
        else:
            self.inter_split_flag = 0

        if self.log2size <= self.ctx.sps.log2_max_transform_block_size and \
                self.log2size > self.ctx.sps.log2_min_transform_block_size and \
                self.depth < self.cu.max_transform_depth and \
                not (self.cu.intra_split_flag == 1 and self.depth == 0):
            self.split_transform_flag = self.parse__split_transform_flag()
        else:
            if self.log2size > self.ctx.sps.log2_max_transform_block_size or \
                    (self.cu.intra_split_flag == 1 and self.depth == 0) or \
                    self.inter_split_flag == 1:
                self.split_transform_flag = 1
            else:
                self.split_transform_flag = 0
        
        if self.log2size > 2:
            if self.depth == 0 or self.parent.cbf_cb == 1:
                self.cbf_cb = self.parse__cbf_cb()
            else:
                self.cbf_cb = 0

            if self.depth == 0 or self.parent.cbf_cr == 1:
                self.cbf_cr = self.parse__cbf_cr()
            else:
                self.cbf_cr = 0
        else:
            if self.depth > 0 and self.log2size == 2:
                self.cbf_cb = self.parent.cbf_cb
                self.cbf_cr = self.parent.cbf_cr
            else:
                self.cbf_cb = 0
                self.cbf_cr = 0


        if self.split_transform_flag:
            x0 = self.x
            y0 = self.y
            x1 = x0 + (1 << (self.log2size - 1))
            y1 = y0 + (1 << (self.log2size - 1))

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
                child.parse()
        else:
            if self.cu.pred_mode == self.cu.MODE_INTRA or self.depth != 0 or self.cbf_cb or self.cbf_cr:
                self.cbf_luma = self.parse__cbf_luma()
            self.parse_leaf()
    
    def parse_leaf(self):
        assert self.is_leaf() == True

        self.trans_coeff_level = [0] * 3
        self.trans_coeff_level[0] = numpy.zeros((self.size, self.size), int)
        self.trans_coeff_level[1] = numpy.zeros((self.size if self.log2size <= 2 else (self.size >> 1), self.size if self.log2size <= 2 else (self.size >> 1)), int)
        self.trans_coeff_level[2] = numpy.zeros((self.size if self.log2size <= 2 else (self.size >> 1), self.size if self.log2size <= 2 else (self.size >> 1)), int)

        if self.cbf_luma or self.cbf_cb or self.cbf_cr:
            if self.ctx.pps.cu_qp_delta_enabled_flag == 1 and self.cu.get_root().is_cu_qp_delta_coded == 0:
                self.cu_qp_delta_abs = self.parse__cu_qp_delta_abs()
                if self.cu_qp_delta_abs:
                    self.cu_qp_delta_sign_flag = self.parse__cu_qp_delta_sign_flag()
                else:
                    self.cu_qp_delta_sign_flag = 0
                self.cu.get_root().is_cu_qp_delta_coded = 1
                self.cu.get_root().cu_qp_delta_val = self.cu_qp_data_abs * (1 - 2 * self.cu_qp_delta_sign_flag)
                assert self.cu.get_root().cu_qp_delta_val >= -(26 + self.ctx.sps.qp_bd_offset_y/2) and self.cu.get_root().cu_qp_delta_val <= +(25 + self.ctx.sps.qp_bd_offset_y/2)
            
            self.transform_skip_flag = numpy.zeros(3, bool)
            self.last_sig_coeff_x_prefix = numpy.zeros(3, int)
            self.last_sig_coeff_y_prefix = numpy.zeros(3, int)
            self.last_sig_coeff_x_suffix = numpy.zeros(3, int)
            self.last_sig_coeff_y_suffix = numpy.zeros(3, int)
            self.last_significant_coeff_x = numpy.zeros(3, int)
            self.last_significant_coeff_y = numpy.zeros(3, int)

            self.coded_sub_block_flag = [0] * 3
            self.sig_coeff_flag = [0] * 3
            self.coeff_abs_level_greater1_flag = [0] * 3
            self.coeff_abs_level_greater2_flag = [0] * 3
            self.coeff_sign_flag = [0] * 3
            self.coeff_abs_level_remaining = [0] * 3

            if self.cbf_luma:
                self.parse_residual_coding(self.x, self.y, self.log2size, 0)
            
            if self.log2size > 2:
                # For luma TU with size larger than 4x4, two chroma half-size TUs are associated
                if self.cbf_cb:
                    self.parse_residual_coding(self.x, self.y, self.log2size-1, 1)
                if self.cbf_cr:
                    self.parse_residual_coding(self.x, self.y, self.log2size-1, 2)
            else:
                # This is the branch for luma TU size 4x4
                # Since chroma TU size 2x2 is not allowed, every 4 luma 4x4 TUs will share two 4x4 chroma TUs
                if self.idx == 3:
                    sisters  = self.get_sisters()
                    if sisters[0].cbf_cb:
                        self.parse_residual_coding(sisters[0].x, sisters[0].y, self.log2size, 1)
                    if sisters[0].cbf_cr:
                        self.parse_residual_coding(sisters[0].x, sisters[0].y, self.log2size, 2)

    def parse_residual_coding(self, x0, y0, log2size, c_idx):
        log.location.debug("Start decoding residual: c_idx = %d", c_idx)

        size = 1 << log2size

        if self.ctx.pps.transform_skip_enabled_flag and (not self.cu.cu_transquant_bypass_flag) and (log2size==2):
            self.transform_skip_flag[c_idx] = self.parse__transform_skip_flag(c_idx)

        self.last_sig_coeff_x_prefix[c_idx] = self.parse__last_sig_coeff_x_prefix(log2size, c_idx)
        self.last_sig_coeff_y_prefix[c_idx] = self.parse__last_sig_coeff_y_prefix(log2size, c_idx)
        assert self.last_sig_coeff_x_prefix[c_idx] in range(0, log2size<<1)
        assert self.last_sig_coeff_y_prefix[c_idx] in range(0, log2size<<1)
        
        if self.last_sig_coeff_x_prefix[c_idx] > 3:
            self.last_sig_coeff_x_suffix[c_idx] = self.parse__last_sig_coeff_x_suffix(c_idx)
            assert self.last_sig_coeff_x_suffix[c_idx] in range(0, 1<<((self.last_sig_coeff_x_prefix[c_idx]>>1)-1))
            self.last_significant_coeff_x[c_idx] = (1<<((self.last_sig_coeff_x_prefix[c_idx]>>1)-1)) * (2+(self.last_sig_coeff_x_prefix[c_idx]&1)) + self.last_sig_coeff_x_suffix[c_idx]
        else:
            self.last_significant_coeff_x[c_idx] = self.last_sig_coeff_x_prefix[c_idx]

        if self.last_sig_coeff_y_prefix[c_idx] > 3:
            self.last_sig_coeff_y_suffix[c_idx] = self.parse__last_sig_coeff_y_suffix(c_idx)
            assert self.last_sig_coeff_y_suffix[c_idx] in range(0, 1<<((self.last_sig_coeff_y_prefix[c_idx]>>1)-1))
            self.last_significant_coeff_y[c_idx] = (1<<((self.last_sig_coeff_y_prefix[c_idx]>>1)-1)) * (2+(self.last_sig_coeff_y_prefix[c_idx]&1)) + self.last_sig_coeff_y_suffix[c_idx]
        else:
            self.last_significant_coeff_y[c_idx] = self.last_sig_coeff_y_prefix[c_idx]
        
        if self.cu.pred_mode == self.cu.MODE_INTRA and (log2size == 2 or (log2size == 3 and c_idx == 0)):
            if c_idx == 0:
                pred_mode_intra = self.cu.get_intra_pred_mode_y(x0, y0) #[self.cu.y][self.cu.x]
            else:
                pred_mode_intra = self.cu.intra_pred_mode_c

            assert pred_mode_intra in range(0, 34 + 1)

            if pred_mode_intra in range(6, 14 + 1):
                scan_idx = 2
                scan_array = scan.get_vertical_scan_order_array
            elif pred_mode_intra in range(22, 30 + 1):
                scan_idx = 1
                scan_array = scan.get_horizontal_scan_order_array
            else:
                scan_idx = 0
                scan_array = scan.get_upright_diagonal_scan_order_array
        else:
            scan_idx = 0
            scan_array = scan.get_upright_diagonal_scan_order_array

        if scan_idx == 2:
            (self.last_significant_coeff_x[c_idx], self.last_significant_coeff_y[c_idx]) = (self.last_significant_coeff_y[c_idx], self.last_significant_coeff_x[c_idx])
        
        assert log2size >= 2
        size_subblock = 1 << (log2size - 2)
        size_4x4 = 1 << 2
        scan_order_subblock = scan_array(size_subblock)
        scan_order_4x4 = scan_array(size_4x4)

        # Determin the index of the last subblock which contains significant coefficient
        last_scan_pos = 16
        last_sub_block = size_subblock * size_subblock - 1
        while True:
            if last_scan_pos == 0:
                last_scan_pos = 16
                last_sub_block -= 1
            last_scan_pos -= 1
            xs = scan_order_subblock[last_sub_block][0]
            ys = scan_order_subblock[last_sub_block][1]
            xc = (xs << 2) + scan_order_4x4[last_scan_pos][0]
            yc = (ys << 2) + scan_order_4x4[last_scan_pos][1]
            if not ((xc != self.last_significant_coeff_x[c_idx]) or (yc != self.last_significant_coeff_y[c_idx])):
                break
        
        self.coded_sub_block_flag[c_idx] = numpy.zeros((size_subblock, size_subblock), bool)
        self.sig_coeff_flag[c_idx] = numpy.zeros((size_subblock, size_subblock, size, size), bool)
        self.coeff_abs_level_greater1_flag[c_idx] = numpy.zeros((size_subblock, size_subblock, size * size), bool)
        self.coeff_abs_level_greater2_flag[c_idx] = numpy.zeros((size_subblock, size_subblock, size * size), bool)
        self.coeff_sign_flag[c_idx] = numpy.zeros((size_subblock, size_subblock, size * size), bool)
        self.coeff_abs_level_remaining[c_idx] = numpy.zeros((size_subblock, size_subblock, size * size), int)
       
        greater1_context = {}

        greater1_context["greater1_ctx_of_last_invocation_in_a_previous_4x4_subblock"] = 0
        greater1_context["coeff_abs_level_greater1_flag_of_last_invocation_in_a_previous_4x4_subblock"] = 0

        greater1_context["greater1_ctx_of_previous_invocation_in_current_4x4_subblock"] = 0
        greater1_context["ctx_set_of_previous_invocation_in_current_4x4_subblock"] = 0
        greater1_context["coeff_abs_level_greater1_flag_of_previous_invocation_in_current_4x4_subblock"] = 0

        greater1_context["first_invocation_in_tu_flag"] = 1
        
        # Loop each 4x4 subblock reversely from the last subblock contain significant coefficients
        # 'i' is the index of the subblock in corresponding scan order determined by scan_idx
        for i in reversed(range(last_sub_block + 1)):

            # Coodinates of the subblock relative to the top-left point of the current TU
            xs = scan_order_subblock[i][0]
            ys = scan_order_subblock[i][1]
            
            # For the sub blocks between [1, last_sub_block-1] inclusive, there is a flag to indicate whether the coefficients in these subblocks are all zero.
            if i < last_sub_block and i > 0:
                self.coded_sub_block_flag[c_idx][xs][ys] = self.parse__coded_sub_block_flag(c_idx, xs, ys, log2size) 
                infer_sb_dc_sig_coeff_flag = 1
            else:
                # For the 1st subblock, it is very likely to contain significant coefficients 
                # For the last significant block, it will surely contain significant coefficients
                if (xs, ys) == (0, 0) or (xs, ys) == (self.last_significant_coeff_x[c_idx] >> 2, self.last_significant_coeff_y[c_idx] >> 2):
                    self.coded_sub_block_flag[c_idx][xs][ys] = 1
                else:
                    # For the subblocks after the last significant subblock, their coefficients are all zero
                    self.coded_sub_block_flag[c_idx][xs][ys] = 0
                infer_sb_dc_sig_coeff_flag = 0
            
            # Loop each node of subblock i, if it is the last significant block, loop starts from the last significant coefficient
            for n in reversed(range(((last_scan_pos - 1) if (i == last_sub_block) else 15) + 1)):
                xc = (xs << 2) + scan_order_4x4[n][0]
                yc = (ys << 2) + scan_order_4x4[n][1]
                if self.coded_sub_block_flag[c_idx][xs][ys] and (n > 0 or (not infer_sb_dc_sig_coeff_flag)):
                    self.sig_coeff_flag[c_idx][xs][ys][xc][yc] = self.parse__sig_coeff_flag(xc, yc, log2size, c_idx, scan_idx)
                    if self.sig_coeff_flag[c_idx][xs][ys][xc][yc]:
                        infer_sb_dc_sig_coeff_flag = 0
                else:
                    if i == last_sub_block and (xc, yc) == (self.last_significant_coeff_x[c_idx], last_significant_coeff_y[c_idx]):
                        self.sig_coeff_flag[c_idx][xs][ys][xc][yc] = 1
                    elif (xc & 3, yc & 3) == (0, 0) and infer_sb_dc_sig_coeff_flag == 1 and self.coded_sub_block_flag[c_idx][xs][ys] == 1:
                        self.sig_coeff_flag[c_idx][xs][ys][xc][yc] = 1
                    else:
                        self.sig_coeff_flag[c_idx][xs][ys][xc][yc] = 0
            
            #TODO: merge this loop with the previous one
            for n in reversed(range(last_scan_pos if (i == last_sub_block) else 16, 16)):
                xc = (xs << 2) + scan_order_4x4[n][0]
                yc = (ys << 2) + scan_order_4x4[n][1]
                if i == last_sub_block and (xc, yc) == (self.last_significant_coeff_x[c_idx], self.last_significant_coeff_y[c_idx]):
                    self.sig_coeff_flag[c_idx][xs][ys][xc][yc] = 1
                elif (xc & 3, yc & 3) == (0, 0) and infer_sb_dc_sig_coeff_flag == 1 and self.coded_sub_block_flag[c_idx][xs][ys] == 1:
                    self.sig_coeff_flag[c_idx][xs][ys][xc][yc] = 1
                else:
                    self.sig_coeff_flag[c_idx][xs][ys][xc][yc] = 0

            first_sig_scan_pos = 16 # Indicates the position which contains the first significant coefficient in the current 4x4 subblock
            last_sig_scan_pos = -1 # Indicates the position which contains the last significant coefficient in the current 4x4 subblock
            num_greater1_flag = 0 # Indicates how many greater than 1 coefficients existed in the current 4x4 subblock
            last_greater1_scan_pos = -1 # Indicates the position where it is the last coefficient that is greater than 1 in the current 4x4 subblock
            for n in reversed(range(15 + 1)):
                xc = (xs << 2) + scan_order_4x4[n][0]
                yc = (ys << 2) + scan_order_4x4[n][1]
                if self.sig_coeff_flag[c_idx][xs][ys][xc][yc]:
                    if num_greater1_flag < 8:
                        self.coeff_abs_level_greater1_flag[c_idx][xs][ys][n] = self.parse__coeff_abs_level_greater1_flag(c_idx, i, n, num_greater1_flag==0, greater1_context)
                        greater1_context["first_invocation_in_tu_flag"] = 0
                        num_greater1_flag += 1
                        if self.coeff_abs_level_greater1_flag[c_idx][xs][ys][n] and (last_greater1_scan_pos == -1):
                            last_greater1_scan_pos = n
                    else:
                        self.coeff_abs_level_greater1_flag[c_idx][xs][ys][n] = 0

                    if last_sig_scan_pos == -1:
                        last_sig_scan_pos = n
                    first_sig_scan_pos = n
                else:
                    self.coeff_abs_level_greater1_flag[c_idx][xs][ys][n] = 0

            greater1_context["greater1_ctx_of_last_invocation_in_a_previous_4x4_subblock"] = greater1_context["greater1_ctx_of_previous_invocation_in_current_4x4_subblock"]
            greater1_context["coeff_abs_level_greater1_flag_of_last_invocation_in_a_previous_4x4_subblock"] = greater1_context["coeff_abs_level_greater1_flag_of_previous_invocation_in_current_4x4_subblock"]

            sign_hidden = (last_sig_scan_pos - first_sig_scan_pos > 3) and (not self.cu.cu_transquant_bypass_flag)
            if last_greater1_scan_pos != -1:
                self.coeff_abs_level_greater2_flag[c_idx][xs][ys][last_greater1_scan_pos] = self.parse__coeff_abs_level_greater2_flag(c_idx, greater1_context)
            for n in range(16):
                if n != last_greater1_scan_pos:
                    self.coeff_abs_level_greater2_flag[c_idx][xs][ys][n] = 0
            
            for n in reversed(range(15 + 1)):
                xc = (xs << 2) + scan_order_4x4[n][0]
                yc = (ys << 2) + scan_order_4x4[n][1]
                if self.sig_coeff_flag[c_idx][xs][ys][xc][yc] and ((not self.ctx.pps.sign_data_hiding_enabled_flag) or (not sign_hidden) or (n != first_sig_scan_pos)):
                    self.coeff_sign_flag[c_idx][xs][ys][n] = self.parse__coeff_sign_flag()
                else:
                    self.coeff_sign_flag[c_idx][xs][ys][n] = 0

            num_sig_coeff = 0
            sum_abs_level = 0
            self.last_abs_level = 0
            self.last_rice_param = 0
            for n in reversed(range(15 + 1)):
                xc = (xs << 2) + scan_order_4x4[n][0]
                yc = (ys << 2) + scan_order_4x4[n][1]
                if self.sig_coeff_flag[c_idx][xs][ys][xc][yc]:
                    base_level = 1 + self.coeff_abs_level_greater1_flag[c_idx][xs][ys][n] + self.coeff_abs_level_greater2_flag[c_idx][xs][ys][n]
                    if base_level == ((3 if n == last_greater1_scan_pos else 2) if num_sig_coeff < 8 else 1):
                        self.coeff_abs_level_remaining[c_idx][xs][ys][n] = self.parse__coeff_abs_level_remaining(base_level)
                    else:
                        self.coeff_abs_level_remaining[c_idx][xs][ys][n] = 0

                    self.trans_coeff_level[c_idx][xc][yc] = (self.coeff_abs_level_remaining[c_idx][xs][ys][n] + base_level) * (1 - (2 * self.coeff_sign_flag[c_idx][xs][ys][n]))
                    if self.ctx.pps.sign_data_hiding_enabled_flag and sign_hidden:
                        sum_abs_level += self.coeff_abs_level_remaining[c_idx][xs][ys][n] + base_level
                        if n == first_sig_scan_pos and ((sum_abs_level % 2) == 1):
                            self.trans_coeff_level[c_idx][xc][yc]  = -self.trans_coeff_level[c_idx][xc][yc]

                    num_sig_coeff += 1
                else:
                    self.coeff_abs_level_remaining[c_idx][xs][ys][n] = 0
                    self.trans_coeff_level[c_idx][xc][yc] = 0

    def parse__split_transform_flag(self):
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
    
    def parse__cbf_chroma(self, component):
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

    def parse__cbf_cb(self):
        return self.parse__cbf_chroma("cb")

    def parse__cbf_cr(self):
        return self.parse__cbf_chroma("cr")

    def parse__cbf_luma(self):
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

    def parse__last_sig_coeff_x_suffix(self, c_idx):
        return self.parse__last_sig_coeff_xy_suffix("last_sig_coeff_x_suffix", self.last_sig_coeff_x_prefix[c_idx])

    def parse__last_sig_coeff_y_suffix(self, c_idx):
        return self.parse__last_sig_coeff_xy_suffix("last_sig_coeff_y_suffix", self.last_sig_coeff_y_prefix[c_idx])

    def parse__last_sig_coeff_xy_suffix(self, name, last_sig_coeff_xy_prefix):
        length = (last_sig_coeff_xy_prefix >> 1) - 1;
        value = self.ctx.cabac.decode_bypass()

        for i in range(1, length):
            value = (value << 1) | self.ctx.cabac.decode_bypass()

        log.syntax.info("%s = %d", name, value)
        return value;

    def parse__sig_coeff_flag(self, xc, yc, log2size, c_idx, scan_idx):
        if self.ctx.img.slice_hdr.init_type == 0:
            ctx_offset = 0
        elif self.ctx.img.slice_hdr.init_type == 1:
            ctx_offset = 42
        elif self.ctx.img.slice_hdr.init_type == 2:
            ctx_offset = 84
        else:
            raise ValueError("Unexpected init_type.")

        ctx_idx_map = [0, 1, 4, 5, 2, 3, 4, 5, 6, 6, 8, 8, 7, 7, 8]
        if log2size == 2:
            sig_ctx = ctx_idx_map[(yc << 2) + xc]
        elif (xc + yc) == 0:
            sig_ctx = 0
        else:
            (xs, ys) = (xc >> 2, yc >> 2)
            prev_csbf = 0
            if xs < ((1 << (log2size - 2)) - 1):
                prev_csbf += self.coded_sub_block_flag[c_idx][xs + 1][ys]
            if ys < ((1 << (log2size - 2)) - 1):
                prev_csbf += (self.coded_sub_block_flag[c_idx][xs][ys + 1] << 1)
            (xp, yp) = (xc & 3, yc & 3)

            if prev_csbf == 0:
                sig_ctx = 2 if ((xp + yp) == 0) else (1 if ((xp + yp) < 3) else 0)
            elif prev_csbf == 1:
                sig_ctx = 2 if (yp == 0) else (1 if yp == 1 else 0)
            elif prev_csbf == 2:
                sig_ctx = 2 if xp == 0 else (1 if xp == 1 else 0)
            else:
                sig_ctx = 2

            if c_idx == 0:
                if (xs + ys) > 0:
                    sig_ctx += 3
                if log2size == 3:
                    sig_ctx += (9 if scan_idx == 0 else 15)
                else:
                    sig_ctx += 21
            else:
                if log2size == 3:
                    sig_ctx += 9
                else:
                    sig_ctx += 12

        if c_idx == 0:
            ctx_inc = sig_ctx
        else:
            ctx_inc = 27 + sig_ctx
        
        bit = self.ctx.cabac.decode_decision("sig_coeff_flag", ctx_offset + ctx_inc)
        log.syntax.info("sig_coeff_flag = %d", bit)
        return bit

    
    def parse__coded_sub_block_flag(self, c_idx, xs, ys, log2size):
        if self.ctx.img.slice_hdr.init_type == 0:
            ctx_offset = 0
        elif self.ctx.img.slice_hdr.init_type == 1:
            ctx_offset = 4
        elif self.ctx.img.slice_hdr.init_type == 2:
            ctx_offset = 8
        else:
            raise ValueError("Unexpected init_type.")

        #TODO: check the csbf_ctx calculation process with SPEC
        csbf_ctx = 0
        if xs < ((1 << (log2size - 2)) - 1):
            csbf_ctx += self.coded_sub_block_flag[c_idx][xs + 1][ys]
        if ys < ((1 << (log2size - 2)) - 1):
            csbf_ctx += self.coded_sub_block_flag[c_idx][xs][ys + 1]

        if c_idx == 0:
            ctx_inc = min(csbf_ctx, 1)
        else:
            ctx_inc = 2 + min(csbf_ctx, 1)

        ctx_idx = ctx_offset + ctx_inc
        bit = self.ctx.cabac.decode_decision("coded_sub_block_flag", ctx_idx)
        log.syntax.info("coded_sub_block_flag = %d", bit)
        return bit

    def parse__coeff_abs_level_remaining(self, base_level):
        rice_param = min(self.last_rice_param + (1 if self.last_abs_level > (3 * (1 << self.last_rice_param)) else 0), 4)

        prefix = 0
        suffix = 0

        while self.ctx.cabac.decode_bypass():
            prefix += 1
        assert prefix < 31

        if prefix < 3:
            for i in range(rice_param):
                suffix = (suffix << 1) | self.ctx.cabac.decode_bypass() 
            value = (prefix << rice_param) + suffix
        else:
            prefix_minus3 = prefix - 3
            for i in range(prefix_minus3 + rice_param):
                suffix = (suffix << 1) | self.ctx.cabac.decode_bypass()
            value = (((1 << prefix_minus3) + 3 - 1) << rice_param) + suffix
        

        self.last_rice_param = rice_param
        self.last_abs_level = base_level + value

        log.syntax.info("coeff_abs_level_remaining = %d", value)
        return value;

    def parse__coeff_sign_flag(self):
        bit = self.ctx.cabac.decode_bypass()
        log.syntax.info("coeff_sign_flag = %d", bit)
        return bit

    def parse__coeff_abs_level_greater1_flag(self, c_idx, i, n, first_invocation_in_4x4_subblock_flag, greater1_context):
        if self.ctx.img.slice_hdr.init_type == 0:
            ctx_offset = 0
        elif self.ctx.img.slice_hdr.init_type == 1:
            ctx_offset = 24
        elif self.ctx.img.slice_hdr.init_type == 2:
            ctx_offset = 48
        else:
            raise ValueError("Unexpected init_type.")
        
        if first_invocation_in_4x4_subblock_flag == 1:
            if i == 0 or c_idx > 0:
                ctx_set = 0
            else:
                ctx_set = 2

            if greater1_context["first_invocation_in_tu_flag"] == 1:
                last_greater1_ctx = 1
            else:
                last_greater1_ctx = greater1_context["greater1_ctx_of_last_invocation_in_a_previous_4x4_subblock"]
                if last_greater1_ctx > 0:
                    last_greater1_flag = greater1_context["coeff_abs_level_greater1_flag_of_last_invocation_in_a_previous_4x4_subblock"]
                    if last_greater1_flag == 1:
                        last_greater1_ctx = 0
                    else:
                        last_greater1_ctx += 1

            if last_greater1_ctx == 0:
                ctx_set = ctx_set + 1
            
            greater1_ctx = 1
        else:
            ctx_set = greater1_context["ctx_set_of_previous_invocation_in_current_4x4_subblock"]

            greater1_ctx = greater1_context["greater1_ctx_of_previous_invocation_in_current_4x4_subblock"]
            if greater1_ctx > 0:
                last_greater1_flag = greater1_context["coeff_abs_level_greater1_flag_of_previous_invocation_in_current_4x4_subblock"]
                if last_greater1_flag == 1:
                    greater1_ctx = 0
                else:
                    greater1_ctx += 1

        ctx_inc = ctx_set * 4 + min(3, greater1_ctx)
        if c_idx > 0:
            ctx_inc += 16
        
        ctx_idx = ctx_offset + ctx_inc
        
        bit = self.ctx.cabac.decode_decision("coeff_abs_level_greater1_flag", ctx_idx)

        greater1_context["coeff_abs_level_greater1_flag_of_previous_invocation_in_current_4x4_subblock"] = bit
        greater1_context["greater1_ctx_of_previous_invocation_in_current_4x4_subblock"] = greater1_ctx
        greater1_context["ctx_set_of_previous_invocation_in_current_4x4_subblock"] = ctx_set

        log.syntax.info("coeff_abs_level_greater1_flag = %d", bit)
        return bit

    def parse__coeff_abs_level_greater2_flag(self, c_idx, greater1_context):
        ctx_set = greater1_context["ctx_set_of_previous_invocation_in_current_4x4_subblock"]
        ctx_inc = ctx_set

        if c_idx > 0:
            ctx_inc += 4

        if self.ctx.img.slice_hdr.init_type == 0:
            ctx_offset = 0
        elif self.ctx.img.slice_hdr.init_type == 1:
            ctx_offset = 6
        elif self.ctx.img.slice_hdr.init_type == 2:
            ctx_offset = 12
        else:
            raise ValueError("Unexpected init_type.")
        
        ctx_idx = ctx_offset + ctx_inc

        bit = self.ctx.cabac.decode_decision("coeff_abs_level_greater2_flag", ctx_idx)

        log.syntax.info("coeff_abs_level_greater2_flag = %d", bit)
        return bit

    def parse__transform_skip_flag(self, c_idx):
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
        log.syntax.info("transform_skip_flag = %d", bit)
        return bit

    def parse__last_sig_coeff_xy_prefix(self, log2size, c_idx, xy):
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
     
    def parse__last_sig_coeff_x_prefix(self, log2size, c_idx):
        return self.parse__last_sig_coeff_xy_prefix(log2size, c_idx, 'x')

    def parse__last_sig_coeff_y_prefix(self, log2size, c_idx):
        return self.parse__last_sig_coeff_xy_prefix(log2size, c_idx, 'y')

    def get_trans_coeff_level(self, x, y, c_idx):
        assert self.is_root()
        assert self.contain(x, y)
        for leave in self.get_leaves():
            if leave.contain(x, y):
                #print "size = %d, x = %d, y = %d, leave.x = %d, leave.y = %d, c_idx = %d" % (leave.size, x, y, leave.x, leave.y, c_idx)
                if c_idx == 0:
                    return leave.trans_coeff_level[c_idx][x - leave.x][y - leave.y]
                else: 
                    if self.log2size > 2:
                        return leave.trans_coeff_level[c_idx][x - leave.x][y - leave.y]
                    else:
                        raise "Attention!"
                        if leave.idx == 3:
                            return leave.trans_coeff_level[c_idx][x - leave.x][y - leave.y]
                        else:
                            return leave.get_sisters()[3].trans_coeff_level[c_idx][x - leave.x][y - leave.y]
        return None

    def get_trans_coeff_level_y(self, x, y):
        self.get_trans_coeff_level(x, y, 0)

    def get_trans_coeff_level_cb(self, x, y):
        self.get_trans_coeff_level(x, y, 1)

    def get_trans_coeff_level_cr(self, x, y):
        self.get_trans_coeff_level(x, y, 2)

    def get_split_transform_flag(self, x, y, depth):
        assert self.is_root()
        assert self.contain(x, y)
        for i in self.traverse(strategy = "breath-first"):
            if i.contain(x, y) and i.depth == depth:
                return i.split_transform_flag
        raise ValueError("Error: can't find the split_transform_flag in the specified pixel coordinates and depth.")
