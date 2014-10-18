import ptl
import log

class Vps:
    def __init__(self, ctx):
        self.ctx = ctx
        self.profile_tier_level = ptl.ProfileTierLevel(ctx.bs)

    def parse(self):
        bs = self.ctx.bs

        log.main.info("++++++ Start decoding VPS ++++++")

        self.vps_video_parameter_set_id = bs.u(4, "vps_video_parameter_set_id")

        self.vps_reserved_three_2bits = bs.u(2, "vps_reserved_three_2bits")
        assert self.vps_reserved_three_2bits == 3

        self.vps_max_layers_minus1 = bs.u(6, "vps_max_layers_minus1")
        self.vps_max_sub_layers_minus1 = bs.u(3, "vps_max_sub_layers_minus1")
        self.vps_max_sub_layers = self.vps_max_sub_layers_minus1 + 1
        self.vps_temporal_id_nesting_flag = bs.u(1, "vps_temporal_id_nesting_flag")

        self.vps_reserved_0xffff_16bits = bs.u(16, "vps_reserved_0xffff_16bits")
        assert self.vps_reserved_0xffff_16bits == 0xffff

        self.profile_tier_level.decode(self.vps_max_sub_layers_minus1)
        
        self.vps_sub_layer_ordering_info_present_flag = bs.u(1, "vps_sub_layer_ordering_info_present_flag")
        self.vps_max_dec_pic_buffering_minus1 = [0] * (self.vps_max_sub_layers)
        self.vps_max_num_reorder_pics = [0] * (self.vps_max_sub_layers)
        self.vps_max_latency_increase_plus1 = [0] * (self.vps_max_sub_layers)
        for i in range(0 if self.vps_sub_layer_ordering_info_present_flag else self.vps_max_sub_layers_minus1, self.vps_max_sub_layers):
            self.vps_max_dec_pic_buffering_minus1[i] = bs.ue("vps_max_dec_pic_buffering_minus1[%d]" % i)
            self.vps_max_num_reorder_pics[i] = bs.ue("vps_max_num_reorder_pics[%d]" % i)
            self.vps_max_latency_increase_plus1[i] = bs.ue("vps_max_latency_increase_plus1[%d]" % i)

        self.vps_max_layer_id = bs.u(6, "vps_max_layer_id")
        self.vps_num_layer_sets_minus1 = bs.ue("vps_num_layer_sets_minus1")
        self.vps_num_layer_sets = self.vps_num_layer_sets_minus1 + 1

        self.layer_id_included_flag = [0] * (self.vps_num_layer_sets)
        for i in range(1, self.vps_num_layer_sets_minus1+1):
            self.layer_id_included_flag[i] = [0] * (self.vps_max_layer_id+1)
            for j in range(0, self.vps_max_layer_id+1):
                self.layer_id_include_flag[i][j] = bs.u(1, "layer_id_include_flag[%d][%d]" % (i, j))

        self.vps_timing_info_present_flag = bs.u(1, "vps_timing_info_present_flag")
        if self.vps_timing_info_present_flag:
            self.vps_num_units_in_tick = bs.u(32, "vps_num_units_in_tick")
            self.timg_scale = bs.u(32, "timg_scale")
            self.vps_poc_proportional_to_timing_flag = bs.u(1, "vps_poc_proportional_to_timing_flag")
            if self.vps_poc_proportional_to_timing_flag:
                self.vps_num_ticks_poc_diff_one_minus1 = bs.ue("vps_num_ticks_poc_diff_one_minus1")
            self.vps_num_hrd_parameters = bs.ue("vps_num_hrd_parameters")

            self.hrd_layer_set_idx = [0] * self.vps_num_hrd_parameters
            self.cprms_present_flag = [0] * self.vps_num_hrd_parameters
            for i in range(0, self.vps_num_hrd_parameters):
                self.hrd_layer_set_idx[i] = bs.ue("hrd_layer_set_idx")
                if i > 0:
                    self.cprms_present_flag[i] = bs.u(1, "cprms_present_flag")
                self.hrd_parameters.decode(self.cprms_present_flag[i], self.vps_max_sub_layers_minus1)

        self.vps_extension_flag = bs.u(1, "vps_extension_flag") 

        #TODO rbsp trailing bytes
        '''
        if self.vps_extensio_flag:
            while bs.more_rbsp_data():
                self.vps_extension_data_flag = bs.u(1, "")

        bs.rbsp_trailing_bits()
        '''
