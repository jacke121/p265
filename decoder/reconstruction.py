import numpy
import utils

def reconstruction(pred_samples, residual_samples, log2size, c_idx, rec_samples, bit_depth_y, bit_depth_c):
    size = 1 << log2size

    if c_idx == 0:
        clip = utils.clip1_y
        bit_depth = bit_depth_y
    else:
        clip = utils.clip1_c
        bit_depth = bit_depth_c

    for i in range(0, size):
        for j in range(0, size):
            rec_samples[i][j] = clip(pred_samples[i][j] + residual_samples[i][j], bit_depth)

    return rec_samples
