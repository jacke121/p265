import bsb
import image
import dpb
import cabac

MAX_VPS_COUNT = 16
MAX_SPS_COUNT = 32
MAX_PPS_COUNT = 256

class Context:
    def __init__(self, bs_file = "str.bin"):
        self.bs = bsb.BitStreamBuffer(bs_file)

        self.img = image.Image(self) # The current image being decoded
        self.dpb = dpb.Dpb() # Decoded picture buffer

        self.vps_list = [None] * MAX_VPS_COUNT
        self.sps_list = [None] * MAX_SPS_COUNT
        self.pps_list = [None] * MAX_PPS_COUNT
        self.vps = None # Active vps
        self.sps = None # Active sps
        self.pps = None # Active pps

        self.naluh = None # Active nalu header

        self.cabac = cabac.Cabac(self.bs)

