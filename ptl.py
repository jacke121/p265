class ProfileTierLevel:
    def __init__(self, bs):
        self.bs = bs

    def decode(self, vps_max_sub_layers_minus1):
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

        self.sub_layer_profile_present_flag = []
        self.sub_layer_level_present_flag = []
        for i in range(vps_max_sub_layers_minus1):
            self.sub_layer_profile_present_flag.append(self.bs.u(1, "sub_layer_profile_present_flag[%d]" % i))
            self.sub_layer_level_present_flag.append(self.bs.u(1, "sub_layer_level_present_flag[%d]" % i))
        
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


