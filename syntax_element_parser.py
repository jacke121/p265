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


class NaluHeader:
    def __init__(self, bs):
        self.bs = bs

    def parse(self):
        self.forbidden_zero_bit = self.bs.u(1, "forbidden_zero_bit")
        assert(self.forbidden_zero_bit == 0)
        print "byte_idx = %d bit_idx = %d" % (bs.byte_idx, bs.bit_idx)
        self.nal_unit_type = self.bs.u(6, "nal_unit_type")
        self.nuh_layer_id = self.bs.u(6, "nuh_layer_id")
        self.nuh_temporal_id_plus1 = self.bs.u(3, "nuh_temporal_id_plus1")

class Nalu:
    def __init__(self, bs):
        self.bs = bs
        self.naluh = NaluHeader(bs)
        self.vps = Vps(bs)

    def parse(self):
        self.naluh.parse()
        
        nalu_type = self.naluh.nal_unit_type
        if nalu_type == 32:
            self.vps.parse()
        else:
            raise "Error: unimplemeted NALU type."

class AnnexB:
    def __init__(self, bs):
        self.bs = bs
        self.nalu = Nalu(bs)

    def parse(self):
        #while self.bs.next_bits(24) != 0x000001 and self.bs.next_bits(32) != 0x00000001:
        #    if self.bs.f(8, "leading_zero_8bits") != 0x00:
        #        raise "Error: unexpected leading_zero_8bits."

        #if self.bs.next_bits(24) != 0x000001:
        #    if self.bs.f(8, "zero_byte") != 0x00:
        #        raise "Error: unexpected zero_byte."

        #self.bs.f(24, "start_code_prefix_one_3bytes")
        
        self.bs.search_start_code()

        print "byte_idx = %d bit_idx = %d" % (bs.byte_idx, bs.bit_idx)

        self.nalu.parse()

        raise "TODO"

if __name__ == "__main__":
    bs = bitstream_buffer.BitStreamBuffer("str.bin")
    annexb = AnnexB(bs)
    annexb.parse()
