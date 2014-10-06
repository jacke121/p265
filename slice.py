import math
import copy
import st_rps
import cabac
import ctb
import log

class SliceSegmentHeader:
    def __init__(self, ctx):
        self.ctx = ctx

        self.short_term_ref_pic_set = st_rps.ShortTermRefPicSet(self.ctx.bs)

        self.B_SLICE = 0
        self.P_SLICE = 1
        self.I_SLICE = 2

    def activate_pps(self):
        self.vps = self.ctx.vps # VPS had been activated when parsing SPS
        self.sps = self.ctx.sps # SPS had been activated when parsing PPS
        self.pps = self.ctx.pps = self.ctx.pps_list[self.slice_pic_parameter_set_id]

    def decode(self):
        bs = self.ctx.bs

        log.main.info("============= Slice Header =============")

        self.first_slice_segment_in_pic_flag = bs.u(1, "first_slice_segment_in_pic_flag")
        if self.first_slice_segment_in_pic_flag:
            self.ctx.img.ctb = ctb.Ctb(self.ctx, addr_rs=0) # The first CTB in the picture is created with ctb_addr_rs = 0

        if self.ctx.naluh.nal_unit_type >= self.ctx.naluh.BLA_W_LP and self.ctx.naluh.nal_unit_type <= self.ctx.naluh.RSV_IRAP_VCL23:
            self.no_output_of_prior_pics_flag = bs.u(1, "no_output_of_prior_pics_flag")

        self.slice_pic_parameter_set_id = bs.ue("slice_pic_parameter_set_id")
        self.activate_pps() # Activate PPS 

        if not self.first_slice_segment_in_pic_flag:
            if self.pps.dependent_slice_segments_enabled_flag:
                self.dependent_slice_segment_flag = bs.u(1, "dependent_slice_segment_flag")
            else:
                self.dependent_slice_segment_flag = 0
            self.slice_segment_address = bs.u(math.ceil(math.log(self.sps.pic_size_in_ctbs_y, 2)), "slice_segment_address")
        else:
            self.dependent_slice_segment_flag = 0
            self.slice_segment_address = 0

        if not self.dependent_slice_segment_flag:
            self.slice_reserved_flag = [0] * self.pps.num_extra_slice_header_bits
            for i in range(self.pps.num_extra_slice_header_bits):
                self.slice_reserved_flag[i] = bs.u(1, "slice_reserved_flag[%d]" % i)

            self.slice_type = bs.ue("slice_type")
            assert self.slice_type in [0, 1, 2]

            if self.pps.output_flag_present_flag:
                self.pic_output_flag = bs.u(1, "pic_output_flag")
            else:
                self.pic_output_flag = 1

            if self.sps.separate_colour_plane_flag:
                self.colour_plane_id = bs.u(2, "colour_plane_id")
                assert self.colour_plane_id in [0, 1, 2]

            if self.ctx.naluh.nal_unit_type != self.ctx.naluh.IDR_W_RADL and self.ctx.naluh.nal_unit_type != self.ctx.naluh.IDR_N_LP:
                self.slice_pic_order_cnt_lsb = bs.u(self.sps.log2_max_pic_order_cnt_lsb_minus4 + 4, "slice_pic_order_cnt_lsb")

                self.short_term_ref_pic_set_sps_flag = bs.u(1, "short_term_ref_pic_set_sps_flag")
                self.short_term_ref_pic_set_idx = 0
                if not self.short_term_ref_pic_set_sps_flag:
                    self.short_term_ref_pic_set.decode(self.sps.num_short_term_ref_pic_sets)
                elif self.sps.num_short_term_ref_pic_sets > 1:
                    self.short_term_ref_pic_set_idx = bs.u(math.ceil(math.log(self.sps.num_short_term_ref_pic_sets, 2)), "short_term_ref_pic_set_idx")

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
                        self.num_long_term_sps = bs.ue("num_long_term_sps")
                    self.num_long_term_pics = bs.ue("num_long_term_pics")

                    self.lt_idx_sps = [0] * (self.sps.num_long_term_sps + self.sps.num_long_term_pics)
                    self.poc_lsb_lt = [0] * (self.sps.num_long_term_sps + self.sps.num_long_term_pics)
                    self.used_by_curr_pic_lt_flag = [0] * (self.sps.num_long_term_sps + self.sps.num_long_term_pics)
                    self.delta_poc_msb_present_flag = [0] * (self.sps.num_long_term_sps + self.sps.num_long_term_pics)
                    self.delta_poc_msb_cycle_lt = [0] * (self.sps.num_long_term_sps + self.sps.num_long_term_pics)
                    for i in range(self.sps.num_long_term_sps + self.sps.num_long_term_pics):
                        if i < self.num_long_term_sps:
                            if self.sps.num_long_term_ref_pics_sps > 1:
                                self.lt_idx_sps[i] = bs.u(math.ceil(math.log(self.sps.num_long_term_ref_pics_sps, 2)), "lt_idx_sps[%d]" % i)
                        else:
                            self.poc_lsb_lt[i] = bs.u(self.sps.log2_max_pic_order_cnt_lsb_minus4+4, "poc_lsb_lt[%d]" % i)
                            self.used_by_curr_pic_lt_flag[i] = bs.u(1, "used_by_curr_pic_lt_flag[%d]" % i)
                        self.delta_poc_msb_present_flag[i] = bs.u(1, "delta_poc_msb_present_flag[%d]" % i)
                        if self.delta_poc_msb_present_flag[i]:
                            self.delta_poc_msb_cycle_lt[i] = bs.ue("delta_poc_msb_cycle_lt[%d]" % i)

                for i in range(self.num_long_term_sps + self.num_long_term_pics):
                    if self.used_by_curr_pic_lt_flag[i]:
                        self.num_poc_total_curr += 1

                if self.sps.sps_temporal_mvp_enabled_flag:
                    slef.slice_temporal_mvp_enabled_flag = bs.u(1, "slice_temporal_mvp_enabled_flag")

            if self.sps.sample_adaptive_offset_enabled_flag:
                self.slice_sao_luma_flag = bs.u(1, "slice_sao_luma_flag")
                self.slice_sao_chroma_flag = bs.u(1, "slice_sao_chroma_flag")
            else:
                self.slice_sao_luma_flag = 0
                self.slice_sao_chroma_flag = 0
            
            if self.slice_type == self.P_SLICE or self.slice_type == self.B_SLICE:
                self.num_ref_idx_active_override_flag = bs.u(1, "num_ref_idx_active_override_flag")
                if self.num_ref_idx_active_override_flag:
                    self.num_ref_idx_l0_active_minus1 = bs.ue("num_ref_idx_l0_active_minus1")
                    if self.slice_type == self.B_SLICE:
                        self.num_ref_idx_l1_active_minus1 = bs.ue("num_ref_idx_l1_active_minus1")

                if self.pps.lists_modification_present_flag and self.num_poc_total_curr>1:
                    raise "Unimplemented yet"

                if self.slice_type == self.B_SLICE:
                    self.mvd_l1_zero_flag = bs.u(1, "mvd_l1_zero_flag")

                if self.pps.cabac_init_present_flag:
                    self.cabac_init_flag = bs.u(1, "cabac_init_flag")
                else:
                    self.cabac_init_flag = 0

                if self.slice_temporal_mvp_enabled_flag:
                    raise "Unimplemented yet"
                if (self.weighted_pred_flag and self.slice_type == self.P_SLICE) or (self.weighted_bipred_flag and self.slice_type == self.B_SLICE):
                    raise "Unimplemented yet"
                
                self.five_minus_max_num_merge_cand = bs.ue("five_minus_max_num_merge_cand")

            if self.slice_type == self.I_SLICE:
                self.init_type = 0
            elif self.slice_type == self.P_SLICE:
                self.init_type = (2 if self.cabac_init_flag else 1)
            elif self.slice_type == self.B_SLICE:
                self.init_type = (1 if self.cabac_init_flag else 2)

            self.slice_qp_delta = bs.se("slice_qp_delta")
            self.slice_qp_y = self.slice_qp_delta + self.pps.init_qp_minus26 + 26

            if self.pps.pps_slice_chroma_qp_offsets_present_flag:
                self.slice_cb_qp_offset = bs.se("slice_cb_qp_offset")
                self.slice_cr_qp_offset = bs.se("slice_cr_qp_offset")
            else:
                self.slice_cb_qp_offset = 0 
                self.slice_cr_qp_offset = 0 

            self.deblocking_filter_override_flag = 0
            if self.pps.deblocking_filter_override_enabled_flag:
                self.deblocking_filter_override_flag = bs.u(1, "deblocking_filter_override_flag")

            if self.deblocking_filter_override_flag:
                raise "Unimplemented yet"

            if self.pps.pps_loop_filter_across_slices_enabled_flag and \
                    (self.slice_sao_luma_flag or self.slice_sao_chroma_flag or (not self.slice_deblocking_filter_disabled_flag)):
                self.slice_loop_filter_across_slices_enabled_flag = bs.u(1, "slice_loop_filter_across_slices_enabled_flag")

        if self.pps.tiles_enabled_flag or self.pps.entropy_coding_sync_enabled_flag:
            self.num_entry_point_offsets = self.ue("num_entry_point_offsets")
            if self.num_entry_point_offsets > 0:
                self.offset_len_minus1 = bs.ue("offset_len_minus1")
                for i in range(self.num_entry_point_offsets):
                    raise "Unimplemented yet"

        if self.pps.slice_segment_header_extension_present_flag:
            raise "Unimplemented yet"

        bs.byte_alignment()

