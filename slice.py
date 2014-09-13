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

        self.ctb_addr_rs = self.slice_header.slice_segment_address

        while True:
            self.parse_coding_tree_unit()
            raise "Intentional Stop."

    def parse_coding_tree_unit(self):
        self.x_ctb = self.ctb_addr_rs % self.sps.pic_width_in_ctbs_y
        self.y_ctb = self.ctb_addr_rs / self.sps.pic_width_in_ctbs_y

        self.x_ctb_pixels = self.x_ctb << self.sps.ctb_log2_size_y
        self.y_ctb_pixels = self.y_ctb << self.sps.ctb_log2_size_y

        self.ctb = ctb.Ctb(self.x_ctb_pixels, self.y_ctb_pixels, self.sps)
        self.ctb.slice_addr = self.slice_header.slice_segment_address

        if self.slice_header.slice_sao_luma_flag or self.slice_header.slice_sao_chroma_flag:
            raise "Unsupported yet."
        
        self.parse_coding_quadtree(self.x_ctb_pixels, self.y_ctb_pixels, self.sps.ctb_log2_size_y, 0)

        # should return a CTU

    def parse_coding_quadtree(self, x0, y0, log2_ctb_size, cqt_depth):
        if (x0 + (1 << log2_ctb_size)) <= self.sps.pic_width_in_luma_samples and \
           (y0 + (1 << log2_ctb_size)) <= self.sps.pic_height_in_luma_samples and \
           log2_ctb_size > self.sps.min_cb_log2_size_y:
            split_cu_flag

        pass

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
