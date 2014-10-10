import numpy

def get_upright_diagonal_scan_order_array(size):
    diagnoal_scan = numpy.zeros((size*size, 2))

    i = x = y = 0
    stop = False
    while not stop:
        while y >= 0:
            if x < size and y < size:
                diagnoal_scan[i][0] = x
                diagnoal_scan[i][1] = y
                i += 1
            y -= 1
            x += 1
        y = x
        x = 0
        if i >= (size * size):
            stop = True

    return diagnoal_scan
    
def get_horizontal_scan_order_array(size):
    horizontal_scan = numpy.zeros((size*size, 2))

    i = 0
    for y in range(size):
        for x in range(size):
            horizontal_scan[i][0] = x
            horizontal_scan[i][1] = y
            i += 1

    return horizontal_scan

def get_vertical_scan_order_array(size):
    vertical_scan = numpy.zeros((size*size, 2))

    i = 0
    for x in range(size):
        for y in range(size):
            vertical_scan[i][0] = x
            vertical_scan[i][1] = y
            i += 1

    return vertical_scan

def get_idx_array_from_scan_order_array(a, size):
    a = a.tolist()
    idx = []
    for y in range(size):
        for x in range(size):
            idx.append(a.index([x,y]))
    return idx
   
def dump(tag, a, size):
    print "%s scan (%dx%d): " % (tag, size, size)
    a = get_idx_array_from_scan_order_array(a, size)
    for i in range(size * size):
        print "%2d" % a[i],
        if (i + 1) % size == 0:
            print ""

if __name__ == "__main__":
    def test_upright_diagonal_4x4():
        a = get_upright_diagonal_scan_order_array(4)
        a_exp = [
                0, 2, 5, 9,
                1, 4, 8, 12,
                3, 7, 11, 14,
                6, 10, 13, 15
                ]
        assert get_idx_array_from_scan_order_array(a, 4) == a_exp
        dump("Upright diagonal", a, 4)

    def test_horizontal_4x4():
        a = get_horizontal_scan_order_array(4)
        a_exp = [
                0, 1, 2, 3,
                4, 5, 6, 7,
                8, 9, 10, 11,
                12, 13, 14, 15
                ]
        assert get_idx_array_from_scan_order_array(a, 4) == a_exp
        dump("Horizontal", a, 4)

    def test_vertical_4x4():
        a = get_vertical_scan_order_array(4)
        a_exp = [
                0, 4, 8, 12,
                1, 5, 9, 13,
                2, 6, 10, 14,
                3, 7, 11, 15
                ]
        dump("Vertical", a, 4)

    test_upright_diagonal_4x4()
    test_horizontal_4x4()
    test_vertical_4x4()

    def test_upright_diagonal_8x8():
        a = get_upright_diagonal_scan_order_array(8)
        dump("Upright diagonal", a, 8)

    def test_horizontal_8x8():
        a = get_horizontal_scan_order_array(8)
        dump("Horizontal", a, 8)

    def test_vertical_8x8():
        a = get_vertical_scan_order_array(8)
        dump("Vertical", a, 8)

    test_upright_diagonal_8x8()
    test_horizontal_8x8()
    test_vertical_8x8()

'''
Upright diagonal scan (4x4): 
 0  2  5  9 
 1  4  8 12 
 3  7 11 14 
 6 10 13 15 
Horizontal scan (4x4): 
 0  1  2  3 
 4  5  6  7 
 8  9 10 11 
12 13 14 15 
Vertical scan (4x4): 
 0  4  8 12 
 1  5  9 13 
 2  6 10 14 
 3  7 11 15 
Upright diagonal scan (8x8): 
 0  2  5  9 14 20 27 35 
 1  4  8 13 19 26 34 42 
 3  7 12 18 25 33 41 48 
 6 11 17 24 32 40 47 53 
10 16 23 31 39 46 52 57 
15 22 30 38 45 51 56 60 
21 29 37 44 50 55 59 62 
28 36 43 49 54 58 61 63 
Horizontal scan (8x8): 
 0  1  2  3  4  5  6  7 
 8  9 10 11 12 13 14 15 
16 17 18 19 20 21 22 23 
24 25 26 27 28 29 30 31 
32 33 34 35 36 37 38 39 
40 41 42 43 44 45 46 47 
48 49 50 51 52 53 54 55 
56 57 58 59 60 61 62 63 
Vertical scan (8x8): 
 0  8 16 24 32 40 48 56 
 1  9 17 25 33 41 49 57 
 2 10 18 26 34 42 50 58 
 3 11 19 27 35 43 51 59 
 4 12 20 28 36 44 52 60 
 5 13 21 29 37 45 53 61 
 6 14 22 30 38 46 54 62 
 7 15 23 31 39 47 55 63 
 '''

