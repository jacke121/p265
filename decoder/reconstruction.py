import numpy
import utils

def reconstruction(pu, x0, y0, log2size):
    size = 1 << log2size

    bit_depth_y = pu.cu.ctx.sps.bit_depth_y
    bit_depth_c = pu.cu.ctx.sps.bit_depth_c

    if pu.c_idx == 0:
        clip = utils.clip1_y
        bit_depth = bit_depth_y
    else:
        clip = utils.clip1_c
        bit_depth = bit_depth_c

    start_x = x0 - pu.origin_x
    start_y = y0 - pu.origin_y
    predicted_samples = pu.predicted_samples[start_x:(start_x+size), start_y:(start_y+size)]
    transformed_samples = pu.transformed_samples[start_x:(start_x+size), start_y:(start_y+size)]
    reconstructed_samples = pu.reconstructed_samples[start_x:(start_x+size), start_y:(start_y+size)]

    for i in range(0, size):
        for j in range(0, size):
            reconstructed_samples[i][j] = clip(predicted_samples[i][j] + transformed_samples[i][j], bit_depth)

    return reconstructed_samples
