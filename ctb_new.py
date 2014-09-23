import math
class Cb:
    def __init__(self, x, y, size):
        self.x = x
        self.y = y
		self.size = size # one of 64/32/16/8

		self.children = [] # 4 children or no children for quad tree 
		self.parent = None # parent node

        self.depth= 0  # depth of root is 0, maximum depth of cb with size 64/32/16/8 is 3/2/1/0
		self.split_cu_flag = 0
	
	def add_child(self, idx, child=None):
		pass

	def get_child(self, idx=0):
		pass
	
	def is_root(self):
		pass

	def is_leaf(self):
		pass

	def get_depth(self):
		pass

class Ctb(Cb):
    def __init__(self, ctx, x, y, size):
		super().__init__(x, y, size)
		self.left = None
		self.up = None
		self.upleft = None

        self.sps = self.ctx.sps
		self.x_ctb = self.x >> self.sps.ctb_log2_size_y
		self.y_ctb = self.y >> self.sps.ctb_log2_size_y
		self.addr = self.y_ctb * self.sps.pic_width_in_ctbs_y + self.x_ctb

		self.slice_addr = 0
        self.sao_info = SaoInfo()

if __name__ == "__main__":
    class Sps:
        def __init__(self, pic_width_in_ctbs, pic_width_in_min_cbs, ctb_log2_size, min_cb_log2_size):
            self.pic_width_in_ctbs_y = pic_width_in_ctbs
            self.pic_width_in_min_cbs_y = pic_width_in_min_cbs
            self.ctb_log2_size_y = ctb_log2_size
            self.min_cb_log2_size_y = min_cb_log2_size
            self.ctb_size_y = 1 << self.ctb_log2_size_y
            self.min_cb_size_y = 1 << self.min_cb_log2_size_y

            self.pic_height_in_ctbs_y = self.pic_width_in_ctbs_y
            self.pic_height_in_min_cbs_y = self.pic_width_in_min_cbs_y

    ctb1 = Ctb(addr=3, sps=Sps(2, 16, 6, 3))
    if ctb1.addr != 3: raise 

    ctb1.set_cqt_depth(64, 64, 5, 1)
    ctb1.set_cqt_depth(0xc*8, 0xc*8, 4, 1)
