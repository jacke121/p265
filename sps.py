import math
import ptl
import sld
import st_rps

import logging
log = logging.getLogger(__name__)

class VuiParameters:
    def __init__(self, bs):
        self.bs = bs

    def parse(self):
        raise "Not implemented yet"

class Sps:
    def __init__(self, ctx):
        self.ctx = ctx
        self.profile_tier_level = ptl.ProfileTierLevel(self.ctx.bs)
        self.scaling_list_data = sld.ScalingListData(self.ctx.bs)
        self.vui_parameters = VuiParameters(self.ctx.bs)

    def activate_vps(self):
        self.ctx.vps = self.ctx.vps_list[self.sps_video_parameter_set_id]

    def parse(self):
        bs = self.ctx.bs

        log.info("============= Sequence Parameter Set =============")

        self.sps_video_parameter_set_id = bs.u(4, "sps_video_parameter_set_id")
        self.activate_vps() # Activate VPS

        self.sps_max_sub_layers_minus1 = bs.u(3, "sps_max_sub_layers_minus1")
        self.sps_temporal_id_nesting_flag = bs.u(1, "sps_temporal_id_nesting_flag")

        self.profile_tier_level.decode(self.sps_max_sub_layers_minus1)

        self.sps_seq_parameter_set_id = bs.ue("sps_seq_parameter_set_id")
        self.chroma_format_idc = bs.ue("chroma_format_idc")

        self.separate_colour_plane_flag = 0
        if self.chroma_format_idc == 3:
            self.separate_colour_plane_flag = bs.u(1, "separate_colour_plane_flag")

        self.pic_width_in_luma_samples = bs.ue("pic_width_in_luma_samples")
        self.pic_height_in_luma_samples = bs.ue("pic_height_in_luma_samples")

        self.conformance_window_flag = bs.u(1, "conformance_window_flag")
        if self.conformance_window_flag:
            self.conf_win_left_offset = bs.ue("conf_win_left_offset")
            self.conf_win_right_offset = bs.ue("conf_win_right_offset")
            self.conf_win_top_offset = bs.ue("conf_win_top_offset")
            self.conf_win_bottom_offset = bs.ue("conf_win_bottom_offset")

        self.bit_depth_luma_minus8 = bs.ue("bit_depth_luma_minus8")
        self.bit_depth_chroma_minus8 = bs.ue("bit_depth_chroma_minus8")
        assert self.bit_depth_luma_minus8 in range(0, 7)
        assert self.bit_depth_chroma_minus8 in range(0, 7)
        self.bit_depth_y = self.bit_depth_luma_minus8 + 8
        self.bit_depth_c = self.bit_depth_chroma_minus8 + 8
        self.qp_bd_offset_y = self.bit_depth_luma_minus8 * 6
        self.qp_bd_offset_c = self.bit_depth_chroma_minus8 * 6

        self.log2_max_pic_order_cnt_lsb_minus4 = bs.ue("log2_max_pic_order_cnt_lsb_minus4")
        self.sps_sub_layer_ordering_info_present_flag = bs.u(1, "sps_sub_layer_ordering_info_present_flag")
        
        self.sps_max_dec_pic_buffering_minus1 = [0] * (self.sps_max_sub_layers_minus1+1)
        self.sps_max_num_reorder_pics = [0] * (self.sps_max_sub_layers_minus1+1)
        self.sps_max_latency_increase_plus1 = [0] * (self.sps_max_sub_layers_minus1+1)
        for i in range(0 if self.sps_sub_layer_ordering_info_present_flag else self.sps_max_sub_layers_minus1, self.sps_max_sub_layers_minus1+1):
            self.sps_max_dec_pic_buffering_minus1[i] = bs.ue("sps_max_dec_pic_buffering_minus1")
            self.sps_max_num_reorder_pics[i] = bs.ue("sps_max_num_reorder_pics")
            self.sps_max_latency_increase_plus1[i] = bs.ue("sps_max_latency_increase_plus1")

        self.log2_min_luma_coding_block_size_minus3 = bs.ue("log2_min_luma_coding_block_size_minus3")
        self.log2_diff_max_min_luma_coding_block_size = bs.ue("log2_diff_max_min_luma_coding_block_size")

        self.log2_min_transform_block_size_minus2 = bs.ue("log2_min_transform_block_size_minus2")
        self.log2_diff_max_min_transform_block_size = bs.ue("log2_diff_max_min_transform_block_size")

        self.max_transform_hierarchy_depth_inter = bs.ue("max_transform_hierarchy_depth_inter")
        self.max_transform_hierarchy_depth_intra = bs.ue("max_transform_hierarchy_depth_intra")

        self.initialize_picture_size_parameters()

        self.scaling_list_enabled_flag = bs.u(1, "scaling_list_enabled_flag")
        if self.scaling_list_enabled_flag:
            self.sps_scaling_list_data_present_flag = bs.u(1, "sps_scaling_list_data_present_flag")
            if self.sps_scaling_list_data_present_flag:
                scaling_list_data.parse()
        
        self.amp_enabled_flag = bs.u(1, "amp_enabled_flag")
        self.sample_adaptive_offset_enabled_flag = bs.u(1, "sample_adaptive_offset_enabled_flag")

        self.pcm_enabled_flag = bs.u(1, "pcm_enabled_flag")
        if self.pcm_enabled_flag:
            self.pcm_sample_bit_depth_luma_minus1 = bs.u(4, "pcm_sample_bit_depth_luma_minus1")
            self.pcm_sample_bit_depth_chroma_minus1 = bs.u(4, "pcm_sample_bit_depth_chroma_minus1")
            self.log2_min_pcm_luma_coding_block_size_minus3 = bs.ue("log2_min_pcm_luma_coding_block_size_minus3")
            self.log2_diff_max_min_pcm_luma_coding_block_size = bs.ue("log2_diff_max_min_pcm_luma_coding_block_size")
            self.pcm_loop_filter_disabled_flag = bs.u(1, "pcm_loop_filter_disabled_flag")

        self.num_short_term_ref_pic_sets = bs.ue("num_short_term_ref_pic_sets")
        self.short_term_ref_pic_set = [0] * self.num_short_term_ref_pic_sets
        for i in range(0, self.num_short_term_ref_pic_sets):
            self.short_term_ref_pic_set[i] = st_rps.ShortTermRefPicSet(bs)
            self.short_term_ref_pic_set[i].parse(i, self.num_short_term_ref_pic_sets)

        self.long_term_ref_pics_present_flag = bs.u(1, "long_term_ref_pics_present_flag")
        if self.long_term_ref_pics_present_flag:
            self.num_long_term_ref_pics_sps = bs.ue("num_long_term_ref_pics_sps")
            
            self.lt_ref_pic_poc_lsb_sps = [0] * self.num_long_term_ref_pics_sps
            self.used_by_curr_pic_lt_sps_flag = [0] * self.num_long_term_ref_pics_sps
            for i in range(0, self.num_long_term_ref_pics_sps):
                self.lt_ref_pic_poc_lsb_sps[i] = bs.u(self.log2_max_pic_order_cnt_lsb_minus4, "lt_ref_pic_poc_lsb_sps[%d]" % i)
                self.used_by_curr_pic_lt_sps_flag[i] = bs.u(1, "used_by_curr_pic_lt_sps_flag[%d]" % i)

        self.sps_temporal_mvp_enabled_flag = bs.u(1, "sps_temporal_mvp_enabled_flag")
        self.strong_intra_smoothing_enabled_flag = bs.u(1, "strong_intra_smoothing_enabled_flag")

        self.vui_parameters_present_flag = bs.u(1, "vui_parameters_present_flag")
        if self.vui_parameters_present_flag:
            vui_parameters.parse()

        
        self.sps_extension_flag = bs.u(1, "sps_extension_flag")

        #TODO rbsp trailing bytes
        '''
        if self.sps_extensio_flag:
            while bs.more_rbsp_data():
                self.sps_extension_data_flag = bs.u(1, "")

        bs.rbsp_trailing_bits()
        '''

        self.log_derived_picture_info()

        #raise "TODO @ SPS"

    def initialize_picture_size_parameters(self):
        self.min_cb_log2_size_y = self.log2_min_luma_coding_block_size_minus3 + 3
        self.ctb_log2_size_y = self.min_cb_log2_size_y + self.log2_diff_max_min_luma_coding_block_size

        self.min_cb_size_y = 1 << self.min_cb_log2_size_y
        self.ctb_size_y = 1 << self.ctb_log2_size_y

        self.pic_width_in_min_cbs_y = self.pic_width_in_luma_samples / self.min_cb_size_y
        self.pic_width_in_ctbs_y = self.pic_width_in_luma_samples / self.ctb_size_y

        self.pic_height_in_min_cbs_y = self.pic_height_in_luma_samples / self.min_cb_size_y
        self.pic_height_in_ctbs_y = self.pic_height_in_luma_samples / self.ctb_size_y

        self.pic_size_in_min_cbs_y = self.pic_width_in_min_cbs_y * self.pic_height_in_min_cbs_y
        self.pic_size_in_ctbs_y = self.pic_width_in_ctbs_y * self.pic_height_in_ctbs_y

        self.pic_size_in_samples_y = self.pic_width_in_luma_samples * self.pic_height_in_luma_samples

        self.log2_min_transform_block_size = self.log2_min_transform_block_size_minus2 + 2
        if self.log2_min_transform_block_size >= self.min_cb_log2_size_y:
            raise ValueError("The minimum transform block size should be less than minimum coding block size.")

        self.log2_max_transform_block_size = self.log2_min_transform_block_size + self.log2_diff_max_min_transform_block_size
        if self.log2_max_transform_block_size > min(self.ctb_log2_size_y, 5):
            raise ValueError("The maximum transform block size should not be greater than CTB size, and should be less than or equal to 32")

        self.pic_width_in_min_tbs = self.pic_width_in_ctbs_y << (self.ctb_log2_size_y - self.log2_min_transform_block_size)
        self.pic_height_in_min_tbs = self.pic_height_in_ctbs_y << (self.ctb_log2_size_y - self.log2_min_transform_block_size)
    
    def log_derived_picture_info(self):
        log.info("==============Derived Picture INFO from SPS parameters ==============")
        log.info("pic_width_in_luma_samples = %d", self.pic_width_in_luma_samples)
        log.info("pic_height_in_luma_samples = %d", self.pic_height_in_luma_samples)
        log.info("pic_width_in_ctbs_y = %d" % self.pic_width_in_ctbs_y)
        log.info("pic_height_in_ctbs_y = %d" % self.pic_height_in_ctbs_y)
        log.info("ctb_size_y = %d" % self.ctb_size_y)
        log.info("min_cb_size_y = %d" % self.min_cb_size_y)


