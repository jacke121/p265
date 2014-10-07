class Tree:
    def __init__(self, x, y, log2size, depth=0, parent=None):
        self.x = x
        self.y = y
        self.log2size = log2size
        self.size = 1 << log2size # one of 64/32/16/8
        self.depth= depth# depth of root is 0, maximum depth of cb with size 64/32/16/8 is 3/2/1/0
        self.parent = parent
        self.children = [] # 4 children or no children for quad tree 
    
    def add_child(self, child=None):
        self.children.append(child) # In order appending
        assert len(self.children) <= 4

    def get_child(self, idx=0):
        assert idx >= 0 and idx <= 3
        self.children[idx]
    
    def is_root(self):
        return True if self.parent is None else False

    def is_leaf(self):
        return len(self.children) == 0

    def contain(self, x, y):
        x_flag = x >= self.x and x < (self.x + self.size)
        y_flag = y >= self.y and y < (self.y + self.size)
        return x_flag and y_flag

    def traverse(self):
        yield self
        for child in self.children:
            if child is not None:
                for i in child.traverse():
                    yield i

    def get_leaves(self):
        leaves = []
        for n in self.traverse():
            if n.is_leaf():
                leaves.append(n)
        return leaves

    def dump(self):
        print "%s%dx%d(%d)" % (' '*4*self.depth, self.x, self.y, self.size)
        for n in self.children:
            if n is not None:
                n.dump()

    def dump_leaves(self):
        if self.is_leaf():
            print "%dx%d(%d)" % (self.x, self.y, self.size)
        else:
            for n in self.children:
                if n is not None:
                    n.dump_leaves()

    def split(self, size, depth):
        if len(self.children) == 4: 
            raise ValueError("Already split.")
        cb = [None] * 4
        cb[0] = Cb(self.x, self.y, size, depth, self)
        cb[1] = Cb(self.x+size, self.y, size, depth, self)
        cb[2] = Cb(self.x, self.y+size, size, depth, self)
        cb[3] = Cb(self.x+size, self.y+size, size, depth, self)
        #if random.randint(0,1):
        #    not_exist_idx = random.randint(0,3)
        #    cb[not_exist_idx] = None
        for i in range(4):
            self.add_child(cb[i])

    def populate(self, max_depth):
        if self.depth > max_depth: 
            return
        self.split_cu_flag = random.randint(0, 1)
        if self.split_cu_flag == 1:
            self.split(self.size/2, self.depth + 1)
        for n in self.children:
            if n is not None:
                n.populate(max_depth)

    def __str__(self):
        a = [[' ' for i in range(self.size)] for j in range(self.size)]
        print "leaves = ", self.get_leaves()
        for n in self.get_leaves():
            print "%dx%d(%d)" % (n.x, n.y, n.size)
            x0 = n.x - self.x
            y0 = n.y - self.y
            for i in range(x0, x0+n.size):
                a[y0][i] = '-'
                a[y0+n.size-1][i] = '-'
            for i in range(y0, y0+n.size):
                a[i][x0] = '|'
                a[i][x0+n.size-1] = '|'

        s = ""
        for y in range(self.size):
            for x in range(self.size):
                s += a[y][x]
            s += "\n"
        return s

if __name__ == "__main__":
    ctb = Tree(0, 0, 64)
    ctb.populate(2)
    ctb.dump()
    ctb.dump_leaves()
    
    for i in ctb.traverse():
        print "%s%dx%d(%d)" % (' '*4*i.depth, i.x, i.y, i.size)
    
    cb0 = Tree(0, 0, 32)
    assert cb0.contain(31, 31) == True
    assert cb0.contain(32, 32) == False
    assert cb0.contain(1,2) == True
    print ctb
    exit()

