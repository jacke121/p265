import sld

class Pps:
    def __init__(self, bs):
        self.bs = bs
        self.scaling_list_data = sld.ScalingListData(bs)

    def parse(self):
        print >>self.bs.log, "============= Picture Parameter Set ============="

        self.pps_pic_parameter_set_id = self.bs.ue("pps_pic_parameter_set_id")
        self.pps_seq_parameter_set_id = self.bs.ue("pps_seq_parameter_set_id")
        self.dependent_slice_segments_enabled_flag = self.bs.u(1, "dependent_slice_segments_enabled_flag")
        self.output_flag_present_flag = self.bs.u(1, "output_flag_present_flag")
        self.num_extra_slice_header_bits = self.bs.u(3, "num_extra_slice_header_bits")
        self.sign_datahiding_enabled_flag = self.bs.u(1, "sign_datahiding_enabled_flag")
        self.cabac_init_present_flag = self.bs.u(1, "cabac_init_present_flag")
        self.num_ref_idx_l0_defualt_active_minus1 = self.bs.ue("num_ref_idx_l0_defualt_active_minus1")
        self.num_ref_idx_l1_defualt_active_minus1 = self.bs.ue("num_ref_idx_l1_defualt_active_minus1")
        self.init_qp_minus26 = self.bs.se("init_qp_minus26")
        self.constrained_intra_pred_flag = self.bs.u(1, "constrained_intra_pred_flag")
        self.transform_skip_enabled_flag = self.bs.u(1, "transform_skip_enabled_flag")
        self.cu_qp_delta_enabled_flag = self.bs.u(1, "cu_qp_delta_enabled_flag")
        if self.cu_qp_delta_enabled_flag:
            self.diff_cu_qp_delta_depth = self.bs.ue("diff_cu_qp_delta_depth")
        self.pps_cb_qp_offset = self.bs.se("pps_cb_qp_offset")
        self.pps_cr_qp_offset = self.bs.se("pps_cr_qp_offset")
        self.pps_slice_chroma_qp_offsets_present_flag = self.bs.u(1, "pps_slice_chroma_qp_offsets_present_flag")
        self.weighted_pred_flag = self.bs.u(1, "weighted_pred_flag")
        self.weighted_bipred_flag = self.bs.u(1, "weighted_bipred_flag")
        self.transquant_bypass_enabled_flag = self.bs.u(1, "transquant_bypass_enabled_flag")
        self.tiles_enabled_flag = self.bs.u(1, "tiles_enabled_flag ")
        self.entropy_coding_sync_enabled_flag = self.bs.u(1, "entropy_coding_sync_enabled_flag")
        if self.tiles_enabled_flag:
            self.num_tile_columns_minus1 = self.bs.ue("num_tile_columns_minus1")
            # TODO
            raise "Unimplemented yet."

        self.pps_loop_filter_across_slices_enabled_flag = self.bs.u(1, "pps_loop_filter_across_slices_enabled_flag")
        self.deblocking_filter_control_present_flag = self.bs.u(1, "deblocking_filter_control_present_flag")

        self.deblocking_filter_override_enabled_flag = 0
        if self.deblocking_filter_control_present_flag:
            self.deblocking_filter_override_enabled_flag = self.bs.u(1, "deblocking_filter_override_enabled_flag")
            self.pps_deblocking_filter_disabled_flag = self.bs.u(1, "pps_deblocking_filter_disabled_flag")
            if not self.pps_deblocking_filter_disabled_flag:
                self.pps_beta_offset_div2 = self.bs.se("pps_beta_offset_div2")
                self.pps_tc_offset_div2 = self.bs.se("pps_tc_offset_div2")

        self.pps_scaling_list_data_present_flag = self.bs.u(1, "pps_scaling_list_data_present_flag")
        if self.pps_scaling_list_data_present_flag:
            self.scaling_list_data.parse()

        self.lists_modification_present_flag = self.bs.u(1, "lists_modification_present_flag")
        self.log2_parallel_merge_level_minus2 = self.bs.ue("log2_parallel_merge_level_minus2")
        self.slice_segment_header_extension_present_flag = self.bs.u(1, "slice_segment_header_extension_present_flag")
        self.pps_extension_flag = self.bs.u(1, "pps_extension_flag")

        '''
        if self.pps_extension_flag:
            while self.bs.more_rbsp_data():
                self.pps_extension_data_flag = self.bs.u(1, "")
        self.bs.rbsp_trailing_bits()
        '''

        

