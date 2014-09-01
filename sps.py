import ptl

class ScalingListData:
    def __init__(self, bs):
        self.bs = bs

    def parse(self):
        self.scaling_list_pred_mode_flag = [0] * 4
        self.scaling_list_pred_matrix_id_delta = [0] * 4
        self.scaling_list_dc_coef_minus8 = [0] * 2
        self.ScalingList = [0] * 4
        self.scaling_list_delta_coef = [0] * 4

        for sizeId in range(0, 4):

            self.scaling_list_pred_mode_flag[sizeId] = [0] * (2 if sizeId==3 else 6)
            self.scaling_list_pred_matrix_id_delta[sizeId] = [0] * (2 if sizeId==3 else 6)
            if (sizeId > 1):
                self.scaling_list_dc_coef_minus8[sizeId-2] = [0] * (2 if sizeId==3 else 6)
            self.ScalingList[sizeId] = [0] * (2 if sizeId==3 else 6)
            self.scaling_list_delta_coef[sizeId] = [0] * (2 if sizeId==3 else 6)

            for matrixId in range(0, 2 if sizeId==3 else 6):
                self.scaling_list_pred_mode_flag[sizeId][matrixId] = self.bs.u(1, "scaling_list_pred_mode_flag[%d][%d]" % (sizeId, matrixId))
                if not self.scaling_list_pred_mode_flag[sizeId][matrixId]:
                    self.scaling_list_pred_matrix_id_delta[sizeId][matrixId] = self.bs.ue("scaling_list_pred_matrix_id_delta[%d][%d]" % (sizeId, matrixId))
                else:
                    nextCoef = 8
                    coefNum = math.min(64, 1 << (4 + (sizeId << 1)))
                    if sizeId > 1:
                        self.scaling_list_dc_coef_minus8[sizeId-2][matrixId] = self.bs.se("scaling_list_dc_coef_minus8[%d][%d]" % (sizeId-2, matrixId))
                        nextCoef = scaling_list_dc_coef_minus8[sizeId-2][matrixId] + 8

                    self.scaling_list_delta_coef[sizeId][matrixId] = [0] * coefNum
                    self.ScalingList[sizeId][matrixId] = [0] * coefNum
                    for i in range(0, coefNum):
                        self.scaling_list_delta_coef[sizeId][matrixId][i] = self.bs.se("scaling_list_delta_coef[%d][%d][%d]" % (sizeId, matrixId, i))
                        nextCoef = (nextCoef + self.scaling_list_delta_coef[sizeId][matrixId][i] + 256) % 256
                        ScalingList[sizeId][matrixId][i] = nextCoef

class ShortTermRefPicSet:
    def __init__(self, bs):
        self.bs = bs

    def parse(self, stRpsIdx, num_short_term_ref_pic_sets):
        if stRpsIdx != 0:
            self.inter_ref_pic_set_prediction_flag = self.bs.u(1, "inter_ref_pic_set_prediction_flag")
        else:
            self.inter_ref_pic_set_prediction_flag = 0

        if self.inter_ref_pic_set_prediction_flag:
            raise "Not implemented yet"

            if stRpsIdx == num_short_term_ref_pic_sets:
                self.delta_idx_minus1 = self.bs.ue("")

            self.delta_rps_sign = self.bs.u(1, "")
            self.abs_delta_rps_minus1 = self.bs.ue("")
            #...
        else:
            self.num_negative_pics = self.bs.ue("num_negative_pics")
            self.num_positive_pics = self.bs.ue("num_positive_pics")

            self.delta_poc_s0_minus1 = [0] * self.num_negative_pics
            self.used_by_curr_pic_s0_flag = [0] * self.num_negative_pics
            for i in range(0, self.num_negative_pics):
                self.delta_poc_s0_minus1[i] = self.bs.ue("delta_poc_s0_minus1[%d]" % i)
                self.used_by_curr_pic_s0_flag[i] = self.bs.u(1, "used_by_curr_pic_s0_flag[%d]" % i)

            self.delta_poc_s1_minus1 = [0] * self.num_positive_pics
            self.used_by_curr_pic_s1_flag = [0] * self.num_positive_pics
            for i in range(0, self.num_positive_pics):
                self.delta_poc_s1_minus1[i] = self.bs.ue("delta_poc_s1_minus1[%d]" % i)
                self.used_by_curr_pic_s1_flag[i] = self.bs.u(1, "used_by_curr_pic_s1_flag[%d]" % i)

