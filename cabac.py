import log

class CabacTables:
    def __init__(self):
        self.setup_init_value_tables()
        self.setup_lps_range_table()
        self.setup_next_state_mps_table()
        self.setup_next_state_lps_table()
    
    def setup_init_value_tables(self):
        self.init_value_tables = {}
        self.init_value_tables["sao_merge_leftup_flag"] = [153, 153, 153] # Table 9-5
        self.init_value_tables["sao_type_idx_lumachroma_flag"] = [200, 185, 160] # Table 9-6
        self.init_value_tables["split_cu_flag"] = [139, 141, 157, 107, 139, 126, 107, 139, 126] # Table 9-7
        self.init_value_tables["cu_transquant_bypass_flag"] = [154, 154, 154] # Table 9-8
        self.init_value_tables["cu_skip_flag"] = [197, 185, 201, 197, 185, 201] # Table 9-9
        self.init_value_tables["pred_mode_flag"] = [149, 134] # Table 9-10
        self.init_value_tables["part_mode"] = [184, 154, 139, 154, 154, 154, 139, 154, 154] # Table 9-11
        self.init_value_tables["prev_intra_luma_pred_flag"] = [184, 154, 183] # Table 9-12
        self.init_value_tables["intra_chroma_pred_mode"] = [63, 152, 152] # Table 9-13
        self.init_value_tables["rqt_root_cbf"] = [79, 79] # Table 9-14
        self.init_value_tables["merge_flag"] = [110, 154] # Table 9-15
        self.init_value_tables["merge_idx"] = [122, 137] # Table 9-16
        self.init_value_tables["inter_pred_idc"] = [95, 79, 63, 31, 31, 95, 79, 63, 31, 31] # Table 9-17
        self.init_value_tables["ref_idx_l0l1"] = [153, 153, 153, 153] # Table 9-18
        self.init_value_tables["mvp_l0l1_flag"] = [168, 168] # Table 9-19
        self.init_value_tables["split_transform_flag"] = [153, 138, 138, 124, 138, 94, 224, 167, 122] # Table 9-20 
        self.init_value_tables["cbf_luma"] = [111, 141, 153, 111, 153, 111] # Table 9-21
        self.init_value_tables["cbf_chroma"] = [94, 138, 182, 154, 149, 107, 167, 154, 149, 92, 167, 154] # Table 9-22
        self.init_value_tables["abs_mvd_greater0greater1_flag"] = [140, 198, 169, 198] # Table 9-23
        self.init_value_tables["cu_qp_delta_abs"] = [154, 154, 154, 154, 154, 154] # Table 9-24
        self.init_value_tables["transform_skip_flag"] = [139, 139, 139, 139, 139, 139] # Table 9-25
        self.init_value_tables["last_sig_coeff_x_prefix"] = \
            [
                110, 110, 124, 125, 140, 153, 125, 127, 140, 109, 111, 143, 127, 111,  79, 108, 123,  63, 
                125, 110,  94, 110,  95,  79, 125, 111, 110,  78, 110, 111, 111,  95,  94, 108, 123, 108, 
                125, 110, 124, 110,  95,  94, 125, 111, 111,  79, 125, 126, 111, 111,  79, 108, 123,  93
            ] # Table 9-26
        self.init_value_tables["last_sig_coeff_y_prefix"] = \
            [
                110, 110, 124, 125, 140, 153, 125, 127, 140, 109, 111, 143, 127, 111,  79, 108, 123,  63, 
                125, 110,  94, 110,  95,  79, 125, 111, 110,  78, 110, 111, 111,  95,  94, 108, 123, 108, 
                125, 110, 124, 110,  95,  94, 125, 111, 111,  79, 125, 126, 111, 111,  79, 108, 123,  93
            ] # Table 9-27
        self.init_value_tables["coded_sub_block_flag"] = [91, 171, 134, 141, 121, 140, 61, 154, 121, 140, 61, 154] # Table 9-28
        self.init_value_tables["sig_coeff_flag"] = \
            [
                    111, 111, 125, 110, 110,  94, 124, 108, 124, 107, 125, 141, 179, 153, 125, 107,
                    125, 141, 179, 153, 125, 107, 125, 141, 179, 153, 125, 140, 139, 182, 182, 152,
                    136, 152, 136, 153, 136, 139, 111, 136, 139, 111,
                    155, 154, 139, 153, 139, 123, 123,  63, 153, 166, 183, 140, 136, 153, 154, 166,
                    183, 140, 136, 153, 154, 166, 183, 140, 136, 153, 154, 170, 153, 123, 123, 107,
                    121, 107, 121, 167, 151, 183, 140, 151, 183, 140,
                    170, 154, 139, 153, 139, 123, 123,  63, 124, 166, 183, 140, 136, 153, 154, 166,
                    183, 140, 136, 153, 154, 166, 183, 140, 136, 153, 154, 170, 153, 138, 138, 122,
                    121, 122, 121, 167, 151, 183, 140, 151, 183, 140
            ] # Table 9-29
        self.init_value_tables["coeff_abs_level_greater1_flag"] = \
            [
                140,  92, 137, 138, 140, 152, 138, 139, 153,  74, 149,  92, 139, 107, 122, 152, 
                140, 179, 166, 182, 140, 227, 122, 197, 154, 196, 196, 167, 154, 152, 167, 182, 
                182, 134, 149, 136, 153, 121, 136, 137, 169, 194, 166, 167, 154, 167, 137, 182, 
                154, 196, 167, 167, 154, 152, 167, 182, 182, 134, 149, 136, 153, 121, 136, 122, 
                169, 208, 166, 167, 154, 152, 167, 182
            ] # Table 9-30
        self.init_value_tables["coeff_abs_level_greater2_flag"] = \
            [
                138, 153, 136, 167, 152, 152, 107, 167,  91, 
                122, 107, 167, 107, 167,  91, 107, 107,  167
            ] # Table 9-31

    def setup_lps_range_table(self):
        # [64][4]
        self.lps_range_table = \
            [
                [128, 176, 208, 240],
                [128, 167, 197, 227],
                [128, 158, 187, 216],
                [123, 150, 178, 205],
                [116, 142, 169, 195],
                [111, 135, 160, 185],
                [105, 128, 152, 175],
                [100, 122, 144, 166],
                [ 95, 116, 137, 158],
                [ 90, 110, 130, 150],
                [ 85, 104, 123, 142],
                [ 81,  99, 117, 135],
                [ 77,  94, 111, 128],
                [ 73,  89, 105, 122],
                [ 69,  85, 100, 116],
                [ 66,  80,  95, 110],
                [ 62,  76,  90, 104],
                [ 59,  72,  86,  99],
                [ 56,  69,  81,  94],
                [ 53,  65,  77,  89],
                [ 51,  62,  73,  85],
                [ 48,  59,  69,  80],
                [ 46,  56,  66,  76],
                [ 43,  53,  63,  72],
                [ 41,  50,  59,  69],
                [ 39,  48,  56,  65],
                [ 37,  45,  54,  62],
                [ 35,  43,  51,  59],
                [ 33,  41,  48,  56],
                [ 32,  39,  46,  53],
                [ 30,  37,  43,  50],
                [ 29,  35,  41,  48],
                [ 27,  33,  39,  45],
                [ 26,  31,  37,  43],
                [ 24,  30,  35,  41],
                [ 23,  28,  33,  39],
                [ 22,  27,  32,  37],
                [ 21,  26,  30,  35],
                [ 20,  24,  29,  33],
                [ 19,  23,  27,  31],
                [ 18,  22,  26,  30],
                [ 17,  21,  25,  28],
                [ 16,  20,  23,  27],
                [ 15,  19,  22,  25],
                [ 14,  18,  21,  24],
                [ 14,  17,  20,  23],
                [ 13,  16,  19,  22],
                [ 12,  15,  18,  21],
                [ 12,  14,  17,  20],
                [ 11,  14,  16,  19],
                [ 11,  13,  15,  18],
                [ 10,  12,  15,  17],
                [ 10,  12,  14,  16],
                [  9,  11,  13,  15],
                [  9,  11,  12,  14],
                [  8,  10,  12,  14],
                [  8,   9,  11,  13],
                [  7,   9,  11,  12],
                [  7,   9,  10,  12],
                [  7,   8,  10,  11],
                [  6,   8,   9,  11],
                [  6,   7,   9,  10],
                [  6,   7,   8,   9],
                [  2,   2,   2,   2]
            ]

    def setup_next_state_mps_table(self):
        # [64]
        self.next_state_mps_table = \
            [
                1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,
                17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,
                33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,
                49,50,51,52,53,54,55,56,57,58,59,60,61,62,62,63
            ]

    def setup_next_state_lps_table(self):
        # [64]
        self.next_state_lps_table =\
            [
                0,0,1,2,2,4,4,5,6,7,8,9,9,11,11,12,
                13,13,15,15,16,16,18,18,19,19,21,21,22,22,23,24,
                24,25,26,26,27,27,28,29,29,30,30,30,31,32,32,33,
                33,33,34,34,35,35,35,36,36,36,37,37,37,38,38,63
            ]

