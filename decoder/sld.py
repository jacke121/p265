import numpy

class ScalingListData:
    default_scaling_list_4x4 = [
      16,16,16,16,
      16,16,16,16,
      16,16,16,16,
      16,16,16,16
    ]
    
    default_scaling_list_8x8_intra = [
      16,16,16,16,16,16,16,16,
      16,16,17,16,17,16,17,18,
      17,18,18,17,18,21,19,20,
      21,20,19,21,24,22,22,24,
      24,22,22,24,25,25,27,30,
      27,25,25,29,31,35,35,31,
      29,36,41,44,41,36,47,54,
      54,47,65,70,65,88,88,115
    ]
    
    default_scaling_list_8x8_inter = [
      16,16,16,16,16,16,16,16,
      16,16,17,17,17,17,17,18,
      18,18,18,18,18,20,20,20,
      20,20,20,20,24,24,24,24,
      24,24,24,24,25,25,25,25,
      25,25,25,28,28,28,28,28,
      28,33,33,33,33,33,41,41,
      41,41,54,54,54,71,71,91
    ]
    
    default_scaling_list = numpy.zeros((4, 6, 64), int)

    for size_id in [0]: # 4x4
        for matrix_id in range(0, 6):
            for i in range(0, 16):
                default_scaling_list[0][matrix_id][i] = default_scaling_list_4x4[i]

    for size_id in [1, 2]: # 8x8, 16x16
        for matrix_id in [0, 1, 2]: # intra y/cb/cr
            for i in range(0, 64):
                default_scaling_list[size_id][matrix_id][i] = default_scaling_list_8x8_intra[i]

    for size_id in [1, 2]: # 8x8, 16x16
        for matrix_id in [3, 4, 5]: # inter y/cb/cr
            for i in range(0, 64):
                default_scaling_list[size_id][matrix_id][i] = default_scaling_list_8x8_inter[i]

    for size_id in [3]: # 32x32
        for matrix_id in [0]: # intra y
            for i in range(0, 64):
                default_scaling_list[size_id][matrix_id][i] = default_scaling_list_8x8_intra[i]

    for size_id in [3]: # 32x32
        for matrix_id in [1]: # inter y
            for i in range(0, 64):
                default_scaling_list[size_id][matrix_id][i] = default_scaling_list_8x8_inter[i]

    def __init__(self, bs):
        self.bs = bs

    def decode(self):
        self.scaling_list_pred_mode_flag = [0] * 4
        self.scaling_list_pred_matrix_id_delta = [0] * 4
        self.scaling_list_dc_coef_minus8 = [0] * 2
        self.scaling_list_delta_coef = [0] * 4
        self.scaling_list = [0] * 4
        
        # size_id = [0, 1, 2, 3] = ['4x4', '8x8', '16x16', '32x32']
        for size_id in range(0, 4):
            matrix_num = 2 if size_id==3 else 6
            self.scaling_list_pred_mode_flag[size_id] = [0] * matrix_num
            self.scaling_list_pred_matrix_id_delta[size_id] = [0] * matrix_num
            if (size_id > 1):
                self.scaling_list_dc_coef_minus8[size_id-2] = [0] * matrix_num
            self.scaling_list_delta_coef[size_id] = [0] * matrix_num
            self.scaling_list[size_id] = [0] * matrix_num

            for matrix_id in range(0, matrix_num):
                self.scaling_list_pred_mode_flag[size_id][matrix_id] = self.bs.u(1, "scaling_list_pred_mode_flag[%d][%d]" % (size_id, matrix_id))
                if self.scaling_list_pred_mode_flag[size_id][matrix_id] == 0:
                    # The scaling list are the same as a reference scaling list.
                    self.scaling_list_pred_matrix_id_delta[size_id][matrix_id] = self.bs.ue("scaling_list_pred_matrix_id_delta[%d][%d]" % (size_id, matrix_id))
                    if self.scaling_list_pred_matrix_ic_delta[size_id][matrix_id] == 0:
                        for i in range(0, min(63, (1 << (4 + (size_id << 1))) - 1) + 1):
                            self.scaling_list[size_id][matrix_id][i] = self.default_scaling_list[size_id][matrix_id][i]
                    else:
                        ref_matrix_id = matrix_id - self.self.scaling_list_pred_matrix_ic_delta[size_id][matrix_id]
                        for i in range(0, min(63, (1 << (4 + (size_id << 1))) - 1) + 1):
                            self.scaling_list[size_id][matrix_id][i] = self.scaling_list[size_id][ref_matrix_id][i]

                    if size_id > 1:
                        if self.scaling_list_pred_matrix_ic_delta[size_id][matrix_id] == 0:
                            self.scaling_list_dc_coef_minus8[size_id-2][matrix_id] = 8
                        else:
                            self.scaling_list_dc_coef_minus8[size_id-2][ref_matrix_id]
                else:
                    # The scaling list are explicitly signaled in the syntax elements
                    next_coef = 8
                    coef_num = math.min(64, 1 << (4 + (size_id << 1)))
                    if size_id > 1:
                        self.scaling_list_dc_coef_minus8[size_id-2][matrix_id] = self.bs.se("scaling_list_dc_coef_minus8[%d][%d]" % (size_id-2, matrix_id))
                        assert self.scaling_list_dc_coef_minus8[size_id-2][matrix_id] in range(-7, 247+1)
                        next_coef = scaling_list_dc_coef_minus8[size_id-2][matrix_id] + 8

                    self.scaling_list_delta_coef[size_id][matrix_id] = [0] * coef_num
                    self.scaling_list[size_id][matrix_id] = [0] * coef_num
                    for i in range(0, coef_num):
                        self.scaling_list_delta_coef[size_id][matrix_id][i] = self.bs.se("scaling_list_delta_coef[%d][%d][%d]" % (size_id, matrix_id, i))
                        assert self.scaling_list_delta_coef[size_id][matrix_id][i] in range(-128, 127+1)
                        next_coef = (next_coef + self.scaling_list_delta_coef[size_id][matrix_id][i] + 256) % 256
                        self.scaling_list[size_id][matrix_id][i] = next_coef
                        assert self.scaling_list[size_id][matrix_id][i] > 0
