from subprocess import Popen, PIPE
cmd="python -c 'from ctypes import *; memset(0,1,1)'"
proc = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
out, err = proc.communicate()
print(proc.returncode, type(proc.returncode))

