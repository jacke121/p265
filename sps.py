import ptl

class Sps:
    def __init__(self, bs):
        self.bs = bs
        self.profile_tier_level = ptl.ProfileTierLevel(bs)

    def parse(self):
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

        self.log2_max_pic_order_cont_lsb_minus4 = self.bs.ue("log2_max_pic_order_cont_lsb_minus4")
        self.sps_sub_layer_ordering_info_present_flag = self.bs.u(1, "sps_sub_layer_ordering_info_present_flag")
        
        self.sps_max_dec_pic_buffering_minus1 = [0] * (self.sps_max_sub_layers_minus1+1)
        self.sps_max_num_reorder_pics = [0] * (self.sps_max_sub_layers_minus1+1)
        self.sps_max_latency_increase_plus1 = [0] * (self.sps_max_sub_layers_minus1+1)
        for i in range(0 if self.sps_sub_layer_ordering_info_present_flag else self.sps_max_sub_layers_minus1, self.sps_max_sub_layers_minus1+1):
            self.sps_max_dec_pic_buffering_minus1[i] = self.bs.ue("sps_max_dec_pic_buffering_minus1")
            self.sps_max_num_reorder_pics[i] = self.bs.ue("sps_max_num_reorder_pics")
            self.sps_max_latency_increase_plus1[i] = self.bs.ue("sps_max_latency_increase_plus1")

        raise "TODO @ SPS"


