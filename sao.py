class Sao:
	def __init__(self, ctx, x, y):
		self.ctx = ctx

		self.cabac = self.ctx.cabac

		self.img = self.ctx.img
		self.ctbs = self.img.ctbs
		self.ctb = self.img.ctbs[x][y]

		self.pps = self.img.pps
		self.sps = self.img.sps

		self.slice_hdrs = self.img.slice_hdrs
		self.slice_hdr = self.slice_hdrs[self.ctb.slice_addr]

    def decode(self):
		rx = self.ctb.x
		ry = self.ctb.y

		# Decode sao_merge_left_flag
        if rx > 0:
            left_ctb_in_slice_seg = self.ctb.addr_rs > self.ctb.slice_addr
            left_ctb_in_tile =  self.pps.tile_id[self.ctb.addr_ts] ==  self.pps.tile_id[self.pps.ctb_addr_rs2ts[self.ctb.addr_rs-1]]
            if left_ctb_in_slice_seg and left_ctb_in_tile:
                self.sao_merge_left_flag = self.decode_sao_merge_left_flag()
		else:
			self.sao_merge_left_flag = 0
		
		# Decode sao_merge_up_flag
        if ry > 0 and (not self.sao_merge_left_flag):
            up_ctb_in_slice_seg = (self.ctb.addr_rs - self.sps.pic_width_in_ctbs_y) >= self.ctb.slice_addr
            up_ctb_in_tile = self.pps.tile_id[self.ctb.addr_ts] == self.pps.tile_id[self.pps.ctb_addr_rs2ts[self.ctb.addr_rs - self.sps.pic_width_in_ctbs_y]]
            if up_ctb_in_slice_seg and up_ctb_in_tile:
                self.sao_merge_up_flag = self.decode_sao_merge_up_flag()
		else:
			self.sao_merge_up_flag = 0
        
		self.sao_type_idx = [0] * 3
        self.sao_offset_abs = [[0] * 4] * 3
        self.sao_offset_sign = [[0] * 4] * 3
        self.sao_band_position= [0] * 3
        if (not self.sao_merge_up_flag) and (not self.sao_merge_left_flag):
            for c_idx in range(3):
                if (self.slice_hdr.slice_sao_luma_flag and c_idx == 0) or (self.slice_hdr.slice_sao_chroma_flag and c_idx > 0)
                    if c_idx == 0:
                        self.sao_type_idx_luma == self.decode_sao_type_idx_luma()
                        self.sao_type_idx[0] = self.sao_type_idx_luma
                    elif c_idx == 1:
                        self.sao_type_idx_chroma == self.decode_sao_type_idx_chroma()
                        self.sao_type_idx[1] = self.sao_type_idx_chroma
                        self.sao_type_idx[2] = self.sao_type_idx_chroma
                   
                    if self.sao_type_idx[c_idx] != 0:
                        for i in range(4):
                            self.sao_offset_abs[c_idx][i] = self.decode_sao_offset_abs()

                        if self.sao_type_idx[c_idx] == 1:
                            for i in range(4):
                                if self.sao_offset_abs[c_idx][i] != 0:
                                    self.sao_offset_sign[c_idx][i] = self.decode_sao_offset_sign()
							self.sao_band_position[c_idx] = self.decode_sao_band_position()
						else:
							if c_idx == 0:
								self.sao_eo_class_luma = self.decode_sao_eo_class_luma()
							elif c_idx == 1:
								self.sao_eo_class_chroma = self.decode_sao_eo_class_chroma()
        else:
			# Set default value of sao_type_idx
            for c_idx in range(3):
                if self.sao_merge_left_flag:
                    self.sao_type_idx[c_idx] = self.ctbs[rx - 1][ry].sao.sao_tpe_idx[c_idx]
                elif self.sao_merge_up_flag:
                    self.sao_type_idx[c_idx] = self.ctbs[rx][ry - 1].sao.sao_tpe_idx[c_idx]
                else:
                    self.sao_type_idx[c_idx] = 0

			# Set default value of sao_offset_abs
            for c_idx in range(3):
				if self.sao_merge_left_flag:
					self.sao_offset_abs[c_idx] = self.ctbs[rx - 1][ry].sao.sao_offset_abs[c_idx]
				elif self.sao_merge_up_flag:
					self.sao_offset_abs[c_idx] = self.ctbs[rx][ry - 1].sao.sao_offset_abs[c_idx]
				else:
					self.sao_offset_abs[c_idx] = [0] * 4

			# Set default value of sao_offset_sign
			for c_idx in range(3):
				if self.sao_merge_left_flag:
					self.sao_offset_sign[c_idx] = self.ctbs[rx - 1][ry].sao.sao_offset_sign[c_idx]
				elif self.sao_merge_up_flag:
					self.sao_offset_sign[c_idx] = self.ctbs[rx][ry - 1].sao.sao_offset_sign[c_idx]
				elif self.sao_type_idx[c_idx] == 2:
					for i in range(4):
						if i == 0 or i == 1:
							self.sao_offset_sign[c_idx][i] = 0
						else:
							self.sao_offset_sign[c_idx][i] = 1
				else:
					self.sao_offset_sign[c_idx] = [0] * 4

			# Set defualt value of sao_band_position
			for c_idx in range(3):
				if self.sao_merge_left_flag:
					self.sao_band_position[c_idx] = self.ctbs[rx - 1][ry].sao.sao_band_position[c_idx]
				elif self.sao_merge_up_flag:
					self.sao_band_position[c_idx] = self.ctbs[rx][ry - 1].sao.sao_band_position[c_idx]
				else:
					self.sao_band_position[c_idx] = 0
			
			# Set default value of sao_eo_class
			for c_idx in range(3)
				if self.sao_merge_left_flag:
					self.sao_eo_class[c_idx] = self.ctbs[rx - 1][ry].sao.sao_eo_class[c_idx]
				elif self.sao_merge_up_flag:
					self.sao_eo_class[c_idx] = self.ctbs[rx][ry - 1].sao.sao_eo_class[c_idx]
				else:
					self.sao_eo_class[c_idx] = 0

    def decode_sao_merge_left_flag(self):
        bit = self.cabac.decode_decision("sao_merge_left_flag", 0)
		return bit

    def decode_sao_merge_up_flag(self):
        bit = self.cabac.decode_decision("sao_merge_up_flag", 0)
		return bit

    def decode_sao_type_idx(self, table):
        bit0 = self.cabac.decode_decision(table, 0)

		if bit0 == 0:
			return 0
		else:
			bit1 = self.cabac.decode_bypass()
			if bit1 == 0:
				return 1
			else:
				return 2
	
	def decode_sao_type_idx_luma(self):
		self.decode_sao_type_idx("sao_type_idx_luma")

	def decode_sao_type_idx_chroma(self):
		self.decode_sao_type_idx("sao_type_idx_chrma")

    def decode_sao_offset_abs(self):
        c_max = (1 << (math.min(self.sps.bit_depth, 10) - 5)) - 1

		for i in range(c_max):
			bit = self.cabac.decode_bypass()
			if bit == 0:
				return i

		return c_max
    
    def decode_sao_offset_sign(self):
        bit = self.cabac.decode_bypass()
		return bit

	def decode_sao_band_position(self):
		value = self.cabac.decode_bypass()

		for i in range(4):
			value = (value << 1) | self.cabac.decode_bypass()

		return value

	def decode_sao_eo_class(self):
		value = self.cabac.decode_bypass() << 1
		value |= self.cabac.decode_bypass()
		return value

	def decode_sao_eo_class_luma(self):
		self.decode_sao_eo_class()
	
	def decode_sao_eo_class_chroma(self):
		self.decode_sao_eo_class()

