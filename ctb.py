import sys
import random
import math
import sao

import logging
log = logging.getLogger(__name__)

class Cb:
    def __init__(self, x, y, size, depth=0, parent=None):
        self.x = x
        self.y = y
        self.size = size # one of 64/32/16/8
        self.depth= depth# depth of root is 0, maximum depth of cb with size 64/32/16/8 is 3/2/1/0
        self.parent = parent

        self.children = [] # 4 children or no children for quad tree 
        self.split_cu_flag = 0
    
    def add_child(self, child=None):
        self.children.append(child) # In order appending
        assert len(self.children) <= 4

    def get_child(self, idx=0):
        assert idx >= 0 and idx <= 3
        self.children[idx]
    
    def is_root(self):
        return True if self.parent is None else False

    def is_leaf(self):
        return len(self.children) == 0

    def contain(self, x, y):
        x_flag = x >= self.x and x < (self.x + self.size)
        y_flag = y >= self.y and y < (self.y + self.size)
        return x_flag and y_flag

    def traverse(self):
        yield self
        for child in self.children:
            if child is not None:
                for i in child.traverse():
                    yield i

    def get_leaves(self):
        leaves = []
        for n in self.traverse():
            if n.is_leaf():
                leaves.append(n)
        return leaves

    def dump(self):
        print "%s%dx%d(%d)" % (' '*4*self.depth, self.x, self.y, self.size)
        for n in self.children:
            if n is not None:
                n.dump()

    def dump_leaves(self):
        if self.is_leaf():
            print "%dx%d(%d)" % (self.x, self.y, self.size)
        else:
            for n in self.children:
                if n is not None:
                    n.dump_leaves()

    def split(self, size, depth):
        if len(self.children) == 4: 
            raise ValueError("Already split.")
        cb = [None] * 4
        cb[0] = Cb(self.x, self.y, size, depth, self)
        cb[1] = Cb(self.x+size, self.y, size, depth, self)
        cb[2] = Cb(self.x, self.y+size, size, depth, self)
        cb[3] = Cb(self.x+size, self.y+size, size, depth, self)
        #if random.randint(0,1):
        #    not_exist_idx = random.randint(0,3)
        #    cb[not_exist_idx] = None
        for i in range(4):
            self.add_child(cb[i])

    def populate(self, max_depth):
        if self.depth > max_depth: 
            return
        self.split_cu_flag = random.randint(0, 1)
        if self.split_cu_flag == 1:
            self.split(self.size/2, self.depth + 1)
        for n in self.children:
            if n is not None:
                n.populate(max_depth)

    def __str__(self):
        a = [[' ' for i in range(self.size)] for j in range(self.size)]
        print "leaves = ", self.get_leaves()
        for n in self.get_leaves():
            print "%dx%d(%d)" % (n.x, n.y, n.size)
            x0 = n.x - self.x
            y0 = n.y - self.y
            for i in range(x0, x0+n.size):
                a[y0][i] = '-'
                a[y0+n.size-1][i] = '-'
            for i in range(y0, y0+n.size):
                a[i][x0] = '|'
                a[i][x0+n.size-1] = '|'

        s = ""
        for y in range(self.size):
            for x in range(self.size):
                s += a[y][x]
            s += "\n"
        return s

class Ctb(Cb):
    def __init__(self, ctx, addr_rs):
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
        
        self.parse_coding_quadtree(self.x, self.y, self.ctx.sps.ctb_log2_size_y, depth=0, parent=None, exist=True)

        print(self)

    def parse_coding_quadtree(self, x0, y0, log2size, depth, parent, exist):
        assert depth in [0, 1, 2, 3]

        if parent is None:
            pass
        elif exist:
            cb = Cb(x0, y0, log2size, depth, parent)
            assert depth in [1, 2, 3]
            parent.add_child(cb)
        elif not exist:
            parent.add_child(None)
            return
        else:
            raise ValueError("Unexpected situation.")

        right_boundary_within_pic_flag = (x0 + (1 << log2size)) <= self.sps.pic_width_in_luma_samples
        bottom_boundary_within_pic_flag = (y0 + (1 << log2size)) <= self.sps.pic_height_in_luma_samples
        minimum_cb_flag = log2size <= self.sps.min_cb_log2_size_y

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
            
            self.parse_coding_quadtree(x0, y0, log2size-1, depth+1, self, True)
            self.parse_coding_quadtree(x1, y0, log2size-1, depth+1, self, x1 < self.sps.pic_width_in_luma_samples)
            self.parse_coding_quadtree(x0, y1, log2size-1, depth+1, self, y1 < self.sps.pic_height_in_luma_samples)
            self.parse_coding_quadtree(x1, y1, log2size-1, depth+1, self, x1 < self.sps.pic_width_in_luma_samples and y1 < self.sps.pic_height_in_luma_samples)
        else:
            self.parse_coding_unit(x0, y0, log2size)

        raise "Unimplemented yet." 
    
    def parse_coding_unit(self, x0, y0, log2size):
        raise "Unimplemented yet." 

    def decode_split_cu_flag(self, x0, y0, depth):
        available_left  = self.ctx.img.check_availability(x0, y0, x0-1, y0)
        available_above = self.ctx.img.check_availability(x0, y0, x0, y0-1)

        cond_left = 1 if available_left  and self.ctx.img.get_cqt_depth(x0-1, y0) > depth else 0
        cond_above= 1 if available_above and self.ctx.img.get_cqt_depth(x0, y0-1) > depth else 0

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


if __name__ == "__main__":
    ctb = Cb(0, 0, 64)
    ctb.populate(2)
    ctb.dump()
    ctb.dump_leaves()
    
    for i in ctb.traverse():
        print "%s%dx%d(%d)" % (' '*4*i.depth, i.x, i.y, i.size)
    
    cb0 = Cb(0, 0, 32)
    assert cb0.contain(31, 31) == True
    assert cb0.contain(32, 32) == False
    assert cb0.contain(1,2) == True
    print ctb
    exit()

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
