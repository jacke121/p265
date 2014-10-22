import utils

class IntraPu:
    def __init__(self, cu, c_idx):
        self.cu = cu
        self.c_idx = c_idx

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
        self.filter_neighbor()
        self.decode_prediction_samples()
        self.scaling_process()
        self.transformation_process()
        self.reconstruction_process()

    def decode_neighbor(self, x0, y0, log2size, depth):
        size = 1 << log2size
        self.neighbor = utils.md_dict()

        x = -1
        for y in range(-1, size*2-1, 1):
            self.neighbor[x][y] = -1

        y = -1
        for x in range(0, size*2-1, 1):
            self.neighbor[x][y] = -1

        x_current, y_current = x0, y0
        
        def derive_neighbor():
            x_neighbor, y_neighbor = x_current + x, y_current + y
            if self.c_idx > 0:
                x_neighbor, y_neighbor = x_neighbor << 1, y_neighbor << 1
                x_current, y_current = x_current << 1, y_current << 1
            
            available = self.cu.ctx.img.check_availability(x_current, y_current, x_neighbor, y_neighbor)
            if available == False or (self.cu.ctx.img.get("pred_mode", x_neighbor, y_neighbor) != self.cu.MODE_INTRA and self.cu.ctx.pps.constrained_intra_pred_flag == 1):
                pass
            else:
                self.neighbor[x][y] = self.cu.ctx.img.get_sample(x_neighbor, y_neighbor)

        x = -1
        for y in range(-1, size*2-1, 1):
            derive_neighbor()

        y = -1
        for x in range(0, size*2-1, 1):
            derive_neighbor()
        
        substitute_enable = 0

        x = -1
        for y in range(-1, size*2-1, 1):
            if self.neighbor[x][y] == -1:
                substitute_enable = 1

        y = -1
        for x in range(0, size*2-1, 1):
            if self.neighbor[x][y] == -1:
                substitute_enable = 1

        if substitute_enable == 1:
            bit_depth = self.cu.ctx.img.slice_hdr.bit_depth_y if self.c_idx == 0 else self.cu.ctx.img.slice_hdr.bit_depth_c

