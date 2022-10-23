from plotting_tools import *
from phase_picker import phase_picker
import os
from subprocess import Popen, PIPE

root_crsmex = os.environ["ROOT_CRSMEX"]

if __name__ == '__main__':
    for directory in os.listdir(os.path.join(root_crsmex,'tmp')):
        cmd = 'python phase_picker.py -d ' + directory + ' -p'
        print(cmd)
        proc = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
        out, err = proc.communicate()
        print('return code: ', proc.returncode)
    #plot_catalog('catalog.db')
