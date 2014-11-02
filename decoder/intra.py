import utils
import copy
import numpy
import scaling
import transform
import reconstruction
import log

class IntraPredMode:
    INTRA_PLANAR = 0
    INTRA_DC = 1
    INTRA_ANGULAR = 2

class IntraPu:
    def __init__(self, cu, c_idx, mode, log2size, x, y):
        self.cu = cu
        self.c_idx = c_idx
        self.mode = mode

        self.origin_x = x
        self.origin_y = y

        size = 1 << log2size
        self.predicted_samples = numpy.zeros((size, size), int)
        self.scaled_samples = numpy.zeros((size, size), int)
        self.transformed_samples = numpy.zeros((size, size), int)
        self.reconstructed_samples = numpy.zeros((size, size), int)

    def decode(self, x, y, log2size, depth):
        split_transform_flag = self.cu.tu.get_split_transform_flag(x, y, depth)
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
    
    def decode_leaf(self, x0, y0, log2size, depth):
        size = 1 << log2size

        self.decode_pred_samples(x0, y0, log2size, depth)
        scaling.inverse_scaling(pu=self, x0=x0, y0=y0, log2size=log2size)
        transform.inverse_transform(pu=self, x0=x0, y0=y0, log2size=log2size)
        reconstruction.reconstruction(pu=self, x0=x0, y0=y0, log2size=log2size)

    def decode_pred_samples(self, x0, y0, log2size, depth):
        neighbors = self.decode_neighbor(x0, y0, log2size, depth)

        if self.mode == IntraPredMode.INTRA_PLANAR:
            self.decode_intra_planar(neighbors, x0, y0, log2size)
        elif self.mode == IntraPredMode.INTRA_DC:
            self.decode_intra_dc(neighbors, x0, y0, log2size)
        else:
            self.decode_intra_angular(neighbors, x0, y0, log2size)

    def decode_intra_planar(self, neighbors, x0, y0, log2size):
        size = 1 << log2size

        start_x = x0 - self.origin_x
        start_y = y0 - self.origin_y
        samples = self.predicted_samples[start_x:(start_x+size), start_y:(start_y+size)]

        for x in range(0, size):
            for y in range(0, size):
                samples[x][y] = ((size-1-x)*neighbors[-1][y] + \
                                           (x+1)*neighbors[size][-1] + \
                                           (size-1-y)*neighbors[x][-1] + \
                                           (y+1)*neighbors[-1][size] + size) >>  (log2size + 1)

    def decode_intra_dc(self, neighbors, x0, y0, log2size):
        size = 1 << log2size

        start_x = x0 - self.origin_x
        start_y = y0 - self.origin_y
        samples = self.predicted_samples[start_x:(start_x+size), start_y:(start_y+size)]

        dc_val = size
        for x in range(0, size):
            dc_val += neighbors[x][-1]
        for y in range(0, size):
            dc_val += neighbors[-1][y]
        dc_val = dc_val >> (log2size + 1)

        if self.c_idx == 0 and size < 32:
            samples[0][0] = (neighbors[-1][0] + 2 * dc_val + neighbors[0][-1] + 2) >> 2
            for x in range(1, size):
                samples[x][0] = (neighbors[x][-1] + 3 * dc_val + 2) >> 2
            for y in range(1, size):
                samples[0][y] = (neighbors[-1][y] + 3 * dc_val + 2) >> 2
            for x in range(1, size):
                for y in range(1, size):
                    samples[x][y] = dc_val
        else:
            for x in range(0, size):
                for y in range(0, size):
                    samples[x][y] = dc_val

    def decode_intra_angular(self, neighbors, x0, y0, log2size):
        size = 1 << log2size

        start_x = x0 - self.origin_x
        start_y = y0 - self.origin_y
        samples = self.predicted_samples[start_x:(start_x+size), start_y:(start_y+size)]

        if self.mode >= 18:
            ref = {}
            for x in range(0,size + 1):
                ref[x] = neighbors[-1 + x][-1]

            if pred_angle < 0:
                if ((size * pred_angle) >> 5) < -1:
                    for x in range((size * pred_angle) >> 5, -1 + 1):
                        ref[x] = neighbors[-1][-1 + ((x * inv_angle) >> 8)]
            else:
                for x in range(size + 1, 2 * size + 1):
                    ref[x] = neighbors[-1 + x][-1]

            for x in range(0, size):
                for y in range(0, size):
                    idx = ((y + 1) * pred_angle) >> 5
                    fact = ((y + 1) * pred_angle) & 31
                    if fact == 0:
                        self.pred_smaples[x][y] = ((32 - fact) * ref[x + idx + 1] + fact * ref[x + idx + 2] + 16) >> 5
                    else:
                        samples[x][y] = ref[x + idx + 1]
                    if x == 0 and self.mode == 26 and self.c_idx == 0 and size < 32:
                        samples[x][y] = utils.clip1y(neighbors[x][-1] + ((neighbors[-1][y] - neighbors[-1][-1]) >> 1))
        else:
            ref = {}
            for x in range(0, size + 1):
                ref[x] = neighbors[-1][-1 + x]
            if pred_angle < 0:
                if ((size * pred_angle) >> 5) < -1:
                    for x in range((size * pred_angle) >> 5, -1 + 1):
                        ref[x] = neighbors[-1 + ((x * inv_angle + 128) >> 8)][-1]
            else:
                for x in range(size + 1, 2 * size + 1):
                    ref[x] = neighbors[-1][-1 + x]

            for x in range(0, size):
                for y in range(0, size):
                    idx = ((x + 1) * pred_angle) >> 5
                    fact = ((x + 1) * pred_angle) & 31

                    if fact != 0:
                        samples[x][y] = ((32 - fact) * ref[y + idx + 1] + fact * ref[y + idx + 2] + 16) >> 5
                    else:
                        samples[x][y] = ref[y+ idx + 1]

                    if y ==0 and self.mode == 10 and self.c_idx == 0 and size < 32:
                        samples[x][y] = utils.clip1y(neighbors[-1][y] + (neighbors[x][-1] - neighbors[-1][-1]) >> 1)

    def decode_neighbor(self, x0, y0, log2size, depth):
        size = 1 << log2size
        
        # Neighbor interators
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
        
        # Initialize neighbor pixels as -1
        neighbors = utils.md_dict()
        for (x, y) in xy_neighbor_iterator(size):
            neighbors[x][y] = -1

        x_current, y_current = x0, y0
        for (x, y) in xy_neighbor_iterator(size):
            x_neighbor, y_neighbor = x_current + x, y_current + y
            if self.c_idx > 0:
                x_neighbor, y_neighbor = x_neighbor << 1, y_neighbor << 1
                x_current, y_current = x_current << 1, y_current << 1
            
            available = self.cu.ctx.img.check_availability(x_current, y_current, x_neighbor, y_neighbor)
            if available == False or (self.cu.get_root().get_pred_mode(x_neighbor, y_neighbor) != self.cu.MODE_INTRA and self.cu.ctx.pps.constrained_intra_pred_flag == 1):
                pass
            else:
                neighbor_ctu = self.cu.ctx.img.get_ctu(x_neighbor, y_neighbor)
                neighbors[x][y] = neighbor_ctu.get_reconstructed_sample(x_neighbor, y_neighbor)
        
        # Substitution process
        substitute_enable = 0
        no_available_neighbors = 1
        for (x, y) in xy_neighbor_iterator(size):
            if neighbors[x][y] == -1:
                substitute_enable = 1
            else:
                no_available_neighbors = 0
        if substitute_enable == 1:
            bit_depth = self.cu.ctx.sps.bit_depth_y if self.c_idx == 0 else self.cu.ctx.sps.bit_depth_c
            if no_available_neighbors == 1:
                for (x, y) in xy_neighbor_iterator(size):
                    neighbors[x][y] = 1 << (bit_depth - 1)
            else:
                if neighbors[-1][size*2 - 1] == -1:
                    for (x, y) in xy_neighbor_iterator(size):
                        if neighbors[x][y] != -1:
                            neighbors[-1][size*2 - 1] = neighbors[x][y]
                    for (x, y) in y_neighbor_iterator(size):
                        if neighbors[x][y] == -1:
                            neighbors[x][y] = neighbors[x][y + 1]
                    for (x, y) in x_neighbor_iterator(size):
                        if neighbors[x][y] == -1:
                            neighbors[x][y] = neighbors[x - 1][y]

        # Filtering process
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
                        abs(neighbors[-1][-1] + neighbors[size*2-1][-1] - 2*neighbors[size-1][-1]) < (1 << (bit_depth_y - 5)) and \
                        abs(neighbors[-1][-1] + neighbors[-1][size*2-1] - 2*neighbors[-1][size-1]) < (1 << (bit_depth_y - 5)):
                    bi_int_flag = 1
                else:
                    bi_int_flag = 0
                if bi_int_flag == 1:
                    pf[-1][-1] = neighbors[-1][-1]
                    for y in range(0, 62+1):
                        pf[-1][y] = ((63-y)*neighbors[-1][-1] + (y+1)*neighbors[-1][63] + 32) >> 6
                    pf[-1][63] = neighbors[-1][63]
                    for x in range(0, 62+1):
                        pf[x][-1] = ((63-x)*neighbors[-1][-1] + (x+1)*neighbors[63][-1] + 32) >> 6
                    pf[63][-1] = neighbors[63][-1]
                else:
                    pf[-1][-1] = (neighbors[-1][0] + 2*neighbors[-1][-1] + neighbors[0][-1] + 2) >> 2
                    for y in range(0, size*2-2+1):
                        pf[-1][y] = (neighbors[-1][y+1] + 2*neighbors[-1][y] + neighbors[-1][y-1] + 2) >> 2
                    pf[-1][size*2-1] = neighbors[-1][size*2-1]
                    for x in range(0, size*2-2+1):
                        pf[x][-1] = (neighbors[x-1][-1] + 2*neighbors[x][-1] + neighbors[x+1][-1] + 2) >> 2
                    pf[size*2-1][-1] = neighbors[size*2-1][-1]
                neighbors = pf
        
        return neighbors

