#from re import I
#from turtle import color
#from urllib.parse import _NetlocResultMixinStr
from obspy.core import read
from obspy.signal.trigger import ar_pick
from matplotlib import pyplot as plt
from util import load_configuration
import os
import glob
from pandas import DataFrame, read_pickle
import time
import argparse
import matplotlib as mpl
mpl.use('Agg')

plt.rcParams["figure.figsize"] = (10, 6)
plt.rcParams.update({'font.size': 16})
config = load_configuration()
root_crsmex = os.environ["ROOT_CRSMEX"]
stations = read_pickle(os.path.join(root_crsmex, config["stations"]))
stations.sort_values(by=['station'], inplace=True)
#print(stations)

#df = tr1.stats.sampling_rate
f1 = 2.0       # Frequency of the lower bandpass window
f2 = 20      # Frequency of the lower bandpass window
lta_p = 1    # Length of LTA for the P arrival in seconds.
sta_p = 0.1  # Length of STA for the P arrival in seconds.
lta_s = 4    # Length of LTA for the S arrival in seconds.
sta_s = 1.0  # Length of STA for the S arrival in seconds.
m_p = 2      # Number of AR coefficients for the P arrival.
m_s = 8      # Number of AR coefficients for the S arrival.
l_p = 0.1    # Length of variance window for the P arrival in seconds.
l_s = 0.2   # Length of variance window for the S arrival in seconds.
#s_pick = True  # If True, also pick the S phase, otherwise only the P phase.


def phase_picker(directory,plotting=False):
    try:
        stream=read(os.path.join(root_crsmex,'tmp',directory,'*.sac'))
    except:
        return None

    stream.detrend()
    Nsubplots = len(stream)/3
    m = 0

    P_list = []
    S_list = []
    Sta_list = []

    if plotting:
        fig, ax = plt.subplots(nrows=int(Nsubplots), ncols=1, squeeze=False)

    for sta in stations['station']:
        st_sta = stream.select(station=sta)
        if st_sta:
            try:
                tz=st_sta.select(channel='HHZ')[0].data
                te=st_sta.select(channel='HHE')[0].data
                tn=st_sta.select(channel='HHN')[0].data
                ds=st_sta.select(channel='HHZ')[0].stats.sampling_rate
                p_pick, s_pick = ar_pick(tz, te, tn, ds, f1, f2, lta_p, sta_p, lta_s, sta_p, m_p, m_s, l_p, l_s, True)
            except:
                continue
            P_list.append(round(p_pick,2))
            S_list.append(round(s_pick,2))
            Sta_list.append(sta)
            if plotting:
                st_sta.select(channel='HHZ')[0].filter("highpass", freq=2.0)
                ax[m,0].plot(st_sta.select(channel='HHZ')[0].times(), 
                st_sta.select(channel='HHZ')[0].data,
                linewidth=0.2,color='k',
                label=sta)
                ax[m,0].axvline(p_pick,color='red',ls='--')
                ax[m,0].axvline(s_pick,color='blue',ls='--')
                ax[m,0].autoscale(enable=True, axis='x', tight=True)
                ax[m,0].set_xlabel('time (s)')
                ax[m,0].set_title('Station: ' + sta,fontsize=16)
                ax[m,0].grid(which='major')
                ax[m,0].grid(which='minor')
                m += 1
            del st_sta
    phases = DataFrame({'station' : Sta_list, 'P' : P_list, 'S' : S_list })
    phases.to_pickle(os.path.join(root_crsmex,'tmp',directory,'phases.pkl'))

    if plotting:
        plt.setp(ax, xlim=(phases['P'].min()-5,phases['S'].max()+5))
        #fig.tight_layout()
        fig.savefig(os.path.join(root_crsmex,'tmp',directory,'picks.png'))
        plt.close()
    del stream
    try:
        return phases
    except TypeError:
        return None

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--directory', type=str)
    parser.add_argument('-p', action='store_true', help='-p for plotting.')
    args = parser.parse_args()
    directory = args.directory
    plotting = args.p
    
    #for directory in os.listdir(os.path.join(root_crsmex,'tmp')):    
        #directory='1581993473430802434'
        #directory='1581813837128675329'
        #directory='1582015080493092864'
    print(os.path.join(root_crsmex,'tmp',directory,'*.sac'))
    phases = phase_picker(directory,plotting=plotting)
    print(phases)

