import utils

class IntraPu:
    def __init__(self, cu, c_idx, mode):
        self.cu = cu
        self.c_idx = c_idx
        self.mode = mode

    def decode(self, x, y, log2size, depth):
        split_transform_flag = self.get_split_transform_flag(x, y, depth)
        if self.c_idx == 0:
            split_flag = split_transform_flag
            x_luma = x
            y_luma = y
        else:
            if split_transform_flag == 1 and self.log2size > 2:
                split_flag = 1
            else:
                split_flag = 0
            x_luma = x << 1
            y_luma = y << 1

        if split_flag == 1:
            offset = 1 << (log2size - 1)
            self.decode(x_luma, y_luma, log2size - 1, depth + 1)
            self.decode(x_luma + offset, y_luma, log2size - 1, depth + 1)
            self.decode(x_luma, y_luma + offset, log2size - 1, depth + 1)
            self.decode(x_luma + offset, y_luma + offset, log2size - 1, depth + 1)
        else:
            self.decode_leaf(x, y, log2size, depth)
    
    def get_split_transform_flag(self, x, y, depth):
        for i in self.cu.tu.traverse(strategy = "breath-first"):
            if i.contain(x, y) and i.depth == depth:
                return i.split_transform_flag
        raise ValueError("Error: can't find the split_transform_flag in the specified pixel coordinates and depth.")

    def decode_leaf(self, x, y, log2size, depth):
        self.decode_neighbor()
        self.decode_prediction_samples()
        self.scaling_process()
        self.transformation_process()
        self.reconstruction_process()


    def decode_neighbor(self, x0, y0, log2size, depth):
        size = 1 << log2size

        def x_neighbor_iterator(size):
            x = -1
            for y in reversed(range(-1, size*2, 1)):
                yield (x, y)

        def y_neighbor_iterator(size):
            y = -1
            for x in range(0, size*2, 1):
                yield (x, y)

        def xy_neighbor_iterator(size):
            for (x, y) in x_neighbor_iterator(size):
                yield (x, y)

            for (x, y) in y_neighbor_iterator(size):
                yield (x, y)

        self.neighbor = utils.md_dict()
        for (x, y) in self.neighbor_iterator(size):
            self.neighbor[x][y] = -1

        x_current, y_current = x0, y0
        for (x, y) in self.neighbor_iterator(size):
            x_neighbor, y_neighbor = x_current + x, y_current + y
            if self.c_idx > 0:
                x_neighbor, y_neighbor = x_neighbor << 1, y_neighbor << 1
                x_current, y_current = x_current << 1, y_current << 1
            
            available = self.cu.ctx.img.check_availability(x_current, y_current, x_neighbor, y_neighbor)
            if available == False or (self.cu.ctx.img.get("pred_mode", x_neighbor, y_neighbor) != self.cu.MODE_INTRA and self.cu.ctx.pps.constrained_intra_pred_flag == 1):
                pass
            else:
                self.neighbor[x][y] = self.cu.ctx.img.get_sample(x_neighbor, y_neighbor)

        substitute_enable = 0
        no_available_neighbors = 1
        for (x, y) in self.neighbor_iterator(size):
            if self.neighbor[x][y] == -1:
                substitute_enable = 1
            else:
                no_available_neighbors = 0
        if substitute_enable == 1:
            bit_depth = self.cu.ctx.img.slice_hdr.bit_depth_y if self.c_idx == 0 else self.cu.ctx.img.slice_hdr.bit_depth_c
            if no_available_neighbors == 1:
                for (x, y) in xy_neighbor_iterator(size):
                    self.neighbor[x][y] = 1 << (bit_depth - 1)
            else:
                if self.neighbor[-1][size*2 - 1] == -1:
                    for (x, y) in xy_neighbor_iterator(size):
                        if self.neighbor[x][y] != -1:
                            self.neighbor[-1][size*2 - 1] = self.neighbor[x][y]
                    for (x, y) in y_neighbor_iterator(size):
                        if self.neighbor[x][y] == -1:
                            self.neighbor[x][y] = self.neighbor[x][y + 1]
                    for (x, y) in x_neighbor_iterator(size):
                        if self.neighbor[x][y] == -1:
                            self.neighbor[x][y] = self.neighbor[x - 1][y]

        if self.mode == IntraPredMode.INTRA_DC or size == 4:
            filter_flag = 0
        else:
            min_dist_ver_hor = min(abs(self.mode - 26), abs(self.mode - 10))
            if size == 8:
                intra_hor_ver_dist_thres = 7
            elif size == 16:
                intra_hor_ver_dist_thres = 1
            elif size == 32:
                intra_hor_ver_dist_thres = 0
            else:
                raise
            if min_dist_ver_hor > intra_hor_ver_dist_thres:
                filter_flag = 1
            else:
                filter_flag = 0
            if filter_flag == 1:
                pf = utils.md_dict()
                if self.cu.ctx.sps.strong_intra_smoothing_enabled_flag == 1 and size == 32 and \
                        abs(self.neighbor[-1][-1] + self.neighbor[size*2-1][-1] - 2*self.neighbor[size-1][-1]) < (1 << (bit_depth_y - 5)) and \
                        abs(self.neighbor[-1][-1] + self.neighbor[-1][size*2-1] - 2*self.neighbor[-1][size-1]) < (1 << (bit_depth_y - 5)):
                    bi_int_flag = 1
                else:
                    bi_int_flag = 0
                if bi_int_flag == 1:
                    pf[-1][-1] = self.neighbor[-1][-1]
                    for y in range(0, 62+1):
                        pf[-1][y] = ((63-y)*self.neighbor[-1][-1] + (y+1)*self.neighbor[-1][63] + 32) >> 6
                    pf[-1][63] = self.neighbor[-1][63]
                    for x in range(0, 62+1):
                        pf[x][-1] = ((63-x)*self.neighbor[-1][-1] + (x+1)*self.neighbor[63][-1] + 32) >> 6
                    pf[63][-1] = self.neighbor[63][-1]
                else:
                    pf[-1][-1] = (self.neighbor[-1][0] + 2*self.neighbor[-1][-1] + self.neighbor[0][-1] + 2) >> 2
                    for y in range(0, size*2-2+1):
                        pf[-1][y] = (self.neighbor[-1][y+1] + 2*self.neighbor[-1][y] + self.neighbor[-1][y-1] + 2) >> 2
                    pf[-1][size*2-1] = self.neighbor[-1][size*2-1]
                    for x in range(0, size*2-2+1):
                        pf[x][-1] = (self.neighbor[x-1][-1] + 2*self.neighbor[x][-1] + self.neighbor[x+1][-1] + 2) >> 2
                    pf[size*2-1][-1] = self.neighbor[size*2-1][-1]
                self.neighbor = pf

    def decode_intra_planar(self):
        raise

    def decode_intra_dc(self):
        raise
