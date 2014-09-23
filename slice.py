import math
import st_rps
import cabac
import ctb
import slice_hdr

class SliceData:
    def __init__(self, ctx):
		self.ctx = ctx

        self.bs = self.ctx.bs
        self.img = self.ctx.img
        self.ctbs = self.img.ctbs
		self.slice_hdrs = self.ctx.img.slice_hdrs

        self.naluh = self.ctx.naluh

        self.vps = self.ctx.vps
        self.sps = self.ctx.sps
        self.pps = self.ctx.pps

        self.slice_hdr = None # The slice header used to decode the current slice data segment
		self.ctb = self.img.ctb
        self.cabac = cabac.Cabac(bs)

    def decode(self):
        if not self.slice_hdrs[-1].dependent_slice_segment_flag:
            self.cabac.initialize_context_models(self.slice_hdr)
			self.slice_hdr = self.slice_hdrs[-1]
		else:
			self.slice_hdr = self.slice_hdrs[-2]

        #self.img.ctb_addr_rs = self.slice_hdrs[-1].slice_segment_address
        while True:
            self.parse_coding_tree_unit()
            raise "Intentional Stop."

    def parse_coding_tree_unit(self):

        if self.slice_hdr.slice_sao_luma_flag or self.slice_hdr.slice_sao_chroma_flag:
            self.decode_sao()
        
        self.parse_coding_quadtree(self.ctb.x, self.ctb.y, self.sps.ctb_log2_size_y, 0, 0, self.ctb, True)

        # should return a CTU

    def parse_coding_quadtree(self, x0, y0, log2size, depth, idx, parent, exist):
		if exist and parent:
			cb = Cb(x0, y0, log2size)
			cb.parent = parent
			cb.depth = depth
			if depth == 0: 
				pass # do nothing for root CTB 
			elif depth == 1:
				parent.add_child(idx, cb)
			elif depth == 2:
				parent.add_child(idx, cb)
			elif depth == 3:
				parent.add_child(idx, cb)
			else:
				raise ValueError("Unexpected depth value.")
		elif (not exist) and parent:
			parent.add_child(None)
			return
		else:
			return

		right_boundary_within_pic_flag = (x0 + (1 << log2size)) <= self.sps.pic_width_in_luma_samples
		bottom_boundary_within_pic_flag = (y0 + (1 << log2size)) <= self.sps.pic_height_in_luma_samples
		minimum_cb_flag = log2size > self.sps.min_cb_log2_size_y

		if right_boundary_within_pic_flag and bottom_boundary_within_pic_flag and (not minimum_cb_flag):
			split_cu_flag = self.decode_split_cu_flag()
		
		"""
		if cu_qp_delta_enabled_flag and ...:
			is_cu_qp_delta_coded = 0
			cu_qp_delta_val = 0
		"""
		
		if split_cu_flag:
			x1 = x0 + (1 << log2size)
			y1 = y0 + (1 << log2size)

			if depth == 0:
				next_parent = self.ctb
			elif depth == 1:
				next_parent = parent.children[idx]
			elif depth == 2:
				next_parent = parent.children[idx]
			elif depth == 3:
				next_parent = parent.children[idx]
			else:
				raie ValueError("Unexpected depth")

			self.parse_coding_quadtree(x0, y0, log2size-1, depth+1, 0, next_parent, True)
			self.parse_coding_quadtree(x1, y0, log2size-1, depth+1, 1, next_parent, x1 < self.sps.pic_width_in_luma_samples)
			self.parse_coding_quadtree(x0, y1, log2size-1, depth+1, 2, next_parent, y1 < self.sps.pic_height_in_luma_samples)
			self.parse_coding_quadtree(x1, y1, log2size-1, depth+1, 3, next_parent, x1 < self.sps.pic_width_in_luma_samples and y1 < self.sps.pic_height_in_luma_samples)
		else:
			self.parse_coding_unit(x0, y0, log2size)

        raise "Unimplemented yet." 

	def parse_coding_unit(self, x0, y0, log2size):
		pass

    def get_ctb_addr(self, x, y):
        ctb_x = x >> self.sps.log2_ctb_size_y;
        ctb_y = y >> self.sps.log2_ctb_size_y;
    
        return ctb_y * self.sps.pic_width_in_ctbs_y + ctb_x;

    def get_slice_addr_rs_from_ctb_addr_rs(self, ctb_addr_rs):
        if self.ctbs.has_key(ctb_addr_rs):
            return self.ctbs[ctb_addr_rs]["slice_addr"]
        else:
            return -1

    def check_ctb_availability(self, x_current, y_current, x_neighbor, y_neighbor):
        if x_neighbor < 0 or y_neighbor < 0: return 0
        
        if x_neighbor >= self.sps.pic_width_in_luma_samples:  return 0
        if y_neighbor >= self.sps.pic_height_in_luma_samples: return 0

        current_ctb_addr_rs  = self.get_ctb_addr_rs_from_luma_position(x_current, y_current);
        neighbor_ctb_addr_rs = self.get_ctb_addr_rs_from_luma_position(x_neighbor, y_neighbor);

        # TODO: check if this is correct (6.4.1)
        if self.get_slice_addr_rs_from_ctb_addr_rs(neighbor_ctb_addr_rs) == -1:
            return 0

        if self.pps.tiles_enabled_flag:
            raise "Unsupported yet."
        # check if both CTBs are in the same tile.
        #if (img->pps.TileIdRS[current_ctbAddrRS] !=
        #    img->pps.TileIdRS[neighbor_ctbAddrRS]) {
        #    return 0;
        #}

        return 1

    def set_cqt_depth(self, x, y, log2size, depth):
        ctb_addr = self.get_ctb_addr(x, y)
        return self.ctbs[ctb_addr].set_cqt_addr(x, y, log2size, depth)

    def get_cqt_depth(self, x, y):
        ctb_addr = self.get_ctb_addr(x, y)
        return self.ctbs[ctb_addr].get_cqt_addr(x, y)

    def decode_split_cu_flag(self, x0, y0, cqt_depth):
        availableL = self.check_availability(x0, y0, x0-1, y0)
        availableA = self.check_availability(x0, y0, x0, y0-1)

        condL = condA = 0
        if availableL and self.get_cqt_depth(x0-1, y0) > cqt_depth: condL = 1
        if availableA and self.get_cqt_depth(x0, y0-1) > cqt_depth: condA = 1

        context_offset= condL + condA
        context_idx = context_offset

        bit = self.cabac.decode_bin("split_cu_flag", context_idx, 0)
        return bit


class SliceSegment:
    def __init__(self, ctx):
		self.ctx = ctx
        self.bs = self.ctx.bs

        self.slice_hdr = slice_hdr.SliceHeader(self.ctx)
        self.slice_data = SliceData(self.ctx)

    def decode(self):
        self.slice_hdr.decode()
		self.img.slice_hdrs.append(self.slice_hdr)

		self.slice_data.decode()
