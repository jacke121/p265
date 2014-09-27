import math
import sao

import logging
log = logging.getLogger(__name__)

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
        self.children.append(child)
        assert len(self.children) <= 4

    def get_child(self, idx=0):
        self.children[idx]
    
    def is_root(self):
        if self.parent is None: 
            return True
        else:
            return False

    def is_leaf(self):
        return len(self.children) == 0

    def contain(self, x, y):
        x_flag = x >= self.x and x < (self.x + self.size)
        y_flag = y >= self.y and y < (self.y + self.size)

    def traverse(self):
        yield self
        for child in self.children:
            child.traverse()

    def iter_leaves(self):
        for n in self.traverse():
            if n.is_leaf():
                yield n

    def get_leaves(self):
        return [n for n in self.iter_leaves()]

class Ctb(Cb):
    def __init__(self, ctx, addr_rs):# CTB is indexed by its raster scanning address
        # CB is indexed by its (x, y) coordinates in the picture
        Cb.__init__(self, (addr_rs % ctx.sps.pic_width_in_ctbs_y) << ctx.sps.ctb_log2_size_y, (addr_rs / ctx.sps.pic_width_in_ctbs_y) << ctx.sps.ctb_log2_size_y, ctx.sps.ctb_size_y)

        self.ctx = ctx

        self.slice_addr = 0
        self.sps = self.ctx.sps
        self.pps = self.ctx.pps
        self.addr_rs = addr_rs

        self.x_ctb = self.x >> self.ctx.sps.ctb_log2_size_y
        self.y_ctb = self.y >> self.ctx.sps.ctb_log2_size_y

        self.sao = sao.Sao(self.ctx, self.x_ctb, self.y_ctb)

    def parse_coding_tree_unit(self):
        if self.ctx.img.slice_hdr.slice_sao_luma_flag or self.ctx.img.slice_hdr.slice_sao_chroma_flag:
            self.ctx.img.ctb.sao.decode()
        
        self.parse_coding_quadtree(self.x, self.y, self.ctx.sps.ctb_log2_size_y, depth=0, idx=0, parent=None, exist=True)

        self.draw_partitio(self)

    def draw_ctb_partition(self):
        pass

    def parse_coding_quadtree(self, x0, y0, log2size, depth, idx, parent, exist):
        assert depth in [0, 1, 2, 3]

        if parent is None:
            pass
        elif exist:
            cb = Cb(x0, y0, log2size)
            cb.parent = parent
            cb.depth = depth
            assert depth in [1, 2, 3]
            parent.add_child(cb)
        elif not exist:
            parent.add_child(None)
            return
        else:
            raise ValueError("Unexpected situation.")

        right_boundary_within_pic_flag = (x0 + (1 << log2size)) <= self.sps.pic_width_in_luma_samples
        bottom_boundary_within_pic_flag = (y0 + (1 << log2size)) <= self.sps.pic_height_in_luma_samples
        minimum_cb_flag = log2size > self.sps.min_cb_log2_size_y

        if right_boundary_within_pic_flag and bottom_boundary_within_pic_flag and (not minimum_cb_flag):
            self.decode_split_cu_flag(x0, y0, depth)
        else:
            if log2size > self.ctx.sps.min_cb_log2_size_y:
                self.split_cu_flag = 1
            else:
                self.split_cu_flag = 0
        
        """
        if cu_qp_delta_enabled_flag and ...:
            is_cu_qp_delta_coded = 0
            cu_qp_delta_val = 0
        """
        
        if self.split_cu_flag:
            x1 = x0 + (1 << log2size)
            y1 = y0 + (1 << log2size)
            
            self.parse_coding_quadtree(x0, y0, log2size-1, depth+1, 0, self, True)
            self.parse_coding_quadtree(x1, y0, log2size-1, depth+1, 1, self, x1 < self.sps.pic_width_in_luma_samples)
            self.parse_coding_quadtree(x0, y1, log2size-1, depth+1, 2, self, y1 < self.sps.pic_height_in_luma_samples)
            self.parse_coding_quadtree(x1, y1, log2size-1, depth+1, 3, self, x1 < self.sps.pic_width_in_luma_samples and y1 < self.sps.pic_height_in_luma_samples)
        else:
            self.parse_coding_unit(x0, y0, log2size)

        raise "Unimplemented yet." 
    
    def parse_coding_unit(self, x0, y0, log2size):
        raise "Unimplemented yet." 

    def decode_split_cu_flag(self, x0, y0, depth):
        available_left  = self.check_availability(x0, y0, x0-1, y0)
        available_above = self.check_availability(x0, y0, x0, y0-1)

        cond_left = 1 if available_left  and self.get_cqt_depth(x0-1, y0) > depth else 0
        cond_above= 1 if available_above and self.get_cqt_depth(x0, y0-1) > depth else 0

        context_inc = cond_left + cond_above

        if self.ctx.img.slice_hdr.init_type == 0:
            context_offset = 0
        elif self.ctx.img.slice_hdr.init_type == 1:
            context_offset = 3
        elif self.ctx.img.slice_hdr.init_type == 2:
            context_offset = 6
        else:
            raise ValueError("Unexpected init type.")

        context_idx = context_offset + context_inc

        self.split_cu_flag = self.ctx.cabac.decode_bin("split_cu_flag", context_idx, 0)
        log.info("split_cu_flag = %d" % self.split_cu_flag)

    def get_cqt_depth(self, x, y, log2size, depth):
        ctb_addr_rs = self.get_ctb_addr_rs_from_luma_pixel_coordinates(x, y)
        if ctb_addr_rs == self.addr_rs: # In the current CTB
            for leave in self.get_leaves():
                if leave.contain(x, y):
                    return leave.depth
        else:
            assert ctb_addr_rs in self.ctx.img.ctbs
            self.ctx.img.ctbs[ctb_addr_rs].get_cqt_addr(x, y, log2size, depth)

    def check_availability(self, x_current, y_current, x_neighbor, y_neighbor):
        min_block_addr_current = self.ctx.pps.min_tb_addr_zs[x_current >> self.ctx.sps.log2_min_transform_block_size][y_current >> self.ctx.sps.log2_min_transform_block_size]
        
        if x_neighbor < 0 or y_neighbor < 0: 
            return False
        elif x_neighbor >= self.sps.pic_width_in_luma_samples:  
            return False
        elif y_neighbor >= self.sps.pic_height_in_luma_samples: 
            return False
        else:
            min_block_addr_neighbor = self.ctx.pps.min_tb_addr_zs[x_neighbor >> self.log2_min_transform_block_size][y_neighbor >> self.log2_min_transform_block_size]

        ctb_addr_rs_current = self.get_ctb_addr_rs_from_luma_pixel_coordinates(x_current, y_current)
        ctb_addr_rs_neighbor= self.get_ctb_addr_rs_from_luma_pixel_coordinates(x_neighbor, y_neighbor)

        assert ctb_addr_rs_current == self.addr_rs

        in_different_tiles_flag = self.ctx.pps.tile_id_rs[self.addr_rs] != self.ctx.pps.tile_id_rs[ctb_addr_rs_neighbor]
        in_different_slices_flag = self.slice_addr != self.ctx.img.ctbs[ctb_addr_rs_neighbor].slice_addr

        if min_block_addr_neighbor > min_block_addr_current:
            return False
        elif in_different_slices_flag:
            return False
        elif in_different_tiles_flag:
            return False
        else:
            return True

    def get_ctb_addr_rs_from_luma_pixel_coordinates(self, x, y):
        assert x > 0 and y > 0
        x_ctb = x >> self.sps.ctb_log2_size_y
        y_ctb = y >> self.sps.ctb_log2_size_y
        return y_ctb * self.ctx.sps.pic_width_in_ctbs_y + x_ctb

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
