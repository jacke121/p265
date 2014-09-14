import math
import st_rps
import cabac
import ctb
import slice_hdr

class SliceData:
    def __init__(self, bs, naluh, slice_header, img):
        self.bs = bs
        self.naluh = naluh
        self.slice_header = slice_header
        self.img = img
        self.cabac = cabac.Cabac(bs)
        self.ctbs = {}

    def decode(self):
        self.vps = self.slice_header.vps
        self.sps = self.slice_header.sps
        self.pps = self.slice_header.pps

        if not self.slice_header.dependent_slice_segment_flag:
            self.cabac.initialize_context_models(self.slice_header)

        self.ctb_addr_in_raster_scan = self.slice_header.slice_segment_address

        while True:
            self.parse_coding_tree_unit()
            raise "Intentional Stop."

    def parse_coding_tree_unit(self):

        self.ctb = ctb.Ctb(self.ctb_addr_in_raster_scan, self.sps)
        self.ctb.slice_addr = self.slice_header.slice_segment_address

        if self.slice_header.slice_sao_luma_flag or self.slice_header.slice_sao_chroma_flag:
            self.decode_sao()
        
        self.parse_coding_quadtree(self.ctb.x_ctb, self.y_ctb, self.sps.ctb_log2_size_y, 0)

        # should return a CTU

    def decode_sao_merge_left_flag(self):
        pass

    def decode_sao_merge_up_flag(self):
        pass

    def decode_sao_type_idx_luma(self):
        pass

    def decode_sao_type_idx_chroma(self):
        pass
    
    def decode_sao_offset_abs(self):
        pass
    
    def decode_sao_offset_sign(self):
        pass

    def decode_sao(self):
        self.sao_merge_left_flag = 0
        if self.ctb.x_ctb > 0:
            left_ctb_in_slice_seg = self.ctb.addr > self.ctb.slice_addr
            left_ctb_in_tile =  self.pps.tile_id[self.ctb.addr_in_tile_scan] == \
                    self.pps.tile_id[self.pps.ctb_addr_rs2ts[self.ctb.addr_in_raster_scan-1]]
            if left_ctb_in_slice_seg and left_ctb_in_tile:
                self.sao_merge_left_flag = self.decode_sao_merge_left_flag()

        self.sao_merge_up_flag = 0
        if self.ctb.y_ctb > 0 and (not self.sao_merge_left_flag):
            up_ctb_in_slice_seg = (self.ctb.addr - self.sps.pic_width_in_ctbs_y) >= self.ctb.slice_addr
            up_ctb_in_tile = self.pps.tile_id[self.ctb.addr_in_tile_scan] == \
                    self.tile_id[self.pps.ctb_addr_rs2ts[self.ctb.addr_in_raster_scan - self.sps.pic_width_in_ctbs_y]]
            
            if up_ctb_in_slice_seg and up_ctb_in_tile:
                self.sao_merge_up_flag = self.decode_sao_merge_up_flag()
        
        sao_info = ctb.SaoInfo()
        if (not self.sao_merge_up_flag) and (not self.sao_merge_left_flag):
            for colorIdx in range(3):
                if (self.slice_hdr.slice_sao_luma_flag and colorIdx==0) or (self.slice_hdr.slice_sao_chroma_flag and colorIdx>0)
                    if colorIdx == 0:
                        self.sao_type_idx_luma == self.decode_sao_type_idx_luma()
                        sao_info.sao_type_idx[0] = self.sao_type_idx_luma
                    elif colorIdx == 1:
                        self.sao_type_idx_chroma == self.decode_sao_type_idx_chroma()
                        sao_info.sao_type_idx[1] = self.sao_type_idx_chroma
                        sao_info.sao_type_idx[2] = self.sao_type_idx_chroma
                   
                    if sao_info.sao_type_idx[colorIdx] != 0:
                        self.sao_offset_abs[colorIdx] = [0] * 4
                        for i in range(4):
                            self.sao_offset_abs[colorIdx][i] = self.decode_sao_offset_abs()

                        if sao_info.sao_type_idx[colorIdx] == 1:
                            for i in range(4):
                                if self.sao_offset_abs[colorIdx][i] != 0:
                                    self.sao_offset_sign[colorIdx][i] = self.decode_sao_offset_sign()
        else:
            for colorIdx in range(3):
                if self.sao_merge_left_flag:
                    sao_info.sao_type_idx[colorIdx] = self.ctbs[self.ctb.x_ctb-1][self.ctb.y_ctb].sao_info.sao_tpe_idx[colorIdx]
                elif self.sao_merge_up_flag:
                    sao_info.sao_type_idx[colorIdx] = self.ctbs[self.ctb.x_ctb][self.ctb.y_ctb-1].sao_info.sao_tpe_idx[colorIdx]
                else:
                    sao_info.sao_type_idx[colorIdx] = 0

            #TODO:add default values for sao_offset_abs and sao_offset_sign


    def parse_coding_quadtree(self, x0, y0, log2_ctb_size, cqt_depth):
        if (x0 + (1 << log2_ctb_size)) <= self.sps.pic_width_in_luma_samples and \
           (y0 + (1 << log2_ctb_size)) <= self.sps.pic_height_in_luma_samples and \
           log2_ctb_size > self.sps.min_cb_log2_size_y:
            split_cu_flag

        raise "Unimplemented yet." 

    def get_ctb_addr(self, x, y):
        ctb_x = x >> self.sps.log2_ctb_size_y;
        ctb_y = y >> self.sps.log2_ctb_size_y;
    
        return ctb_y * self.sps.pic_width_in_ctbs_y + ctb_x;

    def get_slice_addr_rs_from_ctb_addr_rs(self, ctb_addr_rs):
        if self.ctbs.has_key(ctb_addr_rs):
            return self.ctbs[ctb_addr_rs]["slice_addr"]
        else:
            return -1

    def check_ctb_availability(self, x_current, y_current, x_neighbor, y_neighbor):
        if x_neighbor < 0 or y_neighbor < 0: return 0
        
        if x_neighbor >= self.sps.pic_width_in_luma_samples:  return 0
        if y_neighbor >= self.sps.pic_height_in_luma_samples: return 0

        current_ctb_addr_rs  = self.get_ctb_addr_rs_from_luma_position(x_current, y_current);
        neighbor_ctb_addr_rs = self.get_ctb_addr_rs_from_luma_position(x_neighbor, y_neighbor);

        # TODO: check if this is correct (6.4.1)
        if self.get_slice_addr_rs_from_ctb_addr_rs(neighbor_ctb_addr_rs) == -1:
            return 0

        if self.pps.tiles_enabled_flag:
            raise "Unsupported yet."
        # check if both CTBs are in the same tile.
        #if (img->pps.TileIdRS[current_ctbAddrRS] !=
        #    img->pps.TileIdRS[neighbor_ctbAddrRS]) {
        #    return 0;
        #}

        return 1

    def set_cqt_depth(self, x, y, log2size, depth):
        ctb_addr = self.get_ctb_addr(x, y)
        return self.ctbs[ctb_addr].set_cqt_addr(x, y, log2size, depth)

    def get_cqt_depth(self, x, y):
        ctb_addr = self.get_ctb_addr(x, y)
        return self.ctbs[ctb_addr].get_cqt_addr(x, y)

    def decode_split_cu_flag(self, x0, y0, cqt_depth):
        availableL = self.check_availability(x0, y0, x0-1, y0)
        availableA = self.check_availability(x0, y0, x0, y0-1)

        condL = condA = 0
        if availableL and self.get_cqt_depth(x0-1, y0) > cqt_depth: condL = 1
        if availableA and self.get_cqt_depth(x0, y0-1) > cqt_depth: condA = 1

        context_offset= condL + condA
        context_idx = context_offset

        bit = self.cabac.decode_bin("split_cu_flag", context_idx, 0)
        return bit


class SliceSegment:
    def __init__(self, bs, naluh, vps, sps, pps, img):
        self.bs = bs
        self.slice_header = slice_hdr.SliceHeader(bs, naluh, vps, sps, pps, img)
        self.slice_data = SliceData(bs, naluh, self.slice_header, img)

    def decode(self):
        self.slice_header.decode()
        self.slice_data.decode()
