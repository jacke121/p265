import numpy

def inverse_scaling(pu, x0, y0, log2size, depth, c_idx, d):
    size = 1 << log2size

    if c_idx == 0: 
        qp = pu.cu.qp_y + pu.cu.ctx.sps.qp_bd_offset_y
    elif c_idx == 1:
        qp = pu.cu.qp_cb + pu.cu.ctx.sps.qp_bd_offset_c
    else:
        qp = pu.cu.qp_cr + pu.cu.ctx.sps.qp_bd_offset_c

    if pu.cu.cu_transquant_bypass_flag == 1:
        raise ValueError("Unimplemented yet.")
    else:
        if c_idx == 0:
            bd_shift = pu.cu.ctx.sps.bit_depth_y + log2size - 5
        else:
            bd_shift = pu.cu.ctx.sps.bit_depth_c + log2size - 5

        level_scale = [40, 45, 51, 57, 64, 72]
        m = numpy.zeros((size, size), int)
        for x in range(0, size):
            for y in range(0, size):
                if pu.cu.ctx.sps.scaling_list_enabled_flag == 0:
                    m[x][y] = 16
                else:
                    size_id = log2size - 2
                    if size_id  == 3:
                        matrix_id = 0 if pu.cu.is_intra_mode() else 1
                    else:
                        if pu.cu.is_intra_mode():
                            matrix_id = c_idx
                        else:
                            matrix_id = c_idx + 3

                    m[x][y] = pu.cu.ctx.sps.scaling_factor[size_id][matrix_id][x][y]
                
                d[x][y] = (pu.cu.trans_coeff_level[x][y][c_idx][x][y] * m[x][y] * (level_scale[qp%6] << (qp/6))) + (1 << (bd_shift - 1))
                d[x][y] = utils.clip3(-32768, 32767, d[x][y] >> bd_shift)

        return d
