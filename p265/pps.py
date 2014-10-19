import numpy
import sys
import sld
import image
import log

class Pps:
    def __init__(self, ctx):
        self.ctx = ctx
        self.sps = self.ctx.sps
        self.scaling_list_data = sld.ScalingListData(self.ctx.bs)

    def activate_sps(self):
        self.sps = self.ctx.sps = self.ctx.sps_list[self.pps_seq_parameter_set_id]

    def parse(self):
        bs = self.ctx.bs

        log.location.info("Start decoding PPS")

        self.pps_pic_parameter_set_id = bs.ue("pps_pic_parameter_set_id")
        self.pps_seq_parameter_set_id = bs.ue("pps_seq_parameter_set_id")

        # Only after parsing to here ,we know what SPS should be used.
        self.activate_sps() # Activate SPS

        self.dependent_slice_segments_enabled_flag = bs.u(1, "dependent_slice_segments_enabled_flag")
        self.output_flag_present_flag = bs.u(1, "output_flag_present_flag")
        self.num_extra_slice_header_bits = bs.u(3, "num_extra_slice_header_bits")
        self.sign_data_hiding_enabled_flag = bs.u(1, "sign_data_hiding_enabled_flag")
        self.cabac_init_present_flag = bs.u(1, "cabac_init_present_flag")

        self.num_ref_idx_l0_default_active_minus1 = bs.ue("num_ref_idx_l0_default_active_minus1")
        self.num_ref_idx_l1_default_active_minus1 = bs.ue("num_ref_idx_l1_default_active_minus1")
        
        self.init_qp_minus26 = bs.se("init_qp_minus26")

        self.constrained_intra_pred_flag = bs.u(1, "constrained_intra_pred_flag")
        self.transform_skip_enabled_flag = bs.u(1, "transform_skip_enabled_flag")

        self.cu_qp_delta_enabled_flag = bs.u(1, "cu_qp_delta_enabled_flag")
        if self.cu_qp_delta_enabled_flag:
            self.diff_cu_qp_delta_depth = bs.ue("diff_cu_qp_delta_depth")

        self.pps_cb_qp_offset = bs.se("pps_cb_qp_offset")
        self.pps_cr_qp_offset = bs.se("pps_cr_qp_offset")
        self.pps_slice_chroma_qp_offsets_present_flag = bs.u(1, "pps_slice_chroma_qp_offsets_present_flag")

        self.weighted_pred_flag = bs.u(1, "weighted_pred_flag")
        self.weighted_bipred_flag = bs.u(1, "weighted_bipred_flag")

        self.transquant_bypass_enabled_flag = bs.u(1, "transquant_bypass_enabled_flag")

        self.tiles_enabled_flag = bs.u(1, "tiles_enabled_flag")
        self.entropy_coding_sync_enabled_flag = bs.u(1, "entropy_coding_sync_enabled_flag")

        if self.tiles_enabled_flag:
            self.num_tile_columns_minus1 = bs.ue("num_tile_columns_minus1")
            self.num_tile_rows_minus1 = bs.ue("num_tile_rows_minus1")
            self.num_tile_columns = self.num_tile_colums_minus1 + 1
            self.num_tile_rows = self.num_tile_colums_minus1 + 1

            self.uniform_spacing_flag = bs.u(1, "uniform_spacing_flag")
            if not self.uniform_spacing_flag:
                # Processig tile columns
                self.column_width_minus1 = [0] * self.num_tile_columns_minus1
                self.column_width = [0] * self.num_tile_columns
                for i in range(self.num_tile_columns_minus1):
                    self.column_width_minus1[i] = bs.ue("column_width_minus1[%d]" % i)
                    self.column_width[i] = self.column_width_minus1[i] + 1
                self.column_width[self.num_tile_columns_minus1] = self.sps.pic_width_in_ctbs_y - sum(self.column_width[0:self.num_tile_columns_minus1])
                assert self.sps.pic_width_in_ctbs_y == sum(self.column_width)

                # Processing tile rows
                self.row_height_minus1 = [0] * self.num_tile_rows_minus1
                self.row_height = [0] * self.num_tile_rows
                for i in range(self.num_tile_rows_minus1):
                    self.row_height_minus1[i] = bs.ue("row_height_minus1[%d]" % i)
                    self.row_height[i] = self.row_height_minus1[i] + 1
                self.row_height[self.num_tile_rows_minus1] = self.sps.pic_height_in_ctbs_y - sum(self.row_height[0:self.num_tile_rows_minus1])
                assert self.sps.pic_height_in_ctbs_y == sum(self.row_height)
            else:
                avg_column_width = self.sps.pic_width_in_ctbs_y / self.num_tile_columns
                self.column_width = [avg_column_width] * self.num_tile_columns

                avg_row_height = self.sps.pic_height_in_ctbs_y / self.num_tile_rows
                self.row_height= [avg_row_height] * self.num_tile_rows

            self.loop_filter_across_tiles_enabled_flag = bs.u(1, "loop_filter_across_tiles_enabled_flag")

            self.column_boundary = [0] * (self.num_tile_columns+1)
            for i in range(self.num_tile_columns):
                self.column_boundary[i+1] = self.column_boundary[i] + self.column_width[i]

            self.row_boundary = [0] * (self.num_tile_rows+1)
            for i in range(self.num_tile_rows):
                self.row_boundary[i+1] = self.row_boundary[i] + self.row_height[i]
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

            self.column_boundary = [0, self.column_width[0]]
            self.row_boundary = [0, self.row_height[0]]
        
        self.initialize_raster_and_tile_scaning_conversion_array()
        self.initialize_tile_id_array()
        self.initialize_min_tb_addr_zs_array()

        self.pps_loop_filter_across_slices_enabled_flag = bs.u(1, "pps_loop_filter_across_slices_enabled_flag")
        self.deblocking_filter_control_present_flag = bs.u(1, "deblocking_filter_control_present_flag")

        if self.deblocking_filter_control_present_flag:
            self.deblocking_filter_override_enabled_flag = bs.u(1, "deblocking_filter_override_enabled_flag")
            self.pps_deblocking_filter_disabled_flag = bs.u(1, "pps_deblocking_filter_disabled_flag")
            if not self.pps_deblocking_filter_disabled_flag:
                self.pps_beta_offset_div2 = bs.se("pps_beta_offset_div2")
                self.pps_tc_offset_div2 = bs.se("pps_tc_offset_div2")
        else:
            self.deblocking_filter_override_enabled_flag = 0

        self.pps_scaling_list_data_present_flag = bs.u(1, "pps_scaling_list_data_present_flag")
        if self.pps_scaling_list_data_present_flag:
            self.scaling_list_data.decode()

        self.lists_modification_present_flag = bs.u(1, "lists_modification_present_flag")
        self.log2_parallel_merge_level_minus2 = bs.ue("log2_parallel_merge_level_minus2")
        self.slice_segment_header_extension_present_flag = bs.u(1, "slice_segment_header_extension_present_flag")

        self.pps_extension_flag = bs.u(1, "pps_extension_flag")
        
        #TODO
        '''
        if self.pps_extension_flag:
            while bs.more_rbsp_data():
                self.pps_extension_data_flag = bs.u(1, "")
        bs.rbsp_trailing_bits()
        '''

    # Raster Scan (RS) <-> Tile Scan (TS) conversion
    def initialize_raster_and_tile_scaning_conversion_array(self):       
        self.ctb_addr_rs2ts = [None] * self.sps.pic_size_in_ctbs_y
        self.ctb_addr_ts2rs = [None] * self.sps.pic_size_in_ctbs_y

        for ctb_addr_rs in range(self.sps.pic_size_in_ctbs_y):
            tb_x = ctb_addr_rs % self.sps.pic_width_in_ctbs_y
            tb_y = ctb_addr_rs / self.sps.pic_width_in_ctbs_y

            tile_x = -1
            for i in range(self.num_tile_columns):
                if tb_x >= self.column_boundary[i]:
                    tile_x = i
            assert(tile_x >= 0)

            tile_y = -1
            for j in range(self.num_tile_rows):
                if tb_y >= self.row_boundary[j]:
                    tile_y = j
            assert(tile_y >= 0)

            self.ctb_addr_rs2ts[ctb_addr_rs] = 0
            
            for i in range(tile_x):
                self.ctb_addr_rs2ts[ctb_addr_rs] += (self.row_height[tile_y] * self.column_width[i])

            for j in range(tile_y):
                self.ctb_addr_rs2ts[ctb_addr_rs] += self.pic_width_in_ctbs_y * self.row_height[j]

            self.ctb_addr_rs2ts[ctb_addr_rs] += (tb_y - self.row_boundary[tile_y]) * self.column_width[tile_x]
            self.ctb_addr_rs2ts[ctb_addr_rs] += tb_x - self.column_boundary[tile_x]

            self.ctb_addr_ts2rs[self.ctb_addr_rs2ts[ctb_addr_rs]] = ctb_addr_rs
    
    def dump_ctb_addr(self):
        print "CTB addr in raster scaning:"
        for y in range(self.sps.pic_height_in_ctbs_y):
            if y in self.row_boundary[1:]:
                for x in range(self.sps.pic_width_in_ctbs_y):
                    sys.stdout.write("-----")
                sys.stdout.write("\n")

            for x in range(self.sps.pic_width_in_ctbs_y):
                if x in self.column_boundary[1:]:
                    sys.stdout.write("|")
                ctb_addr_rs = self.sps.pic_width_in_ctbs_y * y + x
                sys.stdout.write("%4d " % ctb_addr_rs)
            sys.stdout.write("\n")

        print "CTB addr in tile scaning:"
        for y in range(self.sps.pic_height_in_ctbs_y):
            if y in self.row_boundary[1:]:
                for x in range(self.sps.pic_width_in_ctbs_y):
                    sys.stdout.write("-----")
                sys.stdout.write("\n")

            for x in range(self.sps.pic_width_in_ctbs_y):
                if x in self.column_boundary[1:]:
                    sys.stdout.write("|")
                ctb_addr_rs = self.sps.pic_width_in_ctbs_y * y + x
                sys.stdout.write("%4d " % self.ctb_addr_rs2ts[ctb_addr_rs])
            sys.stdout.write("\n")

    # Given a CTB address in RS/TS, the array will return the tile ID which contains this CTB
    def initialize_tile_id_array(self):
        self.tile_id = [0] * self.sps.pic_size_in_ctbs_y
        self.tile_id_rs= [0] * self.sps.pic_size_in_ctbs_y
        
        tile_idx = 0
        for j in range(self.num_tile_rows):
            for i in range(self.num_tile_columns):
                for y in range(self.row_boundary[j], self.row_boundary[j+1]):
                    for x in range(self.column_boundary[i], self.column_boundary[i+1]):
                        ctb_addr_rs = y*self.sps.pic_width_in_ctbs_y + x
                        self.tile_id[self.ctb_addr_rs2ts[ctb_addr_rs]] = tile_idx
                        self.tile_id_rs[ctb_addr_rs] = tile_idx
                tile_idx += 1

    def dump_tile_id(self):
        print "Tile ID of each CTB,"
        for y in range(self.sps.pic_height_in_ctbs_y):
            if y in self.row_boundary[1:]:
                for x in range(self.sps.pic_width_in_ctbs_y):
                    sys.stdout.write("-----")
                sys.stdout.write("\n")

            for x in range(self.sps.pic_width_in_ctbs_y):
                if x in self.column_boundary[1:]:
                    sys.stdout.write("|")
                ctb_addr_rs = self.sps.pic_width_in_ctbs_y * y + x
                sys.stdout.write("%4d " % self.tile_id_rs[ctb_addr_rs])
            sys.stdout.write("\n")


    # Given a location (x, y) in minimum CB size, the array will return the CB address in Z-scan order
    def initialize_min_tb_addr_zs_array(self):
        self.min_tb_addr_zs = [[None for j in range(self.sps.pic_height_in_min_tbs)] for i in range(self.sps.pic_width_in_min_tbs)]

        for y in range(self.sps.pic_height_in_min_tbs):
            for x in range(self.sps.pic_width_in_min_tbs):
                tb_x = (x << self.sps.log2_min_transform_block_size) >> self.sps.ctb_log2_size_y
                tb_y = (y << self.sps.log2_min_transform_block_size) >> self.sps.ctb_log2_size_y

                ctb_addr_rs = self.sps.pic_width_in_ctbs_y * tb_y + tb_x
                self.min_tb_addr_zs[x][y] = self.ctb_addr_rs2ts[ctb_addr_rs] << ((self.sps.ctb_log2_size_y - self.sps.log2_min_transform_block_size) * 2)
            
                p = 0
                for i in range(self.sps.ctb_log2_size_y - self.sps.log2_min_transform_block_size):
                    m = 1 << i
                    p += ((m*m) if m&x else 0) + ((2*m*m) if m&y else 0)

                self.min_tb_addr_zs[x][y] += p
    
    def dump_min_tb_addr_zs(self):
        print "Minimum TB addr in Z-scan order,"
        for y in range(self.sps.pic_height_in_min_tbs):
            for x in range(self.sps.pic_width_in_min_tbs):
                sys.stdout.write("%4d " % self.min_tb_addr_zs[x][y])
            sys.stdout.write("\n")

