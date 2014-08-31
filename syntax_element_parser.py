import bitstream_buffer

class ProfileTierLevel:
    def __init__(self, bs):
        self.bs = bs

    def parse(self, vps_max_sub_layers_minus1):
        self.general_profile_space = self.bs.u(2, "general_profile_space")
        self.general_tier_flag = self.bs.u(1, "general_tier_flag")
        self.general_profile_idc = self.bs.u(5, "general_profile_idc")

        self.general_profile_compatibility_flag = []
        for i in range(32):
            self.general_profile_compatibility_flag.append(self.bs.u(1, "general_profile_compatibility_flag[%d]" % i))
        
        self.general_progressive_source_flag = self.bs.u(1, "general_progressive_source_flag")
        self.general_interlaced_source_flag = self.bs.u(1, "general_interlaced_source_flag")
        self.general_non_packed_constraint_flag = self.bs.u(1, "general_non_packed_constraint_flag")
        self.general_frame_only_constraint_flag = self.bs.u(1, "general_frame_only_constraint_flag")
        self.general_reserved_zero_44bits = self.bs.u(32, "general_reserved_zero_44bits") << 12 | self.bs.u(12, "general_reserved_zero_44bits")
        self.general_level_idc = self.bs.u(8, "general_level_idc")

        self.gsub_layer_profile_present_flag = []
        self.gsub_layer_level_present_flag = []
        for i in range(vps_max_sub_layers_minus1):
            self.gsub_layer_profile_present_flag.append(self.bs.u(1, "sub_layer_profile_present_flag[%d]" % i))
            self.gsub_layer_level_present_flag.append(self.bs.u(1, "sub_layer_level_present_flag[%d]" % i))
        
        self.reserved_zero_2bits = []
        if vps_max_sub_layers_minus1 > 0:
            for i in range(vps_max_sub_layers_minus1):
                self.reserved_zero_2bits.append(0)
            for i in range(vps_max_sub_layers_minus1, 8):
                self.reserved_zero_2bits.append(self.bs.u(2, "reserved_zero_2bits[%d]" % i))
        
        self.sub_layer_profile_space = []
        self.sub_layer_tier_flag = []
        self.sub_layer_profile_idc = []
        self.sub_layer_profile_compatibility_flag = []
        self.sub_layer_progressive_source_flag  = []
        self.sub_layer_interlaced_source_flag = []
        self.sub_layer_non_packed_constraint_flag = []
        self.sub_layer_frame_only_constraint_flag = []
        self.sub_layer_reserved_zero_44bits = []
        self.sub_layer_level_idc = []
        for i in range(vps_max_sub_layers_minus1):
            if self.sub_layer_profile_present_flag[i]:
                self.sub_layer_profile_space.append(self.bs.u(2, "sub_layer_profile_space[%d]" % i))
                self.sub_layer_tier_flag.append(self.bs.u(1, "sub_layer_tier_flag[%d]" % i))
                self.sub_layer_profile_idc.append(self.bs.u(5, "sub_layer_profile_idc[%d]" % i))

                self.sub_layer_profile_compatibility_flag[i] = []
                for j in range(32):
                    self.sub_layer_profile_compatibility_flag[i].append(self.bs.u(1, "sub_layer_profile_compatibility_flag[%d][%d]" % (i, j)))

                self.sub_layer_progressive_source_flag.append(self.bs.u(1, "sub_layer_progressive_source_flag[%d]" % i))
                self.sub_layer_interlaced_source_flag.append(self.bs.u(1, "sub_layer_interlaced_source_flag[%d]" % i))
                self.sub_layer_non_packed_constraint_flag.append(self.bs.u(1, "sub_layer_non_packed_constraint_flag[%d]" % i))
                self.sub_layer_frame_only_constraint_flag.append(self.bs.u(1, "sub_layer_frame_only_constraint_flag[%d]" % i))
                self.sub_layer_reserved_zero_44bits.append((self.bs.u(32, "sub_layer_reserved_zero_44bits[%d]" % i) << 12) | u(12, "sub_layer_reserved_zero_44bits[%d]" % i))

            if self.sub_layer_level_present_flag[i]:
                self.sub_layer_level_idc.append(self.bs.u(8, "sub_layer_level_idc[%d]" % i))

class Vps:
    def __init__(self, bs):
        self.bs = bs
        self.profile_tier_level = ProfileTierLevel(bs)

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

class Sps:
    def __init__(self, bs):
        self.bs = bs
        self.profile_tier_level = ProfileTierLevel(bs)

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

class NaluHeader:
    def __init__(self, bs):
        self.bs = bs

    def parse(self):
        print >>self.bs.log, "============= NALU Header ============="
        self.forbidden_zero_bit = self.bs.u(1, "forbidden_zero_bit")
        assert(self.forbidden_zero_bit == 0)
        self.nal_unit_type = self.bs.u(6, "nal_unit_type")
        self.nuh_layer_id = self.bs.u(6, "nuh_layer_id")
        self.nuh_temporal_id_plus1 = self.bs.u(3, "nuh_temporal_id_plus1")

class Nalu:
    def __init__(self, bs):
        self.bs = bs
        self.naluh = NaluHeader(bs)
        self.vps = Vps(bs)
        self.sps = Sps(bs)

class AnnexB:
    def __init__(self, bs):
        self.bs = bs
        self.nalu = Nalu(bs)

    def parse(self):
        while True:
            self.bs.search_start_code()
            self.bs.report_position()

            self.nalu.naluh.parse()
            nalu_type = self.nalu.naluh.nal_unit_type

            if nalu_type == 32:
                self.nalu.vps.parse()
                self.bs.report_position()
            elif nalu_type == 33:
                self.nalu.sps.parse()
                self.bs.report_position()
                raise "TODO"
            else:
                raise "Error: unimplemeted NALU type."

if __name__ == "__main__":
    bs = bitstream_buffer.BitStreamBuffer("str.bin")
    annexb = AnnexB(bs)
    annexb.parse()
