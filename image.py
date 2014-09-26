import ctb

class Image:
    def __init__(self, ctx):
        self.ctx = ctx
        self.slice_hdrs = [] 
        self.slice_hdr = None

        self.ctb = None
        self.ctbs = {}
    
    def next_ctb(self):
        assert self.ctb.addr_rs not in self.ctb
        self.ctbs[self.ctb.addr_rs] = self.ctb # Save the previously decoded CTB
        self.ctb = ctb.Ctb(self.ctx, self.ctx.pps.ctb_addr_ts2rs[self.ctb.addr_ts + 1]) # Create a new CTB instance
