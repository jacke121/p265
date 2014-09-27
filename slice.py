import copy
import math
import st_rps
import cabac
import ctb
import slice_hdr

import logging
log = logging.getLogger(__name__)

class SliceSegment:
    def __init__(self, ctx):
        self.ctx = ctx
        self.slice_hdr = slice_hdr.SliceHeader(self.ctx)
        self.slice_data = SliceData(self.ctx)

    def decode(self):
        self.slice_hdr.decode()
        self.ctx.img.slice_hdrs.append(copy.deepcopy(self.slice_hdr))
        self.slice_data.decode()

class SliceData:
    def __init__(self, ctx):
        self.ctx = ctx
        self.bs = self.ctx.bs

        self.vps = self.ctx.vps
        self.sps = self.ctx.sps
        self.pps = self.ctx.pps

        self.cabac = self.ctx.cabac

    def decode(self):
        bs = self.bs

        log.info("============= Slice Segment Data =============")

        if not self.ctx.img.slice_hdrs[-1].dependent_slice_segment_flag:
            self.ctx.img.slice_hdr = self.ctx.img.slice_hdrs[-1]
            self.cabac.initialize_context_models(self.ctx.img.slice_hdr)
            self.cabac.initialization_process_arithmetic_decoding_engine()
        else:
            for hdr in reversed(self.ctx.img.slice_hdrs):
                if not hdr.dependent_slice_segment_flag:
                    self.ctx.img.slice_hdr = hdr
                    break

        self.ctx.img.ctb.slice_addr = self.ctx.img.slice_hdr.slice_segment_address 

        while True:
            self.ctx.img.ctb.parse_coding_tree_unit()
            raise "The first CTU is parsed!"

            self.decode_end_of_slice_segment_flag()
            self.ctx.img.next_ctb() # Switching to next CTB
            
            switching_tile_flag = self.ctx.pps.tiles_enabled_flag and (self.ctx.pps.tile_id[self.ctx.img.ctb.addr_ts] != self.ctx.pps.tile_id[self.ctx.img.ctb.addr_ts - 1])
            if (not self.end_of_slice_segment_flag) and (switching_tile_flag or (self.ctx.pps.entropy_coding_sync_enabled_flag and (self.ctx.img.ctb.addr_ts % self.ctx.sps.pic_width_in_ctbs_y))):
                self.decode_end_of_sub_stream_one_bit()
                self.ctx.bs.byte_alignment()
            else:
                break

    def decode_end_of_slice_segment_flag(self):
        pass

    def decode_end_of_sub_stream_one_bit(self):
        pass
