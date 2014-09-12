import math

class Ctb:
    def __init__(self, x_ctb_pixels, y_ctb_pixels, sps):
        self.sps = sps
        self.slice_addr = 0

        self.x_ctb_pixels = x_ctb_pixels
        self.y_ctb_pixels = y_ctb_pixels

        self.x_ctb = self.x_ctb_pixels >> self.sps.ctb_log2_size_y
        self.y_ctb = self.y_ctb_pixels >> self.sps.ctb_log2_size_y

        self.addr = self.x_ctb + self.y_ctb * self.sps.pic_width_in_ctbs_y

        self.ctb_width_in_min_cbs = self.sps.ctb_size_y / self.sps.min_cb_size_y
        self.min_cbs = [{}] * self.ctb_width_in_min_cbs * self.ctb_width_in_min_cbs

    def set_cqt_depth(self, x, y, log2_cb_size, cqt_depth):
        if x < self.x_ctb_pixels or y < self.y_ctb_pixels:
            raise "(%d, %d) is not a valid coordinate for ctb_addr = %d" % (x, y, self.addr)
        
        x_cb = x % self.sps.ctb_size_y
        y_cb = y % self.sps.ctb_size_y

        x_cb = x_cb >> log2_cb_size
        y_cb = y_cb >> log2_cb_size

        cb_addr = x_cb + y_cb * self.ctb_width_in_min_cbs
        print "cb_addr = ", cb_addr

        self.min_cbs[cb_addr]["cqt_depth"] = cqt_depth  

    def dump(self):
        print "(x_ctb_pixels, y_ctb_pixesl) = ", (self.x_ctb_pixels, self.y_ctb_pixels)
        print "(x_ctb, y_ctb) = ", (self.x_ctb, self.y_ctb)
        print "ctb_addr =", self.addr
        print "num_min_cbs = ", self.num_min_cbs

if __name__ == "__main__":
    class Sps:
        def __init__(self, pic_width_in_ctbs, ctb_log2_size, min_cb_log2_size):
            self.pic_width_in_ctbs_y = pic_width_in_ctbs
            self.ctb_log2_size_y = ctb_log2_size
            self.min_cb_log2_size_y = min_cb_log2_size
            self.ctb_size_y = 1 << self.ctb_log2_size_y
            self.min_cb_size_y = 1 << self.min_cb_log2_size_y

    ctb1 = Ctb(64, 64, Sps(2, 6, 3))
    if ctb1.addr != 3: raise 

    ctb1.set_cqt_depth(64, 64, 1)
    ctb1.set_cqt_depth(64+8, 64+8, 1)
