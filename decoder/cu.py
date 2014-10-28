import sys
import random
import math
import numpy
import tree
import tu
import utils
import intra
import log

class IntraPartMode:
    PART_2Nx2N = 0
    PART_NxN = 1

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

    def is_intra_mode(self):
        assert self.is_leaf() == True
        return self.pred_mode == self.MODE_INTRA

    def is_inter_mode(self):
        assert self.is_leaf() == True
        return self.pred_mode == self.MODE_INTER

    def parse_leaf(self):
        assert self.is_leaf() == True

        if self.ctx.pps.transquant_bypass_enabled_flag:
            self.cu_transquant_bypass_flag = self.decode_cu_transquant_bypass_flag()
        else:
            self.cu_transquant_bypass_flag = 0

        if not self.ctx.img.slice_hdr.is_I_slice():
            self.cu_skip_flag = self.decode_cu_skip_flag()
        else:
            self.cu_skip_flag = 0

        if self.cu_skip_flag:
            self.decode_prediction_unit()
            self.pred_mode = self.MODE_SKIP
        else:
            if self.ctx.img.slice_hdr.is_I_slice():
                # I slice only use intra prediction
                self.pred_mode = self.MODE_INTRA
            else:
                # P/B slice has one bit in bitstream as "pred_mode_flag" to indicate whether the current CU is intra or inter predicted
                self.pred_mode_flag = self.decode_pred_mode_flag()
                if self.pred_mode_flag == 0:
                    self.pred_mode = self.MODE_INTER
                else:
                    self.pred_mode = self.MODE_INTRA

            if self.pred_mode != self.MODE_INTRA or self.log2size == self.ctx.sps.min_cb_log2_size_y:
                self.part_mode = self.decode_part_mode()
                if self.pred_mode == self.MODE_INTRA:
                    if self.part_mode == IntraPartMode.PART_2Nx2N:
                        self.intra_split_flag = 0
                    else:
                        self.intra_split_flag = 1
            else:
                self.part_mode = 0
                self.intra_split_flag = 0

            if self.pred_mode == self.MODE_INTRA:
                if self.part_mode == IntraPartMode.PART_2Nx2N and \
                        self.ctx.sps.pcm_enabled_flag == 1 and \
                        self.log2size >= self.ctx.sps.log2_min_pcm_luma_coding_block_size and \
                        self.log2size <= self.ctx.sps.log2_max_pcm_luma_coding_block_size:
                    self.pcm_flag = self.decode_pcm_flag()
                else:
                    self.pcm_flag = 0

                if self.pcm_flag == 1:
                     while not self.ctx.bs.byte_aligned():
                         self.pcm_alignment_zero_bit = self.ctx.bs.f(1, "pcm_alignment_zero_bit")
                         assert self.pcm_alignment_zero_bit == 0
                     self.decode_pcm_sample()
                else:
                    self.decode_intra_pred_mode()
            else:
                self.decode_inter_pred_info()

            if self.pcm_flag == 0:
                if self.pred_mode != self.MODE_INTRA and (not (self.part_mode == InterPartMode.PART_2Nx2N and self.merge_flag == 1)):
                    self.rqt_root_cbf = self.decode_rqt_root_cbf()
                else:
                    self.rqt_root_cbf = 1

                if self.rqt_root_cbf:
                    if self.pred_mode == self.MODE_INTRA:
                        self.max_transform_depth = self.ctx.sps.max_transform_hierarchy_depth_intra + self.intra_split_flag
                    else:
                        self.max_transform_depth = self.ctx.sps.max_transform_hierarchy_depth_inter

                    self.tu = tu.Tu(self.x, self.y, self.log2size, depth=0, parent=None)
                    self.tu.idx = 0
                    self.tu.ctx = self.ctx
                    self.tu.cu = self
                    self.tu.decode()

    def decode_intra_pred_mode(self):
        if self.part_mode == IntraPartMode.PART_NxN:
            pb_offset = self.size/2
        else:
            pb_offset = self.size

        self.intra_pb_size = pb_offset

        #TODO: find a more efficient way to store these four syntax elements
        self.prev_intra_luma_pred_flag = utils.md_dict()
        self.mpm_idx = utils.md_dict()
        self.rem_intra_luma_pred_mode = utils.md_dict()
        self.intra_pred_mode_y = utils.md_dict()

        for j in range(0, self.size, pb_offset):
            for i in range(0, self.size, pb_offset):
                self.prev_intra_luma_pred_flag[self.x + i][self.y + j] = self.decode_prev_intra_luma_pred_flag(self.y + j, self.x + i)

        for j in range(0, self.size, pb_offset):
            for i in range(0, self.size, pb_offset):
                if self.prev_intra_luma_pred_flag[self.x + i][self.y + j]:
                    self.mpm_idx[self.x + i][self.y + j] = self.decode_mpm_idx()
                else:
                    self.rem_intra_luma_pred_mode[self.x + i][self.y + j] = self.decode_rem_intra_luma_pred_mode()
        
        for j in range(0, self.size, pb_offset):
            for i in range(0, self.size, pb_offset):
                x_pb = self.x + i
                y_pb = self.y + j

                x_neighbor_a = x_pb -1
                y_neighbor_a = y_pb
                x_neighbor_b = x_pb
                y_neighbor_b = y_pb - 1

                available_a = self.ctx.img.check_availability(x_pb, y_pb, x_neighbor_a, y_neighbor_a)
                available_b = self.ctx.img.check_availability(x_pb, y_pb, x_neighbor_b, y_neighbor_b)

                ctu_a = self.ctx.img.get_ctu(x_neighbor_a, y_neighbor_a) if available_a else None
                ctu_b = self.ctx.img.get_ctu(x_neighbor_b, y_neighbor_b) if available_b else None
                
                if available_a == False:
                    cand_intra_pred_mode_a = 1
                elif ctu_a.get_pred_mode(x_neighbor_a, y_neighbor_a) != self.MODE_INTRA or ctu_a.get_pcm_flag(x_neighbor_a, y_neighbor_a) == 1:
                    cand_intra_pred_mode_a = 1
                else:
                    cand_intra_pred_mode_a = ctu_a.get_intra_pred_mode_y(x_neighbor_a, y_neighbor_a)

                if available_b == False:
                    cand_intra_pred_mode_b = 1
                elif ctu_b.get_pred_mode(x_neighbor_b, y_neighbor_b) != self.MODE_INTRA or ctu_b.get_pcm_flag(x_neighbor_b, y_neighbor_b) == 1:
                    cand_intra_pred_mode_b = 1
                elif (y_pb - 1) < ((y_pb >> self.ctx.sps.ctb_log2_size_y) << self.ctx.sps.ctb_log2_size_y):
                    cand_intra_pred_mode_b = 1
                else:
                    cand_intra_pred_mode_b = ctu_b.get_intra_pred_mode_y(x_neighbor_b, y_neighbor_b)
                
                cand_mode_list = [0] * 3
                if cand_intra_pred_mode_a == cand_intra_pred_mode_b:
                    if cand_intra_pred_mode_a < 2:
                        cand_mode_list = [0, 1, 26]
                    else:
                        cand_mode_list[0] = cand_intra_pred_mode_a
                        cand_mode_list[1] = 2 + ((cand_intra_pred_mode_a + 29) % 32)
                        cand_mode_list[2] = 2 + ((cand_intra_pred_mode_a -2 + 1) % 32)
                else:
                    cand_mode_list[0] = cand_intra_pred_mode_a
                    cand_mode_list[1] = cand_intra_pred_mode_b
                    if not (cand_mode_list[0] == 0 or cand_mode_list[1] == 0):
                        cand_mode_list[2] = 0
                    elif not (cand_mode_list[0] == 1 or cand_mode_list[1] == 1):
                        cand_mode_list[2] = 1
                    else:
                        cand_mode_list[2] = 26

                if self.prev_intra_luma_pred_flag[x_pb][y_pb] == 1:
                    self.intra_pred_mode_y[x_pb][y_pb] = cand_mode_list[self.mpm_idx[x_pb][y_pb]]
                else:
                    if cand_mode_list[0] > cand_mode_list[1]:
                        (cand_mode_list[0], cand_mode_list[1]) = (cand_mode_list[1], cand_mode_list[0])
                    if cand_mode_list[0] > cand_mode_list[2]:
                        (cand_mode_list[0], cand_mode_list[2]) = (cand_mode_list[2], cand_mode_list[0])
                    if cand_mode_list[1] > cand_mode_list[2]:
                        (cand_mode_list[1], cand_mode_list[2]) = (cand_mode_list[2], cand_mode_list[1])
                    
                    self.intra_pred_mode_y[x_pb][y_pb] = self.rem_intra_luma_pred_mode[x_pb][y_pb]
                    for i in range(3):
                        if self.intra_pred_mode_y[x_pb][y_pb] >= cand_mode_list[i]:
                            self.intra_pred_mode_y[x_pb][y_pb] += 1
        
                assert self.intra_pred_mode_y[x_pb][y_pb] in range(0, 34 + 1)
        
        self.intra_chroma_pred_mode = self.decode_intra_chroma_pred_mode()
        if self.intra_chroma_pred_mode == 0:
            self.intra_pred_mode_c = (34 if self.intra_pred_mode_y[self.x][self.y] == 0 else 0)
        elif self.intra_chroma_pred_mode == 1:
            self.intra_pred_mode_c = (34 if self.intra_pred_mode_y[self.x][self.y] == 26 else 26)
        elif self.intra_chroma_pred_mode == 2:
            self.intra_pred_mode_c = (34 if self.intra_pred_mode_y[self.x][self.y] == 10 else 10)
        elif self.intra_chroma_pred_mode == 3:
            self.intra_pred_mode_c = (34 if self.intra_pred_mode_y[self.x][self.y] == 1 else 1)
        elif self.intra_chroma_pred_mode == 4:
                self.intra_pred_mode_c = self.intra_pred_mode_y[self.x][self.y]
        else:
            raise ValueError("Unexpected intra_chroma_pred_mode = %d" % self.intra_chroma_pred_mode)

        assert self.intra_pred_mode_c in range(0, 34 + 1)
    
    def get_intra_pred_mode_y(self, x, y):
        assert self.is_leaf() == True
        assert self.contain(x, y) == True

        x = (x / self.intra_pb_size) * self.intra_pb_size
        y = (y / self.intra_pb_size) * self.intra_pb_size

        assert self.intra_pred_mode_y[x][y] in range(0, 34 + 1)
        return self.intra_pred_mode_y[x][y]

    def decode_prev_intra_luma_pred_flag(self, y0, x0):
        ctx_inc = 0

        if self.ctx.img.slice_hdr.init_type == 0:
            ctx_offset = 0
        elif self.ctx.img.slice_hdr.init_type == 1:
            ctx_offset = 1
        elif self.ctx.img.slice_hdr.init_type == 2:
            ctx_offset = 2
        else:
            raise ValueError("Unexpected init_type.")

        ctx_idx = ctx_inc + ctx_offset
        bit = self.ctx.cabac.decode_decision("prev_intra_luma_pred_flag", ctx_idx)
        log.syntax.info("prev_intra_luma_pred_flag = %d", bit)
        return bit
    
    def decode_mpm_idx(self):
        i = 0
        while i < 2 and self.ctx.cabac.decode_bypass():
            i += 1
        value = i

        log.syntax.info("mpm_idx = %d", value)
        return value

    def decode_rem_intra_luma_pred_mode(self):
        value = self.ctx.cabac.decode_bypass();

        for i in range(4):
            value = (value << 1) | self.ctx.cabac.decode_bypass();

        log.syntax.info("rem_intra_luma_pred_mode = %d", value)
        return value;
    
    def decode_intra_chroma_pred_mode(self):
        ctx_inc = 0
        if self.ctx.img.slice_hdr.init_type == 0:
            ctx_offset = 0
        elif self.ctx.img.slice_hdr.init_type == 1:
            ctx_offset = 1
        elif self.ctx.img.slice_hdr.init_type == 2:
            ctx_offset = 2
        else:
            raise ValueError("Unexpected init_type.")

        ctx_idx = ctx_offset + ctx_inc
        value = self.ctx.cabac.decode_decision("intra_chroma_pred_mode", ctx_idx)
        if value == 0:
            value = 4
        else:
            value = self.ctx.cabac.decode_bypass()
            value = (value << 1) | self.ctx.cabac.decode_bypass()

        log.syntax.info("intra_chroma_pred_mode = %d", value)
        return value

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

    def parse(self):
        log.location.debug("Start decoding CU: (x, y) = (%d, %d), size = %d, depth = %d", self.x, self.y, self.size, self.depth)

        right_boundary_within_pic_flag = (self.x + (1 << self.log2size)) <= self.ctx.sps.pic_width_in_luma_samples
        bottom_boundary_within_pic_flag = (self.y + (1 << self.log2size)) <= self.ctx.sps.pic_height_in_luma_samples
        minimum_cb_flag = self.log2size <= self.ctx.sps.min_cb_log2_size_y

        if right_boundary_within_pic_flag and bottom_boundary_within_pic_flag and (not minimum_cb_flag):
            self.decode_split_cu_flag()
        else:
            if self.log2size > self.ctx.sps.min_cb_log2_size_y:
                self.split_cu_flag = 1
            else:
                self.split_cu_flag = 0
        
        if self.ctx.pps.cu_qp_delta_enabled_flag and self.log2size >= self.ctx.pps.log2_min_cu_qp_delta_size:
            self.is_cu_qp_delta_coded = 0
            self.cu_qp_delta_val = 0
        
        if self.split_cu_flag:
            x0 = self.x
            y0 = self.y
            x1 = self.x + (1 << (self.log2size - 1))
            y1 = self.y + (1 << (self.log2size - 1))

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
                if child.within_boundary_flag:
                    child.parse()
        else:
            self.parse_leaf()
            #self.decode_leaf()

    def decode_split_cu_flag(self):
        x0 = self.x
        y0 = self.y
        depth = self.depth

        available_left  = self.ctx.img.check_availability(x0, y0, x0-1, y0)
        available_above = self.ctx.img.check_availability(x0, y0, x0, y0-1)

        ctu_left = self.ctx.img.get_ctu(x0-1, y0) if available_left else None
        ctu_above = self.ctx.img.get_ctu(x0, y0-1) if available_above else None

        cond_left = 1 if available_left  and ctu_left.get_depth(x0-1, y0) > depth else 0
        cond_above= 1 if available_above and ctu_above.get_depth(x0, y0-1) > depth else 0

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
    
    def check_part_mode(self, part_mode):
        if self.pred_mode == self.MODE_INTRA:
            assert part_mode in (0, 1)
        else:
            if self.log2size > self.ctx.sps.min_cb_log2_size_y and self.ctx.sps.amp_enabled_flag == 1:
                assert part_mode in (0,1,2,4,5,6,7)
            elif (self.log2size > self.ctx.sps.min_cb_log2_size_y and self.ctx.sps.amp_enabled_flag == 0) or self.log2size == 3:
                assert part_mode in (0,1,2)
            else:
                assert part_mode in (0,1,2,3)

    def decode_part_mode(self):
        if self.ctx.img.slice_hdr.init_type == 0:
            ctx_offset = 0
        elif self.ctx.img.slice_hdr.init_type == 1:
            ctx_offset = 1
        elif self.ctx.img.slice_hdr.init_type == 2:
            ctx_offset = 5
        else:
            raise ValueError("Unexpected init type.")

        #TODO: check this with SPEC
        loop = 0
        value = -1
        while loop < 1:
            if self.pred_mode == self.MODE_INTRA: 
                bit = self.ctx.cabac.decode_decision("part_mode", ctx_offset + 0)
                value = IntraPartMode.PART_2Nx2N if bit else IntraPartMode.PART_NxN
                break
            else: 
                bit0 = self.ctx.cabac.decode_decision("part_mode", ctx_offset + 0)
                if bit0:
                    value = InterPartMode.PART_2Nx2N
                    break

                bit1 = self.ctx.cabac.decode_decision("part_mode", ctx_offset + 1)
                if self.log2size > self.ctx.sps.min_cb_log2_size_y:
                    if not self.ctx.sps.amp_enabled_flag: 
                        value = InterPartMode.PART_2NxN if bit1 else InterPartMode.PART_Nx2N
                        break
                    else:
                        bit3 = self.ctx.cabac.decode_decision("part_mode", ctx_offset + 3)
                        if bit3:
                            value = InterPartMode.PART_2NxN if bit1 else InterPartMode.PART_Nx2N
                            break

                        bit4 = self.ctx.cabac.decode_bypass()
                        if     bit1 and     bit4: value = InterPartMode.PART_2NxnD; break
                        if     bit1 and not bit4: value = InterPartMode.PART_2NxnU; break
                        if not bit1 and not bit4: value = InterPartMode.PART_nLx2N; break
                        if not bit1 and     bit4: value = InterPartMode.PART_nRx2N; break
                else:
                    if bit1: 
                        value = InterPartMode.PART_2NxN
                        break

                    if self.log2size == 3:
                        value = InterPartMode.PART_Nx2N
                        break
                    else:
                        bit2 = self.ctx.cabac.decode_decision("part_mode", ctx_offset + 2)
                        if bit2:
                            value = InterPartMode.PART_Nx2N
                        else:
                            value = InterPartMode.PART_NxN
                        break
            loop += 1
        
        if value == -1:
            raise ValueError("Unexpected partition mode = %d" % value)

        self.check_part_mode(value)

        log.syntax.info("part_mode = %d", value)
        return value

    def decode_leaf(self):
        if self.pcm_flag == 1:
            self.decode_pcm()
        else:
            self.decode_qp()
            raise
            if self.pred_mode == self.MODE_INTRA:
                self.decode_intra()
            elif self.pred_mode == self.MODE_INTER:
                self.decode_inter()
            else:
                raise
    
    def decode_qp(self):
        x_qg = self.x - (self.x & ((1 << self.ctx.pps.log2_min_cu_qp_delta_size) - 1))
        y_qg = self.y - (self.y & ((1 << self.ctx.pps.log2_min_cu_qp_delta_size) - 1))

        first_qg_in_ctb_row = x_qg == 0 and ((y_qg & ((1 << self.ctx.sps.ctb_log2_size_y) - 1)) == 0)

        x_slice = (self.get_root().slice_addr % self.ctx.sps.pic_width_in_ctbs_y) * self.ctx.sps.ctb_size_y
        y_slice = (self.get_root().slice_addr / self.ctx.sps.pic_width_in_ctbs_y) * self.ctx.sps.ctb_size_y
        first_qg_in_slice = x_qg == x_slice and y_qg == y_slice

        if not self.ctx.pps.tiles_enabled_flag:
            first_qg_in_tile = False
        elif not (x_qg & ((1 << self.ctx.sps.ctb_log2_size_y) - 1) == 0 and y_qg & ((1 << self.ctx.sps.ctb_log2size_y) - 1)):
            # QG is not in CTB top-left boundary
            first_qg_in_tile = False
        else:
            #x_ctb = x_qg >> self.ctx.sps.ctb_log2_size_y
            #y_ctb = y_qg >> self.ctx.sps.ctb_log2_size_y
            ctb = self.get_root()
            assert ctb.x == x_qg and ctb.y == y_qg
            first_qg_in_tile = ctb.is_first_ctb_in_tile()

        if first_qg_in_slice or first_qg_in_tile or (first_qg_in_ctb_row and self.ctx.pps.entropy_coding_sync_enabled_flag):
            prev_qp_y = self.ctx.img.slice_hdr.slice_qp_y
        else:
            prev_qp_y = self.prev_qp_y

        available_a = self.ctx.img.check_availability(self.x, self.y, x_qg-1, y_qg)
        ctu_a = self.ctx.img.get_ctu(x_qg-1, y_qg) if available_a else None
        x_tmp = (x_qg-1) >> self.ctx.sps.log2_min_transform_block_size
        y_tmp = y_qg >> self.ctx.sps.log2_min_transform_block_size
        min_tb_addr_a = self.ctx.pps.min_tb_addr_zs[x_tmp][y_tmp]
        derived_ctb_addr_a = min_tb_addr_a >> (2 * (self.ctx.sps.ctb_log2_size_y - self.ctx.sps.log2_min_transform_block_size))
        if available_a == False or self.get_root().addr_ts != derived_ctb_addr_a:
            qp_y_a = prev_qp_y
        else:
            qp_y_a = ctu_a.get_qp_y(x_qg-1, y_qg)

        available_b = self.ctx.img.check_availability(self.x, self.y, x_qg, y_qg-1)
        ctu_b = self.ctx.img.get_ctu(x_qg, y_qg-1) if available_b else None
        x_tmp = x_qg >> self.ctx.sps.log2_min_transform_block_size
        y_tmp = (y_qg-1) >> self.ctx.sps.log2_min_transform_block_size
        min_tb_addr_b = self.ctx.pps.min_tb_addr_zs[x_tmp][y_tmp]
        derived_ctb_addr_b = min_tb_addr_b >> (2 * (self.ctx.sps.ctb_log2_size_y - self.ctx.sps.log2_min_transform_block_size))
        if available_b == False and self.get_root().addr_ts != derived_ctb_addr_b:
            qp_y_b = prev_qp_y
        else:
            qp_y_b = ctu_b.get_qp_y(x_qg, y_qg-1)

        pred_qp_y = (qp_y_a + qp_y_b + 1) >> 1
        self.qp_y = ((pred_qp_y + self.cu_qp_delta_val + 52 + 2 * self.ctx.sps.qp_bd_offset_y) % (52 + self.ctx.sps.qp_bd_offset_y)) - self.ctx.sps.qp_bd_offset_y

        qp_idx_cb = utils.clip3(-self.ctx.sps.qp_bd_offset_c, 57, self.qp_y + self.ctx.pps.pps_cb_qp_offset + self.ctx.img.slice_hdr.slice_cb_qp_offset)
        qp_idx_cr = utils.clip3(-self.ctx.sps.qp_bd_offset_c, 57, self.qp_y + self.ctx.pps.pps_cr_qp_offset + self.ctx.img.slice_hdr.slice_cr_qp_offset)
        def get_qp_c(idx):
            if idx < 30:
                return idx
            elif idx <= 34:
                return idx - 1
            elif idx <= 36:
                return idx - 2
            elif idx <= 38:
                return idx - 3
            elif idx <= 40:
                return idx - 4
            elif idx <= 42:
                return idx - 5
            else:
                return idx - 6
        self.qp_cb = get_qp_c(qp_idx_cb)
        self.qp_cb = get_qp_c(qp_idx_cr)

    def decode_intra(self):
        self.pu = [None for i in range(6)]

        # Luma
        if self.intra_split_flag == 0:
            self.pu[0] = [intra.IntraPu(self, c_idx = 0, mode = self.intra_pred_mode_y[self.x][self.y])]
            self.pu[0].decode(x = self.x, y = self.y, log2size = self.log2size, depth = 0)
        else:
            for i in range(4):
                x_pb = self.x + (self.size >> 1) * (i % 2)
                y_pb = self.y + (self.size >> 1) * (i / 2)
                self.pu[i] = intra.IntraPu(self, c_idx = 0, mode = self.intra_pred_mode_y[x_pb][y_pb])
                self.pu[i].decode(x = x_pb, y = y_pb, log2size = self.log2size-1, depth = 1)
        
        # Chroma
        self.pu[4] = intra.IntraPu(self, c_idx = 1, mode = self.intra_pred_mode_c)
        self.pu[5] = intra.IntraPu(self, c_idx = 2, mode = self.intra_pred_mode_c)
        self.pu[4].decode(x = self.x/2, y = self.y/2, log2size = self.log2size-1, depth = 0)
        self.pu[5].decode(x = self.x/2, y = self.y/2, log2size = self.log2size-1, depth = 0)
