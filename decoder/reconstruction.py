import numpy
import utils

def reconstruction(pred_samples, residual_samples, log2size, c_idx, rec_samples):
    size = 1 << log2size

    if c_idx == 0:
        clip = utils.clip1_y
    else:
        clip = utils.clip1_c

    for i in range(0, size):
        for j in range(0, size):
            rec_samples[i][j] = clip(pred_samples[i][j] + residual_samples[i][j])

    return rec_samples
