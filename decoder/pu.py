class IntraPu:
    def __init__(self, cu, x, y, log2size, depth, mode, c_idx):
        self.cu = cu
        self.x = x
        self.y = y
        self.log2size = log2size
        self.size = 1 << log2size
        self.depth = depth
        self.mode = mode
        self.c_idx = c_idx

    def decode(self, u):
        if self.c_idx == 0:
            split_flag = u.split_transform_flag
        else:
            if u.split_transform_flag == 1 and self.log2size > 2:
                split_flag = 1
            else:
                split_flag = 0

        if split_flag = 1:
            for child in u.children():
                self.decode(child)
        else:
            self.decode_leaf(u)

    def decode_leaf(self, u):
        size = u.size
        self.decode_neighbor()
        self.filter_neighbor()
        self.decode_prediction_samples()
        self.scaling_process()
        self.transformation_process()
        self.reconstruction_process()
