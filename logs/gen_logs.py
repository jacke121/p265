import re

f = None
frame_cnt = 0

for line in open('p265.log'):
    match_new_picture = re.match('^\[location\] Frame (\d+) decoded', line)
    match_vps = re.match('^\[location\] Start decoding VPS', line)
    match_sps = re.match('^\[location\] Start decoding SPS', line)
    match_pps = re.match('^\[location\] Start decoding PPS', line)
    match_ctu = re.match('^\[location\] Start decoding CTU(.*)addr_rs = (\d+)', line)
    if match_new_picture:
        frame_cnt += 1
    if match_vps:
        f = open('vps.log', 'w')
    elif match_sps:
        f = open('sps.log', 'w')
    elif match_pps:
        f = open('pps.log', 'w')
    elif match_ctu:
        f = open("frame%d_ctu%s.log" % (frame_cnt, match_ctu.group(2)), 'w')
    elif f is None:
        pass
    else:
        match_obj = re.match('^\[(syntax_element|cabac|location)\] (.*)', line)
        if match_obj:
            f.write(match_obj.group(2))
            f.write('\n')