class SliceSegmentData:
    def __init__(self, ctx):
        self.ctx = ctx
        self.bs = self.ctx.bs

        self.vps = self.ctx.vps
        self.sps = self.ctx.sps
        self.pps = self.ctx.pps

        self.cabac = self.ctx.cabac

    def decode(self):
        bs = self.bs

        log.main.info("============= Slice Segment Data =============")

        if not self.ctx.img.slice_hdrs[-1].dependent_slice_segment_flag:
            self.ctx.img.slice_hdr = self.ctx.img.slice_hdrs[-1]
            self.cabac.initialize_context_models(self.ctx.img.slice_hdr)
            self.cabac.initialization_process_arithmetic_decoding_engine()
        else:
            for hdr in reversed(self.ctx.img.slice_hdrs):
                if not hdr.dependent_slice_segment_flag:
                    self.ctx.img.slice_hdr = hdr
                    break

        self.ctx.img.ctb.slice_addr = self.ctx.img.slice_hdr.slice_segment_address 

        while True:
            self.ctx.img.ctb.parse_coding_tree_unit()
            raise "The first CTU is parsed!"

            self.decode_end_of_slice_segment_flag()
            self.ctx.img.next_ctb() # Switching to next CTB
            
            switching_tile_flag = self.ctx.pps.tiles_enabled_flag and (self.ctx.pps.tile_id[self.ctx.img.ctb.addr_ts] != self.ctx.pps.tile_id[self.ctx.img.ctb.addr_ts - 1])
            if (not self.end_of_slice_segment_flag) and (switching_tile_flag or (self.ctx.pps.entropy_coding_sync_enabled_flag and (self.ctx.img.ctb.addr_ts % self.ctx.sps.pic_width_in_ctbs_y))):
                self.decode_end_of_sub_stream_one_bit()
                self.ctx.bs.byte_alignment()
            else:
                break

    def decode_end_of_slice_segment_flag(self):
        pass

    def decode_end_of_sub_stream_one_bit(self):
        pass

class SliceSegment:
    def __init__(self, ctx):
        self.ctx = ctx
        self.slice_hdr = SliceSegmentHeader(self.ctx)
        self.slice_data = SliceSegmentData(self.ctx)

    def decode(self):
        self.slice_hdr.decode()
        self.ctx.img.slice_hdrs.append(copy.deepcopy(self.slice_hdr))
        self.slice_data.decode()