class ContextModel:
    def __init__(self):
        self.val_mps = 0
        self.p_state_idx = 0

class Cabac:
    def __init__(self, bs):
        self.bs = bs
        self.tables = CabacTables()
        self.init_value_tables = self.tables.init_value_tables

        self.context_models = {} # TODO: make the size be precise
        for i in self.init_value_tables.keys():
            self.context_models[i] = []
            for j in range(len(self.init_value_tables[i])):
                self.context_models[i].append(ContextModel())

    def clip3(self, min, max, val):
        if val > max:
            result = max
        elif val < min:
            result = min
        else:
            result = val
        
        return result

    def initialization_process(self, ctx_table, ctx_idx, slice_header):
        init_value = self.init_value_tables[ctx_table][ctx_idx]
        slope_idx = init_value >> 4
        offset_idx = init_value & 0xF
        m = slope_idx * 5 - 45
        n = (offset_idx << 3) - 16
        pre_ctx_state = self.clip3(1, 126, ((m * self.clip3(0, 51, slice_header.slice_qp_y)) >> 4) + n)

        val_mps = 0 if (pre_ctx_state <= 63) else 1
        p_state_idx = (pre_ctx_state - 64) if val_mps else (63 - pre_ctx_state)
        self.context_models[ctx_table][ctx_idx].val_mps = val_mps
        self.context_models[ctx_table][ctx_idx].p_state_idx = p_state_idx

        if not (self.context_models[ctx_table][ctx_idx].p_state_idx <= 62):
            raise "Unexpected probability state."

        if ctx_table == "split_cu_flag":
            log.syntax.debug("%s: ctx_idx = %d, p_state_idx = %d, val_mps = %d, qp = %d" % (ctx_table, ctx_idx, p_state_idx, val_mps, slice_header.slice_qp_y))

            #if slice_header.slice_type == slice_header.I_SLICE:
            #    self.init_type = 0
            #elif slice_header.slice_type == slice_header.P_SLICE:
            #    self.init_type = slice_header.cabac_init_flag ? 2 : 1
            #else slice_header.slice_type == slice_header.B_SLICE:
            #    self.init_type = slice_header.cabac_init_flag ? 1 : 2

    def initialize_context_models(self, slice_header):
        for i in self.init_value_tables.keys():
            for j in range(len(self.init_value_tables[i])):
                self.initialization_process(i, j, slice_header)

    def storage_process(self):
        pass

    def synchronization_process(self):
        pass

    def initialization_process_arithmetic_decoding_engine(self):
        self.bs.report_position()
        assert self.bs.byte_aligned() == 1
        self.ivl_curr_range = 510
        self.ivl_offset = self.bs.read_bits(9)
        
        if self.ivl_offset == 510 or self.ivl_offset == 511:
            raise "Unimplemented interval offset."

    def decode_bin(self, ctx_table, ctx_idx, bypass_flag):
        if bypass_flag == 1:
            return self.decode_bypass()
        elif ctx_table == 0 and ctx_idx == 0:
            return self.decode_terminate()
        else:
            return self.decode_decision(ctx_table, ctx_idx)

    def decode_decision(self, ctx_table, ctx_idx):
        p_state_idx = self.context_models[ctx_table][ctx_idx].p_state_idx
        val_mps = self.context_models[ctx_table][ctx_idx].val_mps
        log.syntax.debug("enter decode_decision: p_state_idx = %d, val_mps = %d, ivl_curr_range = %d, ivl_offset = %d" % (p_state_idx, val_mps, self.ivl_curr_range, self.ivl_offset))

        q_range_idx = (self.ivl_curr_range >> 6) & 3
        ivl_lps_range = self.tables.lps_range_table[p_state_idx][q_range_idx]

        self.ivl_curr_range = self.ivl_curr_range - ivl_lps_range
        if self.ivl_offset >= self.ivl_curr_range:
            bin_val = 1 - val_mps
            self.ivl_offset -= self.ivl_curr_range
            self.ivl_curr_range = ivl_lps_range
        else:
            bin_val = val_mps
            
        self.state_transition_process(ctx_table, ctx_idx, bin_val)
        self.renormalization_process()

        log.syntax.debug("exit  decode_decision: p_state_idx = %d, val_mps = %d, ivl_curr_range = %d, ivl_offset = %d, bin = %d" % (p_state_idx, val_mps, self.ivl_curr_range, self.ivl_offset, bin_val))
        return bin_val

    def state_transition_process(self, ctx_table, ctx_idx, bin_val):
        if bin_val == self.context_models[ctx_table][ctx_idx].val_mps:
            self.context_models[ctx_table][ctx_idx].p_state_idx = self.tables.next_state_mps_table[self.context_models[ctx_table][ctx_idx].p_state_idx]
        else:
            if self.context_models[ctx_table][ctx_idx].p_state_idx == 0:
                self.context_models[ctx_table][ctx_idx].val_mps = 1 - self.context_models[ctx_table][ctx_idx].val_mps
            self.context_models[ctx_table][ctx_idx].p_state_idx = self.tables.next_state_lps_table[self.context_models[ctx_table][ctx_idx].p_state_idx]

    def renormalization_process(self):
        if self.ivl_curr_range < 256:
            self.ivl_curr_range <<= 1
            self.ivl_offset <<= 1
            self.ivl_offset |= self.bs.read_bits(1)

    def decode_bypass(self):
        log.syntax.debug("enter decode_bypass: ivl_curr_range = %d, ivl_offset = %d" % (self.ivl_curr_range, self.ivl_offset))
        self.ivl_offset <<= 1
        self.ivl_offset |= self.bs.read_bits(1)

        if self.ivl_offset >= self.ivl_curr_range:
            bin_val = 1
            self.ivl_offset -= self.ivl_curr_range
        else:
            bin_val = 0
        
        if self.ivl_offset >= self.ivl_curr_range:
            raise "Unexpected interval offset."

        log.syntax.debug("exit  decode_bypass: ivl_curr_range = %d, ivl_offset = %d, bin = %d" % (self.ivl_curr_range, self.ivl_offset, bin_val))
        return bin_val

    def decode_terminate(self):
        self.ivl_curr_range -= 2
        if self.ivl_offset >= self.ivl_curr_range:
            bin_val = 1
        else:
            bin_val = 0
            self.renomalization_process()

        return bin_val
    