class VuiParameters:
    def __init__(self, bs):
        self.bs = bs

    def parse(self):
        raise "Not implemented yet"

class Sps:
    def __init__(self, bs):
        self.bs = bs
        self.profile_tier_level = ptl.ProfileTierLevel(bs)
        self.scaling_list_data = ScalingListData(bs)
        self.short_term_ref_pic_set = ShortTermRefPicSet(bs)
        self.vui_parameters = VuiParameters(bs)

    def parse(self):
        print >>self.bs.log, "============= Sequence Parameter Set ============="

        self.sps_video_parameter_set_id = self.bs.u(4, "sps_video_parameter_set_id")
        self.sps_max_sub_layers_minus1 = self.bs.u(3, "sps_max_sub_layers_minus1")
        self.sps_temporal_id_nesting_flag = self.bs.u(1, "sps_temporal_id_nesting_flag")

        self.profile_tier_level.parse(self.sps_max_sub_layers_minus1)

        self.sps_seq_parameter_set_id = self.bs.ue("sps_seq_parameter_set_id")
        self.chroma_format_idc = self.bs.ue("chroma_format_idc")
        if self.chroma_format_idc == 3:
            self.seperate_colour_plane_flag = self.bs.u(1, "seperate_colour_plane_flag")

        self.pic_width_in_luma_samples = self.bs.ue("pic_width_in_luma_samples")
        self.pic_height_in_luma_samples = self.bs.ue("pic_height_in_luma_samples")

        self.conformance_window_flag = self.bs.u(1, "conformance_window_flag")
        if self.conformance_window_flag:
            self.conf_win_left_offset = self.bs.ue("conf_win_left_offset")
            self.conf_win_right_offset = self.bs.ue("conf_win_right_offset")
            self.conf_win_top_offset = self.bs.ue("conf_win_top_offset")
            self.conf_win_bottom_offset = self.bs.ue("conf_win_bottom_offset")

        self.bit_depth_luma_minus8 = self.bs.ue("bit_depth_luma_minus8")
        self.bit_depth_chroma_minus8 = self.bs.ue("bit_depth_chroma_minus8")

        self.log2_max_pic_order_cnt_lsb_minus4 = self.bs.ue("log2_max_pic_order_cnt_lsb_minus4")
        self.sps_sub_layer_ordering_info_present_flag = self.bs.u(1, "sps_sub_layer_ordering_info_present_flag")
        
        self.sps_max_dec_pic_buffering_minus1 = [0] * (self.sps_max_sub_layers_minus1+1)
        self.sps_max_num_reorder_pics = [0] * (self.sps_max_sub_layers_minus1+1)
        self.sps_max_latency_increase_plus1 = [0] * (self.sps_max_sub_layers_minus1+1)
        for i in range(0 if self.sps_sub_layer_ordering_info_present_flag else self.sps_max_sub_layers_minus1, self.sps_max_sub_layers_minus1+1):
            self.sps_max_dec_pic_buffering_minus1[i] = self.bs.ue("sps_max_dec_pic_buffering_minus1")
            self.sps_max_num_reorder_pics[i] = self.bs.ue("sps_max_num_reorder_pics")
            self.sps_max_latency_increase_plus1[i] = self.bs.ue("sps_max_latency_increase_plus1")

        self.log2_min_luma_coding_block_size_minus3 = self.bs.ue("log2_min_luma_coding_block_size_minus3")
        self.log2_diff_max_min_luma_coding_block_size = self.bs.ue("log2_diff_max_min_luma_coding_block_size")
        self.log2_min_transform_block_size_minus2 = self.bs.ue("log2_min_transform_block_size_minus2")
        self.log2_diff_max_min_transform_block_size = self.bs.ue("log2_diff_max_min_transform_block_size")
        self.max_transform_hierarchy_depth_inter = self.bs.ue("max_transform_hierarchy_depth_inter")
        self.max_transform_hierarchy_depth_intra = self.bs.ue("max_transform_hierarchy_depth_intra")

        self.scaling_list_enabled_flag = self.bs.u(1, "scaling_list_enabled_flag")
        if self.scaling_list_enabled_flag:
            self.sps_scaling_list_data_present_flag = self.bs.u(1, "sps_scaling_list_data_present_flag")
            if self.sps_scaling_list_data_present_flag:
                scaling_list_data.parse()
        
        self.amp_enabled_flag = self.bs.u(1, "amp_enabled_flag")
        self.sample_adaptive_offset_enabled_flag = self.bs.u(1, "sample_adaptive_offset_enabled_flag")

        self.pcm_enabled_flag = self.bs.u(1, "pcm_enabled_flag")
        if self.pcm_enabled_flag:
            self.pcm_sample_bit_depth_luma_minus1 = self.bs.u(4, "pcm_sample_bit_depth_luma_minus1")
            self.pcm_sample_bit_depth_chroma_minus1 = self.bs.u(4, "pcm_sample_bit_depth_chroma_minus1")
            self.log2_min_pcm_luma_coding_block_size_minus3 = self.bs.ue("log2_min_pcm_luma_coding_block_size_minus3")
            self.log2_diff_max_min_pcm_luma_coding_block_size = self.bs.ue("log2_diff_max_min_pcm_luma_coding_block_size")
            self.pcm_loop_filter_disabled_flag = self.bs.u(1, "pcm_loop_filter_disabled_flag")

        self.num_short_term_ref_pic_sets = self.bs.ue("num_short_term_ref_pic_sets")
        for i in range(0, self.num_short_term_ref_pic_sets):
            self.short_term_ref_pic_set.parse(i, self.num_short_term_ref_pic_sets)

        self.long_term_ref_pics_present_flag = self.bs.u(1, "long_term_ref_pics_present_flag")
        if self.long_term_ref_pics_present_flag:
            self.num_long_term_ref_pics_sps = self.bs.ue("num_long_term_ref_pics_sps")
            
            self.lt_ref_pic_poc_lsb_sps = [0] * self.num_long_term_ref_pics_sps
            self.used_by_curr_pic_lt_sps_flag = [0] * self.num_long_term_ref_pics_sps
            for i in range(0, self.num_long_term_ref_pics_sps):
                self.lt_ref_pic_poc_lsb_sps[i] = self.bs.u(self.log2_max_pic_order_cnt_lsb_minus4, "lt_ref_pic_poc_lsb_sps[%d]" % i)
                self.used_by_curr_pic_lt_sps_flag[i] = self.bs.u(1, "used_by_curr_pic_lt_sps_flag[%d]" % i)

        self.sps_temporal_mvp_enabled_flag = self.bs.u(1, "sps_temporal_mvp_enabled_flag")
        self.strong_intra_smoothing_enabled_flag = self.bs.u(1, "strong_intra_smoothing_enabled_flag")

        self.vui_parameters_present_flag = self.bs.u(1, "vui_parameters_present_flag")
        if self.vui_parameters_present_flag:
            vui_parameters.parse()

        
        self.sps_extension_flag = self.bs.u(1, "sps_extension_flag")

        #TODO rbsp trailing bytes
        '''
        if self.sps_extensio_flag:
            while self.bs.more_rbsp_data():
                self.sps_extension_data_flag = self.bs.u(1, "")

        self.bs.rbsp_trailing_bits()
        '''

        raise "TODO @ SPS"


