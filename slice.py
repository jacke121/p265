import math
import st_rps
import cabac

class SliceHeader:
    def __init__(self, bs, naluh, vps, sps, pps, img):
        self.bs = bs
        self.naluh = naluh
        self.vps_set = vps
        self.sps_set = sps
        self.pps_set = pps
        self.img = img
        self.short_term_ref_pic_set = st_rps.ShortTermRefPicSet(bs)

        self.B_SLICE = 0
        self.P_SLICE = 1
        self.I_SLICE = 2

    def decode(self):
        print >>self.bs.log, "============= Slice Header ============="

        self.first_slice_segment_in_pic_flag = self.bs.u(1, "first_slice_segment_in_pic_flag")
        if self.naluh.nal_unit_type >= self.naluh.BLA_W_LP and self.naluh.nal_unit_type <= self.naluh.RSV_IRAP_VCL23:
            self.no_output_of_prior_pics_flag = self.bs.u(1, "no_output_of_prior_pics_flag")

        self.slice_pic_parameter_set_id = self.bs.ue("slice_pic_parameter_set_id")
        self.pps = self.pps_set[self.slice_pic_parameter_set_id]
        self.sps = self.sps_set[self.pps.pps_seq_parameter_set_id]
        self.vps = self.vps_set[self.sps.sps_video_parameter_set_id]

        self.dependent_slice_segment_flag = 0
        if not self.first_slice_segment_in_pic_flag:
            if self.pps.dependent_slice_segments_enabled_flag:
                self.dependent_slice_segment_flag = self.bs.u(1, "dependent_slice_segment_flag")
            self.slice_segment_address = self.bs.u(math.ceil(math.log(self.sps.pic_size_in_ctbs_y, 2)), "")

        if not self.dependent_slice_segment_flag:
            self.slice_reserved_flag = [0] * self.pps.num_extra_slice_header_bits
            for i in range(self.pps.num_extra_slice_header_bits):
                self.slice_reserved_flag[i] = self.bs.u(1, "slice_reserved_flag[%d]" % i)
            self.slice_type = self.bs.ue("slice_type")

            #if slice_header.slice_type == slice_header.I_SLICE:
            #    self.init_type = 0
            #elif slice_header.slice_type == slice_header.P_SLICE:
            #    self.init_type = slice_header.cabac_init_flag ? 2 : 1
            #else slice_header.slice_type == slice_header.B_SLICE:
            #    self.init_type = slice_header.cabac_init_flag ? 1 : 2

            if self.pps.output_flag_present_flag:
                self.pic_output_flag = self.bs.u(1, "pic_output_flag")

            if self.sps.separate_colour_plane_flag:
                self.colour_plane_id = self.bs.u(2, "colour_plane_id")

            if self.naluh.nal_unit_type != self.naluh.IDR_W_RADL and self.naluh.nal_unit_type != self.naluh.IDR_N_LP:
                self.slice_pic_order_cnt_lsb = self.bs.u(self.sps.log2_max_pic_order_cnt_lsb_minus4 + 4, "slice_pic_order_cnt_lsb")

                self.short_term_ref_pic_set_sps_flag = self.bs.u(1, "short_term_ref_pic_set_sps_flag")
                self.short_term_ref_pic_set_idx = 0
                if not self.short_term_ref_pic_set_sps_flag:
                    self.short_term_ref_pic_set.parse(self.sps.num_short_term_ref_pic_sets)
                elif self.sps.num_short_term_ref_pic_sets > 1:
                    self.short_term_ref_pic_set_idx = self.bs.u(math.ceil(math.log(self.sps.num_short_term_ref_pic_sets, 2)), "short_term_ref_pic_set_idx")

                if self.short_term_ref_pic_set_sps_flag:
                    self.curr_rps_idx = self.short_term_ref_pic_set_idx
                else:
                    self.curr_rps_idx = self.sps.num_short_term_ref_pic_sets

                st_rps = [0] * (self.sps.num_short_term_ref_pic_sets + 1)
                for i in range(self.sps.num_short_term_ref_pic_sets):
                    st_rps.append(self.sps.short_term_ref_pic_set[i])
                st_rps.append(self.short_term_ref_pic_set)

                self.num_poc_total_curr = 0
                for i in range(st_rps[self.curr_rps_idx].num_negative_pics):
                    if st_rps[self.curr_rps_idx].used_by_curr_pic_s0[i]:
                        self.num_poc_total_curr += 1
                for i in range(st_rps[self.curr_rps_idx].num_postive_pics):
                    if st_rps[self.curr_rps_idx].used_by_curr_pic_s1[i]:
                        self.num_poc_total_curr += 1

                if self.sps.long_term_ref_pics_present_flag:
                    if self.sps.num_long_term_ref_pic_sps > 0:
                        self.num_long_term_sps = self.bs.ue("num_long_term_sps")
                    self.num_long_term_pics = self.bs.ue("num_long_term_pics")

                    for i in range(self.sps.num_long_term_sps + self.sps.num_long_term_pics):
                        if i < self.num_long_term_sps:
                            if self.sps.num_long_term_ref_pics_sps > 1:
                                self.lt_idx_sps[i] = self.bs.u(math.ceil(math.log(self.sps.num_long_term_ref_pics_sps, 2)), "lt_idx_sps[%d]" % i)
                        else:
                            self.poc_lsb_lt[i] = self.bs.u(self.sps.log2_max_pic_order_cnt_lsb_minus4+4, "poc_lsb_lt[%d]" % i)
                            self.used_by_curr_pic_lt_flag[i] = self.bs.u(1, "used_by_curr_pic_lt_flag[%d]" % i)

                        self.delta_poc_msb_present_flag = self.bs.u(1, "delta_poc_msb_present_flag[%d]" % i)
                        if self.delta_poc_msb_present_flag[i]:
                            self.delta_poc_msb_cycle_lt[i] = self.bs.ue("delta_poc_msb_cycle_lt[%d]" % i)

                for i in range(self.num_long_term_sps + self.num_long_term_pics):
                    if self.used_by_curr_pic_lt_flag[i]:
                        self.num_poc_total_curr += 1

                if self.sps.sps_temporal_mvp_enabled_flag:
                    slef.slice_temporal_mvp_enabled_flag = self.bs.u(1, "slice_temporal_mvp_enabled_flag")

            if self.sps.sample_adaptive_offset_enabled_flag:
                self.slice_sao_luma_flag = self.bs.u(1, "slice_sao_luma_flag")
                self.slice_sao_chroma_flag = self.bs.u(1, "slice_sao_chroma_flag")
            
            if self.slice_type == self.P_SLICE or self.slice_type == self.B_SLICE:
                self.num_ref_idx_active_override_flag = self.bs.u(1, "num_ref_idx_active_override_flag")
                if self.num_ref_idx_active_override_flag:
                    self.num_ref_idx_l0_active_minus1 = self.bs.ue("num_ref_idx_l0_active_minus1")
                    if self.slice_type == 2:
                        self.num_ref_idx_l1_active_minus1 = self.bs.ue("num_ref_idx_l1_active_minus1")

                if self.pps.lists_modification_present_flag and self.num_poc_total_curr>1:
                    raise "Unimplemented yet"

                if self.slice_type == self.B_SLICE:
                    self.mvd_l1_zero_flag = self.bs.u(1, "mvd_l1_zero_flag")

                if self.pps.cabac_init_present_flag:
                    self.cabac_init_flag = self.bs.u(1, "cabac_init_flag")

                if self.slice_temporal_mvp_enabled_flag:
                    raise "Unimplemented yet"

                if (self.weighted_pred_flag and self.slice_type == self.P_SLICE) or (self.weighted_bipred_flag and self.slice_type == self.B_SLICE):
                    raise "Unimplemented yet"
                
                self.five_minus_max_num_merge_cand = self.bs.ue("five_minus_max_num_merge_cand")

            self.slice_qp_delta = self.bs.se("slice_qp_delta")
            self.slice_qp_y = self.slice_qp_delta + self.pps.init_qp_minus26 + 26

            if self.pps.pps_slice_chroma_qp_offsets_present_flag:
                self.slice_cb_qp_offset = self.bs.se("slice_cb_qp_offset")
                self.slice_cr_qp_offset = self.bs.se("slice_cr_qp_offset")
            else:
                self.slice_cb_qp_offset = 0 
                self.slice_cr_qp_offset = 0 

            self.deblocking_filter_override_flag = 0
            if self.pps.deblocking_filter_override_enabled_flag:
                self.deblocking_filter_override_flag = self.bs.u(1, "deblocking_filter_override_flag")

            if self.deblocking_filter_override_flag:
                raise "Unimplemented yet"

            if self.pps.pps_loop_filter_across_slices_enabled_flag and \
                    (self.slice_sao_luma_flag or self.slice_sao_chroma_flag or (not self.slice_deblocking_filter_disabled_flag)):
                self.slice_loop_filter_across_slices_enabled_flag = self.bs.u(1, "slice_loop_filter_across_slices_enabled_flag")

        if self.pps.tiles_enabled_flag or self.pps.entropy_coding_sync_enabled_flag:
            self.num_entry_point_offsets = self.ue("num_entry_point_offsets")
            if self.num_entry_point_offsets > 0:
                self.offset_len_minus1 = self.bs.ue("offset_len_minus1")
                for i in range(self.num_entry_point_offsets):
                    raise "Unimplemented yet"

        if self.pps.slice_segment_header_extension_present_flag:
            raise "Unimplemented yet"

        self.bs.byte_alignment()

