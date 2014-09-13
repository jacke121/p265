import math
class Cb:
    def __init__(self):
        self.cqt_depth = 0
        self.addr = 0

class Ctb:
    def __init__(self, x_pixel, y_pixel, sps):
        self.sps = sps
        self.slice_addr = 0
        
        self.x_pixel = x_pixel
        self.y_pixel = y_pixel

        self.x_ctb = self.x_pixel >> self.sps.ctb_log2_size_y
        self.y_ctb = self.y_pixel >> self.sps.ctb_log2_size_y

        self.addr = self.x_ctb + self.y_ctb * self.sps.pic_width_in_ctbs_y

        self.init_min_cbs()

        self.dump()

    def init_min_cbs(self):
        self.min_cbs = {}

        (x_cb, y_cb) = self.get_min_cb_coordinate(self.x_pixel, self.y_pixel)
        width = 1 << (self.sps.ctb_log2_size_y - self.sps.min_cb_log2_size_y)

        for j in range(y_cb, y_cb+width):
            for i in range(x_cb, x_cb+width):
                min_cb_addr = i + j * self.sps.pic_width_in_min_cbs_y
                self.min_cbs[min_cb_addr] = Cb()

    def get_min_cb_coordinate(self, x_pixel, y_pixel):
        x_cb = x_pixel >> self.sps.min_cb_log2_size_y
        y_cb = y_pixel >> self.sps.min_cb_log2_size_y
        return (x_cb, y_cb)

    def get_min_cb_addr(self, x_pixel, y_pixel):
        (x_cb, y_cb) = self.get_min_cb_coordinate(x_pixel, y_pixel)
        return x_cb + y_cb * self.sps.pic_width_in_min_cbs_y

    def get_cqt_depth(self, x, y):
        addr = self.get_min_cb_addr(x, y)
        return self.min_cbs[addr].cqt_depth

    def set_cqt_depth(self, x, y, log2_size, cqt_depth):
        #if x < self.x_ctb_pixels or y < self.y_ctb_pixels:
        #    raise "(%d, %d) is not a valid coordinate for ctb_addr = %d" % (x, y, self.addr)
        
        x_cb = x >> self.sps.min_cb_log2_size_y
        y_cb = y >> self.sps.min_cb_log2_size_y
        print "x_cb, y_cb = ", (x_cb, y_cb)

        width = 1 << (log2_size - self.sps.min_cb_log2_size_y)
        print "width = ", width

        for j in range(y_cb, y_cb+width):
            for i in range(x_cb, x_cb+width):
                min_cb_addr = i + j * self.sps.pic_width_in_min_cbs_y
                print "%02x " % min_cb_addr,
                self.min_cbs[min_cb_addr].cqt_depth = cqt_depth  
            print ""


    def dump(self):
        print "ctb_size = ", self.sps.ctb_size_y
        print "min_cb_size = ", self.sps.min_cb_size_y
        print "pic_width_in_ctbs = ", self.sps.pic_width_in_ctbs_y
        print "pic_width_in_min_cbs = ", self.sps.pic_width_in_min_cbs_y
        

        for j in range(0, self.sps.pic_height_in_min_cbs_y):
            for i in range(0, self.sps.pic_width_in_min_cbs_y):
                print "%02x " % (i + j * self.sps.pic_width_in_min_cbs_y),
            print ""


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

    ctb1 = Ctb(64, 64, Sps(2, 16, 6, 3))
    if ctb1.addr != 3: raise 

    ctb1.set_cqt_depth(64, 64, 5, 1)
    ctb1.set_cqt_depth(0xc*8, 0xc*8, 4, 1)
