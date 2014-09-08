class ShortTermRefPicSet:
    def __init__(self, bs):
        self.bs = bs

    def parse(self, stRpsIdx, num_short_term_ref_pic_sets):
        if stRpsIdx != 0:
            self.inter_ref_pic_set_prediction_flag = self.bs.u(1, "inter_ref_pic_set_prediction_flag")
        else:
            self.inter_ref_pic_set_prediction_flag = 0

        if self.inter_ref_pic_set_prediction_flag:
            raise "Not implemented yet"

            if stRpsIdx == num_short_term_ref_pic_sets:
                self.delta_idx_minus1 = self.bs.ue("")

            self.delta_rps_sign = self.bs.u(1, "")
            self.abs_delta_rps_minus1 = self.bs.ue("")
            #...
        else:
            self.num_negative_pics = self.bs.ue("num_negative_pics")
            self.num_positive_pics = self.bs.ue("num_positive_pics")

            self.delta_poc_s0_minus1 = [0] * self.num_negative_pics
            self.used_by_curr_pic_s0_flag = [0] * self.num_negative_pics
            self.delta_poc_s0 = [0] * self.num_negative_pics

            for i in range(0, self.num_negative_pics):
                self.delta_poc_s0_minus1[i] = self.bs.ue("delta_poc_s0_minus1[%d]" % i)
                self.used_by_curr_pic_s0_flag[i] = self.bs.u(1, "used_by_curr_pic_s0_flag[%d]" % i)

                if i == 0:
                    self.delta_poc_s0[i] = -(self.delta_poc_s0_minus1[i] + 1)
                else:
                    self.delta_poc_s0[i] = self.delta_poc_s0[i-1] - (self.delta_poc_s0_minus1[i] + 1)

            self.delta_poc_s1_minus1 = [0] * self.num_positive_pics
            self.used_by_curr_pic_s1_flag = [0] * self.num_positive_pics
            self.delta_poc_s1 = [0] * self.num_positive_pics

            for i in range(0, self.num_positive_pics):
                self.delta_poc_s1_minus1[i] = self.bs.ue("delta_poc_s1_minus1[%d]" % i)
                self.used_by_curr_pic_s1_flag[i] = self.bs.u(1, "used_by_curr_pic_s1_flag[%d]" % i)


                if i == 0:
                    self.delta_poc_s1[i] = self.delta_poc_s0_minus1[i] + 1
                else:
                    self.delta_poc_s0[i] = self.delta_poc_s0[i-1] + (self.delta_poc_s0_minus1[i] + 1)

            self.num_delta_pocs = self.num_negative_pics + self.num_positive_pics

