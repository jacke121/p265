import sld
import img

class Pps:
    def __init__(self, ctx):
		self.ctx = ctx
        self.bs = self.ctx.bs
		self.img = self.ctx.img
        self.sps_list = self.ctx.sps_list
        self.scaling_list_data = sld.ScalingListData(bs)

	def activate_sps(self):
        self.sps = self.sps_list[pps_seq_paramter_set_id]
		self.ctx.sps = self.sps

		self.create_img()
	
	def create_img(self):
		self.img = img.Image()
        self.img.ctb = ctb.Ctb(self.ctx, 0, 0, 1 << self.sps.ctb_log2_size_y)
        self.img.ctbs = [[None] * self.sps.pic_height_in_ctbs_y] * self.sps.pic_width_in_ctbs_y

    def parse(self):
        print >>self.bs.log, "============= Picture Parameter Set ============="

        self.pps_pic_parameter_set_id = self.bs.ue("pps_pic_parameter_set_id")
        self.pps_seq_parameter_set_id = self.bs.ue("pps_seq_parameter_set_id")
		self.activate_sps()

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
            self.num_tile_rows_minus1 = self.bs.ue("num_tile_rows_minus1")

            self.num_tile_columns = self.num_tile_colums_minus1 + 1
            self.num_tile_rows = self.num_tile_colums_minus1 + 1

            self.uniform_spacing_flag = self.bs.u(1, "uniform_spacing_flag")
            if not self.uniform_spacing_flag:
                self.column_width_minus1 = [0] * self.num_tile_columns_minus1
                self.column_width = [0] * self.num_tile_columns
                for i in range(self.num_tile_columns_minus1):
                    self.column_width_minus1[i] = self.bs.ue("column_width_minus1[%d]" % i)
                    self.column_width[i] = self.column_width_minus1[i] + 1
                self.column_width[self.num_tile_columns_minus1] = self.sps.pic_width_in_ctbs_y - sum(self.column_width_minus1)

                self.row_height_minus1 = [0] * self.num_tile_rows_minus1
                self.row_height = [0] * self.num_tile_rows
                for i in range(self.num_tile_rows_minus1):
                    self.row_height_minus1[i] = self.bs.ue("row_height_minus1[%d]" % i)
                    self.row_height[i] = self.row_height_minus1[i] + 1
                self.row_height[self.num_tile_rows_minus1] = self.sps.pic_height_in_ctbs_y - sum(self.row_height_minus1)

                self.loop_filter_across_tiles_enabled_flag = self.u(1, "loop_filter_across_tiles_enabled_flag")
            else:
                avg_column_width = self.sps.pic_width_in_ctbs_y / self.num_tile_columns
                self.column_width = [avg_column_width] * self.num_tile_columns

                avg_row_height = self.sps.pic_height_in_ctbs_y / self.num_tile_rows
                self.row_height= [avg_row_height] * self.num_tile_rows

            self.column_boundary = [0] * (self.num_tile_columns+1)
            for i in range(self.num_tile_columns):
                self.column_boundary[i+1] = self.column_boundary[i] + self.column_width[i]

            self.row_boundary = [0] * (self.num_tile_rows+1)
            for i in range(self.num_tile_rows):
                self.row_boundary[i+1] = self.row_boundary[i] + self.row_width[i]
        else:
            self.num_tile_columns_minus1 = 0
            self.num_tile_rows_minus1 = 0
            self.num_tile_columns = 1
            self.num_tile_rows = 1
            self.uniform_spacing_flag = 1

            self.column_width_minus1 = [self.sps.pic_width_in_ctbs_y - 1]
            self.row_height_minus1 = [self.sps.pic_height_in_ctbs_y -1]
            self.column_width = [self.sps.pic_width_in_ctbs_y]
            self.row_height = [self.sps.pic_height_in_ctbs_y]

            self.column_boundary = [0, self.column_width]
            self.row_boundary = [0, self.row_width]
        
        self.ctb_addr_rs2ts = [0] * self.sps.pic_size_in_ctbs_y
        self.ctb_addr_ts2rs = [0] * self.sps.pic_size_in_ctbs_y
        self.tile_id = [0] * self.sps.pic_size_in_ctbs_y
        self.tile_id_rs= [0] * self.sps.pic_size_in_ctbs_y

        # Raster scan (RS) <-> tile scan (TS) conversion
        for ctb_addr_rs in range(self.sps.pic_size_in_ctbs_y):
            tb_x = ctb_addr_rs % self.sps.pic_width_in_ctbs_y
            tb_y = ctb_addr_rs / self.sps.pic_width_in_ctbs_y

            tile_x = -1
            for i in range(self.num_tile_columns):
                if tb_x >= self.column_boundary[i]:
                    tile_x = i

            tile_y = -1
            for j in range(self.num_tile_rows):
                if tb_y >= self.row_boundary[i]:
                    tile_y = j

            self.ctb_addr_rs2ts[ctb_addr_rs] = 0
            
            for i in range(tile_x):
                self.ctb_addr_rs2ts[ctb_addr_rs] += self.row_height[tile_y] * self.column_width[i]

            for j in range(tile_y):
                self.ctb_addr_rs2ts[ctb_addr_rs] += self.sps.pic_width_in_ctbs_y * self.row_height[j]

            self.ctb_addr_rs2ts[ctb_addr_rs] += (tb_y - self.row_boundary[tile_y]) * self.column_width[tile_x]
            self.ctb_addr_rs2ts[ctb_addr_rs] += tb_x - self.column_boundary[tile_x]

            self.ctb_addr_ts2rs[self.ctb_addr_rs2ts[ctb_addr_rs]] = ctb_addr_rs

        for j in range(self.num_tile_rows):
            for i in range(self.num_tile_columns):
                for y in range(self.row_boundary[j], self.row_boundary[j+1]):
                    for x in range(self.colunm_boundary[i], self.column_boundary[i+1]):
                        self.tile_id[self.ctb_addr_rs2ts[y*self.pic_width_in_ctbs_y + x]] = tile_idx
                        self.tile_id_rs[y*self.pic_width_in_ctbs_y + x] = tile_idx
                tile_idx += 1

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

        

