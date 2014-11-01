import cu
import sao
import log

class Ctu(cu.Cu):
    def __init__(self, ctx, addr_rs):
        x = (addr_rs % ctx.sps.pic_width_in_ctbs_y) << ctx.sps.ctb_log2_size_y
        y = (addr_rs / ctx.sps.pic_width_in_ctbs_y) << ctx.sps.ctb_log2_size_y
        cu.Cu.__init__(self, x, y, ctx.sps.ctb_log2_size_y, depth=0, parent=None)

        self.ctx = ctx

        self.slice_addr = 0
        self.sps = self.ctx.sps
        self.pps = self.ctx.pps
        self.addr_rs = addr_rs
        self.addr_ts = self.ctx.pps.ctb_addr_rs2ts[self.addr_rs]

        self.x_ctb = self.x >> self.ctx.sps.ctb_log2_size_y
        self.y_ctb = self.y >> self.ctx.sps.ctb_log2_size_y

        self.sao = sao.Sao(self.ctx)

    def parse(self):
        log.location.info("Start decoding CTU: (x, y) = (%d, %d), size = %d, addr_rs = %d", self.x, self.y, self.size, self.addr_rs)

        if self.ctx.img.slice_hdr.slice_sao_luma_flag or self.ctx.img.slice_hdr.slice_sao_chroma_flag:
            self.sao.parse()
        
        cu.Cu.parse(self)
        #print(self)

    def get_depth(self, x, y):
        assert self.contain(x, y)
        for leave in self.get_leaves():
            if leave.contain(x, y):
                return leave.depth

    def get_pred_mode(self, x, y):
        assert self.contain(x, y)
        for leave in self.get_leaves():
            if leave.contain(x, y):
                return leave.pred_mode

    def get_pcm_flag(self, x, y):
        assert self.contain(x, y)
        for leave in self.get_leaves():
            if leave.contain(x, y):
                return leave.pcm_flag

    def get_qp_y(self, x, y):
        assert self.contain(x, y)
        for leave in self.get_leaves():
            if leave.contain(x, y):
                return leave.qp_y
    
    def get_intra_pred_mode_y(self, x, y):
        assert self.contain(x, y)
        for leave in self.get_leaves():
            if leave.contain(x, y):
                x_pb = x - (x % leave.intra_pb_size)
                y_pb = y - (y % leave.intra_pb_size)
                return leave.intra_pred_mode_y[x_pb][y_pb]

    def is_first_ctb_in_tile(self):
        if self.ctx.sps.tiles_enabled_flag == 0:
            return self.x == 0 and self.y == 0
    
        for x in range(0, self.ctx.pps.num_tile_columns):
            if self.ctx.pps.column_boundary[x] == self.x:
                for y in range(0, self.ctx.pps.num_tile_rows):
                    if self.ctx.pps.row_boundary[k] == self.y:
                        return true
                return false
    
        return false;

if __name__ == "__main__":
    class Sps:
        def __init__(self, pic_width_in_ctbs, pic_width_in_min_cbs, ctb_log2_size, min_cb_log2_size):
            self.pic_width_in_ctbs_y = pic_width_in_ctbs
            self.pic_width_in_min_cbs_y = pic_width_in_min_cbs
            self.ctb_log2_size_y = ctb_log2_size
            self.min_cb_log2_size_y = min_cb_log2_size
            self.ctb_size_y = 1 << self.ctb_log2_size_y
            self.min_cb_size_y = 1 << self.min_cb_log2_size_y

            self.pic_height_in_ctbs_y = self.pic_width_in_ctbs_y
            self.pic_height_in_min_cbs_y = self.pic_width_in_min_cbs_y

    ctb1 = Ctb(addr=3, sps=Sps(2, 16, 6, 3))
    if ctb1.addr != 3: raise 

    ctb1.set_cqt_depth(64, 64, 5, 1)
    ctb1.set_cqt_depth(0xc*8, 0xc*8, 4, 1)
