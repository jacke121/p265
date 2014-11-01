def clip3(min, max, val):
    if val > max:
        result = max
    elif val < min:
        result = min
    else:
        result = val
    
    return result

def clip1_y(x, bit_depth):
    return clip3(0, (1 << bit_depth) - 1, x)

def clip1_c(x, bit_depth):
    return clip1_y(x, bit_depth)

'''
class md_dict(dict):
    def __getitem__(self, item):
        try:
            return dict.__getitem__(self, item)
        except KeyError:
            value = self[item] = type(self)()
            return value
'''

class md_dict(dict):
    def __missing__(self, key):
        value = self[key] = type(self)()
        return value

'''
import collections
def md_dict():
    return collections.defaultdict(md_dict)
'''

if __name__ == "__main__":
    d = md_dict()
    print d

    d[0][1] = 7
    d[0][1] = 8
    d[0][8] = 9
    d[0]["test1"] = "hello"
    d["test2"] = 'T'
    
    print d
    print d[2]

    import pprint
    print d