if __name__ == "__main__":
    class TestSps:
        pass

    class TestContext:
        def __init__(self):
            self.sps = TestSps()
            self.bs = None

    ctx = TestContext()

    ctx.sps.pic_width_in_ctbs_y = 8
    ctx.sps.pic_height_in_ctbs_y = 4
    ctx.sps.pic_size_in_ctbs_y = ctx.sps.pic_width_in_ctbs_y * ctx.sps.pic_height_in_ctbs_y
    ctx.sps.pic_width_in_min_tbs = 8 * 4
    ctx.sps.pic_height_in_min_tbs = 4 * 4
    ctx.sps.log2_min_transform_block_size = 4
    ctx.sps.ctb_log2_size_y = 6

    pps = Pps(ctx)
    pps.num_tile_columns = 2
    pps.num_tile_rows = 2
    pps.column_boundary = [0, 4, 8]
    pps.row_boundary = [0, 2, 4]
    pps.row_height = [2, 2]
    pps.column_width = [4, 4]

    pps.sps = ctx.sps
    pps.initialize_raster_and_tile_scaning_conversion_array()
    pps.dump_ctb_addr()
    pps.initialize_tile_id_array()
    pps.dump_tile_id()
    pps.initialize_min_tb_addr_zs_array()
    pps.dump_min_tb_addr_zs()
