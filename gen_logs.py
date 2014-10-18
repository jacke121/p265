import re

f = None
for line in open('syntax_element.log'):
    match_new_picture = re.match('^hm\.(location) -- \+\+\+\+\+\+ Start decoding frame (\d+)', line)
    match_vps = re.match('^\+\+\+\+\+\+ Start decoding VPS(.*)', line)
    match_sps = re.match('^\+\+\+\+\+\+ Start decoding SPS(.*)', line)
    match_pps = re.match('^\+\+\+\+\+\+ Start decoding PPS(.*)', line)
    match_ctu = re.match('^\+\+\+\+\+\+ Start decoding CTU(.*)addr_rs = (\d+)', line)
    if match_new_picture:
        frame_cnt = match_new_picture.group(2)
    if match_vps:
        f = open('logs/vps.log', 'w')
    elif match_sps:
        f = open('logs/sps.log', 'w')
    elif match_pps:
        f = open('logs/pps.log', 'w')
    elif match_ctu:
        f = open("logs/frame%s_ctu%s.log" % ('0', match_ctu.group(2)), 'w')
    elif f is None:
        pass
    else:
        f.write(line)

