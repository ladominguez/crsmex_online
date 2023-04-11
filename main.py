from plotting_tools import *
from phase_picker import phase_picker
import os
from subprocess import Popen, PIPE
from tqdm import tqdm

root_crsmex = os.environ["ROOT_CRSMEX"]

if __name__ == '__main__':
    #directories = os.listdir(os.path.join(root_crsmex,'tmp'))
    for directory in tqdm(os.listdir(os.path.join(root_crsmex,'tmp'))):
        cmd = 'python phase_picker.py -d ' + directory + ' -p'
        file = os.path.join(root_crsmex,'tmp',directory,'phases.pkl') 
        if not os.path.exists(os.path.join(root_crsmex,'tmp',directory,'phases.pkl')):
            proc = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
            out, err = proc.communicate()
            if proc.returncode == -11:
                print('return code: ', proc.returncode)
