class ScalingListData:
    def __init__(self, bs):
        self.bs = bs

    def parse(self):
        self.scaling_list_pred_mode_flag = [0] * 4
        self.scaling_list_pred_matrix_id_delta = [0] * 4
        self.scaling_list_dc_coef_minus8 = [0] * 2
        self.ScalingList = [0] * 4
        self.scaling_list_delta_coef = [0] * 4

        for sizeId in range(0, 4):

            self.scaling_list_pred_mode_flag[sizeId] = [0] * (2 if sizeId==3 else 6)
            self.scaling_list_pred_matrix_id_delta[sizeId] = [0] * (2 if sizeId==3 else 6)
            if (sizeId > 1):
                self.scaling_list_dc_coef_minus8[sizeId-2] = [0] * (2 if sizeId==3 else 6)
            self.ScalingList[sizeId] = [0] * (2 if sizeId==3 else 6)
            self.scaling_list_delta_coef[sizeId] = [0] * (2 if sizeId==3 else 6)

            for matrixId in range(0, 2 if sizeId==3 else 6):
                self.scaling_list_pred_mode_flag[sizeId][matrixId] = self.bs.u(1, "scaling_list_pred_mode_flag[%d][%d]" % (sizeId, matrixId))
                if not self.scaling_list_pred_mode_flag[sizeId][matrixId]:
                    self.scaling_list_pred_matrix_id_delta[sizeId][matrixId] = self.bs.ue("scaling_list_pred_matrix_id_delta[%d][%d]" % (sizeId, matrixId))
                else:
                    nextCoef = 8
                    coefNum = math.min(64, 1 << (4 + (sizeId << 1)))
                    if sizeId > 1:
                        self.scaling_list_dc_coef_minus8[sizeId-2][matrixId] = self.bs.se("scaling_list_dc_coef_minus8[%d][%d]" % (sizeId-2, matrixId))
                        nextCoef = scaling_list_dc_coef_minus8[sizeId-2][matrixId] + 8

                    self.scaling_list_delta_coef[sizeId][matrixId] = [0] * coefNum
                    self.ScalingList[sizeId][matrixId] = [0] * coefNum
                    for i in range(0, coefNum):
                        self.scaling_list_delta_coef[sizeId][matrixId][i] = self.bs.se("scaling_list_delta_coef[%d][%d][%d]" % (sizeId, matrixId, i))
                        nextCoef = (nextCoef + self.scaling_list_delta_coef[sizeId][matrixId][i] + 256) % 256
                        ScalingList[sizeId][matrixId][i] = nextCoef

