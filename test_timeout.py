from subprocess import Popen, PIPE, DEVNULL, TimeoutExpired
import os

input="in get_data.stp\nexit\n"
p = Popen('/Users/antonio/bin/SSNstp',stdin=PIPE, stdout=None, stderr=DEVNULL, bufsize=0) 
try: 
    outs, err = p.communicate(input.encode('ascii'),timeout=50)
except TimeoutExpired:
    p.kill()
    outs, errs = p.communicate()
    print('outs: ', outs)
    print('errs: ', errs)


