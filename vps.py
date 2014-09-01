import ptl

class Vps:
    def __init__(self, bs):
        self.bs = bs
        self.profile_tier_level = ptl.ProfileTierLevel(bs)

    def parse(self):
        print >>self.bs.log, "============= Video Parameter Set ============="

        self.vps_video_parameter_set_id = self.bs.u(4, "vps_video_parameter_set_id")

        self.vps_reserved_three_2bits = self.bs.u(2, "vps_reserved_three_2bits")
        if self.vps_reserved_three_2bits != 3:
            raise "Error: unexpected vps_reserved_three_2bits."

        self.vps_max_layers_minus1 = self.bs.u(6, "vps_max_layers_minus1")
        self.vps_max_sub_layers_minus1 = self.bs.u(3, "vps_max_sub_layers_minus1")
        self.vps_temporal_id_nesting_flag = self.bs.u(1, "vps_temporal_id_nesting_flag")

        self.vps_reserved_0xffff_16bits = self.bs.u(16, "vps_reserved_0xffff_16bits")
        if self.vps_reserved_0xffff_16bits != 0xffff:
            raise "Error: unexpected vps_reserved_0xffff_16bits."

        self.profile_tier_level.parse(self.vps_max_sub_layers_minus1)
        
        self.vps_sub_layer_ordering_info_present_flag = self.bs.u(1, "vps_sub_layer_ordering_info_present_flag")
        self.vps_max_dec_pic_buffering_minus1 = [0] * (self.vps_max_sub_layers_minus1 + 1)
        self.vps_max_num_reorder_pics = [0] * (self.vps_max_sub_layers_minus1 + 1)
        self.max_latency_increase_plus1 = [0] * (self.vps_max_sub_layers_minus1 + 1)
        for i in range(0 if self.vps_sub_layer_ordering_info_present_flag else self.vps_max_sub_layers_minus1, self.vps_max_sub_layers_minus1 + 1):
            self.vps_max_dec_pic_buffering_minus1[i] = self.bs.ue("vps_max_dec_pic_buffering_minus1[%d]" % i)
            self.vps_max_num_reorder_pics[i] = self.bs.ue("vps_max_num_reorder_pics[%d]" % i)
            self.max_latency_increase_plus1[i] = self.bs.ue("max_latency_increase_plus1[%d]" % i)

        self.vps_max_layer_id = self.bs.u(6, "vps_max_layer_id")
        self.vps_num_layer_sets_minus1 = self.bs.ue("vps_num_layer_sets_minus1")

        self.layer_id_included_flag = [0] * (self.vps_num_layer_sets_minus1 + 1)
        for i in range(1, self.vps_num_layer_sets_minus1+1):
            self.layer_id_included_flag[i] = [0] * (self.vps_max_layer_id+1)
            for j in range(0, self.vps_max_layer_id+1):
                self.layer_id_include_flag[i][j] = self.bs.u(1, "layer_id_include_flag[%d][%d]" % (i, j))

        self.vps_timing_info_present_flag = self.bs.u(1, "vps_timing_info_present_flag")
        if self.vps_timing_info_present_flag:
            self.vps_num_units_in_tick = self.bs.u(32, "vps_num_units_in_tick")
            self.timg_scale = self.bs.u(32, "timg_scale")
            self.vps_poc_proportional_to_timing_flag = self.bs.u(32, "vps_poc_proportional_to_timing_flag")
            if self.vps_poc_proportional_to_timing_flag:
                self.vps_num_ticks_poc_diff_one_minus1 = self.bs.ue("vps_num_ticks_poc_diff_one_minus1")
            self.vps_num_hrd_parameters = self.bs.ue("vps_num_hrd_parameters")

            self.hrd_layer_set_idx = [0] * self.vps_num_hrd_parameters
            for i in range(0, self.vps_num_hrd_parameters):
                self.hrd_layer_set_idx[i] = self.bs.ue("hrd_layer_set_idx")
                if i > 0:
                    self.cprms_present_flag[i] = self.bs.u(1, "cprms_present_flag")
                self.hrd_parameters.parse(self.cprms_present_flag[i], self.vps_max_sub_layers_minus1)

        self.vps_extension_flag = self.bs.u(1, "vps_extension_flag") 

        #TODO rbsp trailing bytes