class SliceData:
    def __init__(self, bs, naluh, vps, sps, pps, slice_header, img):
        self.bs = bs
        self.naluh = naluh
        self.vps = vps
        self.sps = sps
        self.pps = pps
        self.slice_header = slice_header
        self.img = img
        self.cabac = cabac.Cabac(bs)
        self.ctbs = [{}] * 2048 # TODO make the size precise

    def decode(self):
        if not self.slice_header.dependent_slice_segment_flag:
            self.cabac.initialize_context_models(self.slice_header)

        while True:
            self.parse_coding_tree_unit()
            raise "Intentional Stop."

    def parse_coding_tree_unit(self):
        self.ctb_addr_rs = self.slice_header.slice_segment_address #TODO: true if first ctb of slice

        self.ctb[self.ctb_addr_rs]["slice_addr"] = [self.slice_header.slice_segment_address]

        self.x_ctb = self.ctb_addr_rs % self.sps.pic_width_in_ctbs_y
        self.y_ctb = self.ctb_addr_rs / self.sps.pic_width_in_ctbs_y

        self.x_ctb_pixels = self.x_ctb << self.sps.ctb_log2_size_y
        self.y_ctb_pixels = self.y_ctb << self.sps.ctb_log2_size_y

        if self.slice_header.slice_sao_luma_flag or self.slice_header.slice_sao_chroma_flag:
            raise "Unsupported yet."
        
        self.parse_coding_quadtree(self.x_ctb_pixels, self.y_ctb_pixels, self.sps.ctb_log2_size_y, 0)

        # should return a CTU

    def parse_coding_quadtree(self, x0, y0, log2_ctb_size, cqt_depth):
        if (x0 + (1 << log2_ctb_size)) <= self.sps.pic_width_in_luma_samples and \
           (y0 + (1 << log2_ctb_size)) <= self.sps.pic_height_in_luma_samples and \
           log2_ctb_size > self.sps.min_cb_log2_size_y:
            split_cu_flag

        pass

    def get_ctb_addr_rs_from_luma_position(self, x, y):
        ctb_x = x >> self.sps.log2_ctb_size_y;
        ctb_y = y >> self.sps.log2_ctb_size_y;
    
        return ctb_y * self.sps.pic_width_in_ctbs_y + ctb_x;

    def get_slice_addr_rs_from_ctb_addr_rs(self, ctb_addr_rs):
        return self.ctbs[ctb_addr_rs]["slice_addr"]

    def check_ctb_availability(self, x_current, y_current, x_neighbor, y_neighbor):
        if x_neighbor < 0 or y_neighbor < 0: return 0
        
        if x_neighbor >= self.sps.pic_width_in_luma_samples:  return 0
        if y_neighbor >= self.sps.pic_height_in_luma_samples: return 0

        current_ctb_addr_rs  = self.get_ctb_addr_rs_from_luma_position(x_current, y_current);
        neighbor_ctb_addr_rs = self.get_ctb_addr_rs_from_luma_position(x_neighbor, y_neighbor);

        # TODO: check if this is correct (6.4.1)
        if self.get_slice_addr_rs_from_ctb_addr_rs(self, current_ctb_addr_rs) !=\
           self.get_slice_addr_rs_from_ctb_addr_rs(self, neighbor_ctb_addr_rs):
            return 0

        # check if both CTBs are in the same tile.
        if (img->pps.TileIdRS[current_ctbAddrRS] !=
            img->pps.TileIdRS[neighbor_ctbAddrRS]) {
            return 0;
        }

        return 1

class SliceSegment:
    def __init__(self, bs, naluh, vps, sps, pps, img):
        self.bs = bs
        self.slice_header = SliceHeader(bs, naluh, vps, sps, pps, img)
        self.slice_data = SliceData(bs, naluh, vps, sps, pps, self.slice_header, img)

    def decode(self):
        self.slice_header.decode()
        self.slice_data.decode()
