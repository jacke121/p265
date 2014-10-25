import random
import matplotlib.patches as patches
import matplotlib.pyplot as plt

class Tree:
    def __init__(self, x, y, log2size, depth=0, parent=None):
        self.x = x
        self.y = y
        self.log2size = log2size
        self.size = 1 << log2size
        self.depth= depth
        self.parent = parent
        self.children = []
    
    def add_child(self, child=None):
        self.children.append(child) # In order appending
        assert len(self.children) <= 4

    def get_child(self, idx=0):
        assert idx >= 0 and idx <= 3
        self.children[idx]

    def get_idx(self):
        if self.parent is None:
            return 0
        else:
            for i in range(4):
                if self.parent.children[i] == self:
                    return i
    
    def is_root(self):
        return True if self.parent is None else False

    def is_leaf(self):
        return len(self.children) == 0

    def get_root(self):
        if self.parent is None:
            return self
        else:
            self.parent.get_root()

    def contain(self, x, y):
        x_flag = x >= self.x and x < (self.x + self.size)
        y_flag = y >= self.y and y < (self.y + self.size)
        return x_flag and y_flag

    def traverse(self, strategy = "depth-first"):
        if strategy == "depth-first":
            yield self
            for child in self.children:
                if child is not None:
                    for i in child.traverse():
                        yield i
        elif strategy == "breath-first":
            q = [self]
            while len(q) != 0:
                node = q.pop()
                yield node 
                for child in node.children:
                    q.insert(0, child)
        else:
            raise ValueError("Undefined tree traversing strategy.")

    def get_leaves(self):
        leaves = []
        for n in self.traverse():
            if n.is_leaf():
                leaves.append(n)
        return leaves
    
    def get_sisters(self):
        if self.parent is not None:
            return [node for node in self.parent.children if node != self]
        else:
            return []

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

    def split(self, log2size, depth):
        if len(self.children) == 4: 
            raise ValueError("Already split.")
        size = 1 << log2size
        t = [None] * 4
        t[0] = Tree(self.x, self.y, log2size, depth, self)
        t[1] = Tree(self.x+size, self.y, log2size, depth, self)
        t[2] = Tree(self.x, self.y+size, log2size, depth, self)
        t[3] = Tree(self.x+size, self.y+size, log2size, depth, self)
        #if random.randint(0,1):
        #    not_exist_idx = random.randint(0,3)
        #    cb[not_exist_idx] = None
        for i in range(4):
            self.add_child(t[i])

    def populate(self, max_depth):
        if self.depth >= max_depth: 
            return
        self.split_cu_flag = random.randint(0, 1)
        if self.split_cu_flag == 1:
            self.split(self.log2size - 1, self.depth + 1)
        for n in self.children:
            if n is not None:
                n.populate(max_depth)

    def __str__(self):
        a = [[' ' for i in range(self.size)] for j in range(self.size)]
        for n in self.get_leaves():
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

    def draw(self, ax):
        if self.is_root():
            edgecolor = 'blue'
        else:
            edgecolor = 'black'
        rect = patches.Rectangle((self.x, self.y), self.size, self.size, edgecolor=edgecolor, facecolor='white')
        ax.add_patch(rect)
        for node in self.children:
            node.draw(ax)

if __name__ == "__main__":
    ctb = Tree(0, 0, 6)
    ctb.populate(3)

    print ctb
    ctb.dump()
    ctb.dump_leaves()

    fig = plt.figure(1)
    ax = fig.add_subplot(111)
    ax.set_xticks([0, 8, 16, 24, 32, 40, 48, 56, 64])
    ax.set_yticks([0, 8, 16, 24, 32, 40, 48, 56, 64])
    ax.xaxis.tick_top()
    ax.invert_yaxis()
    ax.set_xlim(0, 64)
    ax.set_ylim(64, 0)

    ctb.draw(ax)
    plt.show()
    
    print "breath-first traversing start:"
    for i in ctb.traverse(strategy = "breath-first"):
        print "%s%dx%d(%d)" % (' '*4*i.depth, i.x, i.y, i.size)
    exit()

    
    for i in ctb.traverse():
        print "%s%dx%d(%d)" % (' '*4*i.depth, i.x, i.y, i.size)
    
    cb0 = Tree(0, 0, 5)
    assert cb0.contain(31, 31) == True
    assert cb0.contain(32, 32) == False
    assert cb0.contain(1,2) == True
    print ctb
    exit()

