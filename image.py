import ctb

class Image:
    def __init__(self, ctx):
        self.ctx = ctx
        self.slice_hdrs = [] 
        self.slice_hdr = None

        self.ctb = None
        self.ctbs = {}
    
    def next_ctb(self):
        assert self.ctb.addr_rs not in self.ctb
        self.ctbs[self.ctb.addr_rs] = self.ctb # Save the previously decoded CTB
        self.ctb = ctb.Ctb(self.ctx, self.ctx.pps.ctb_addr_ts2rs[self.ctb.addr_ts + 1]) # Create a new CTB instance

    def get_ctb_addr_rs_from_luma_pixel_coordinates(self, x, y):
        assert x > 0 and y > 0
        x_ctb = x >> self.sps.ctb_log2_size_y
        y_ctb = y >> self.sps.ctb_log2_size_y
        return y_ctb * self.ctx.sps.pic_width_in_ctbs_y + x_ctb

    def get_cqt_depth(self, x, y):
        ctb_addr_rs = self.get_ctb_addr_rs_from_luma_pixel_coordinates(x, y)
        ctb = self.ctbs[ctb_addr_rs]
        for leave in ctb.get_leaves():
            if leave.contain(x, y):
                return leave.depth

    def check_availability(self, x_current, y_current, x_neighbor, y_neighbor):
        min_block_addr_current = self.ctx.pps.min_tb_addr_zs[x_current >> self.ctx.sps.log2_min_transform_block_size][y_current >> self.ctx.sps.log2_min_transform_block_size]
        
        if x_neighbor < 0 or y_neighbor < 0: 
            return False
        elif x_neighbor >= self.sps.pic_width_in_luma_samples:  
            return False
        elif y_neighbor >= self.sps.pic_height_in_luma_samples: 
            return False
        else:
            min_block_addr_neighbor = self.ctx.pps.min_tb_addr_zs[x_neighbor >> self.ctx.pps.log2_min_transform_block_size][y_neighbor >> self.ctx.sps.log2_min_transform_block_size]

        ctb_addr_rs_current = self.get_ctb_addr_rs_from_luma_pixel_coordinates(x_current, y_current)
        ctb_addr_rs_neighbor= self.get_ctb_addr_rs_from_luma_pixel_coordinates(x_neighbor, y_neighbor)

        in_different_tiles_flag = self.ctx.pps.tile_id_rs[ctb_addr_rs_current] != self.ctx.pps.tile_id_rs[ctb_addr_rs_neighbor]
        in_different_slices_flag = self.ctx.img.ctbs[ctb_addr_rs_current].slice_addr != self.ctx.img.ctbs[ctb_addr_rs_neighbor].slice_addr

        if min_block_addr_neighbor > min_block_addr_current:
            return False
        elif in_different_slices_flag:
            return False
        elif in_different_tiles_flag:
            return False
        else:
            return True

    def get_upright_diagonal_scan_order_array(self, size):
        diagnoal_scan = numpy.zeros((size*size, 2))

        i = x = y = 0
        stop = False
        while not stop:
            while y >= 0:
                if x < size and y < size:
                    diagnoal_scan[i][0] = x
                    diagnoal_scan[i][1] = y
                    i += 1
                y -= 1
                x += 1
            y = x
            x = 0
            if i >= (size * size):
                stop = True

        return diagnoal_scan
        
    def get_horizontal_scan_order_array(self, size):
        horizontal_scan = numpy.zeros((size*size, 2))

        i = 0
        for y in range(size):
            for x in range(size):
                horizontal_scan[i][0] = x
                horizontal_scan[i][1] = y
                i += 1

        return horizontal_scan

    def get_vertical_scan_order_array(self, size):
        vertical_scan = numpy.zeros((size*size, 2))

        i = 0
        for x in range(size):
            for y in range(size):
                vertical_scan[i][0] = x
                vertical_scan[i][1] = y
                i += 1

        return vertical_scan

