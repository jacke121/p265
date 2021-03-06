import matplotlib.patches as patches
import matplotlib.pyplot as plt
import ctu

class Image:
    def __init__(self, ctx):
        self.ctx = ctx
        self.slice_hdrs = [] 
        self.slice_hdr = None

        self.ctu = None
        self.ctus = {}
    
    def next_ctu(self, end_of_slice_segment_flag):
        assert self.ctu.addr_rs not in self.ctus
        self.ctus[self.ctu.addr_rs] = self.ctu # Save the previously decoded CTU
        if not end_of_slice_segment_flag:
            self.ctu = ctu.Ctu(self.ctx, self.ctx.pps.ctb_addr_ts2rs[self.ctu.addr_ts + 1]) # Create a new CTU instance

    def draw(self, ax):
        for i in self.ctus:
            self.ctus[i].draw(ax)

    def get_ctu_addr_rs(self, x, y):
        assert x >= 0 and y >= 0
        x_ctb = x >> self.ctx.sps.ctb_log2_size_y
        y_ctb = y >> self.ctx.sps.ctb_log2_size_y
        return y_ctb * self.ctx.sps.pic_width_in_ctbs_y + x_ctb

    def get_ctu(self, x, y):
        ctb_addr_rs = self.get_ctu_addr_rs(x, y)
        if ctb_addr_rs == self.ctu.addr_rs:
            ctu = self.ctu
        else:
            ctu = self.ctus[ctb_addr_rs]
        return ctu

    def check_availability(self, x_current, y_current, x_neighbor, y_neighbor):
        log2_min_transform_block_size = self.ctx.sps.log2_min_transform_block_size
        min_block_addr_current = self.ctx.pps.min_tb_addr_zs[x_current >> log2_min_transform_block_size][y_current >> log2_min_transform_block_size]
        
        if x_neighbor < 0 or y_neighbor < 0: 
            return False
        elif x_neighbor >= self.ctx.sps.pic_width_in_luma_samples:  
            return False
        elif y_neighbor >= self.ctx.sps.pic_height_in_luma_samples: 
            return False
        else:
            min_block_addr_neighbor = self.ctx.pps.min_tb_addr_zs[x_neighbor >> log2_min_transform_block_size][y_neighbor >> log2_min_transform_block_size]

        if min_block_addr_neighbor > min_block_addr_current:
            return False

        ctb_addr_rs_current = self.get_ctu_addr_rs(x_current, y_current)
        ctb_addr_rs_neighbor= self.get_ctu_addr_rs(x_neighbor, y_neighbor)
        
        #print "current_addr = %d, neighbor_addr = %d" % (ctb_addr_rs_current, ctb_addr_rs_neighbor)
        assert ctb_addr_rs_current == self.ctu.addr_rs

        if ctb_addr_rs_current == ctb_addr_rs_neighbor:
            in_different_slices_flag = False
            in_different_tiles_flag = False
        else:
            assert ctb_addr_rs_neighbor in self.ctus
            in_different_tiles_flag = self.ctx.pps.tile_id_rs[ctb_addr_rs_current] != self.ctx.pps.tile_id_rs[ctb_addr_rs_neighbor]
            in_different_slices_flag = self.ctu.slice_addr != self.ctx.img.ctus[ctb_addr_rs_neighbor].slice_addr

        if in_different_slices_flag:
            return False
        elif in_different_tiles_flag:
            return False
        else:
            return True

