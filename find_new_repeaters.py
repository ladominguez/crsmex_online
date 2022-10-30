import obspy as ob
import os
import h5py
from scipy import signal
from util import load_configuration
import glob
import numpy as np
from matplotlib import pyplot as plt
from data_colector import possible_sequences
#from plotting_tools import plot_sequence_candidates

# load configuration
config = load_configuration()
root_crsmex = os.environ["ROOT_CRSMEX"]
h5 = h5py.File(config["h5_file"])


def find_new_repeaters(tweet_id, possible_sequences):
    for sequence in possible_sequences:
        print('S' + '%05d'%(sequence))
        sequence_group = h5.get('S' + '%05d'%(sequence))
        stations_seq = list(sequence_group.attrs.get('stations'))
        sac = ob.read(os.path.join(root_crsmex,'tmp',str(tweet_id),'*Z.sac'))
        stations_tweet = [tr.stats.sac.kstnm.strip() for tr in sac]
        process_stations = list(set(stations_seq).intersection(set(stations_tweet)))
        for sta_tweet in process_stations:
            waveforms = sequence_group.get(sta_tweet)
            print(sta_tweet)
            print(waveforms)
            print(waveforms.keys())
            print('sta: ', sta_tweet)
            for wave_key in waveforms.keys():
                wave = np.array(waveforms.get(wave_key))
                delta = waveforms.get(wave_key).attrs['delta']
                npts = waveforms.get(wave_key).attrs['npts']
                t5 = waveforms.get(wave_key).attrs['t5']
                beg = waveforms.get(wave_key).attrs['b']

                print("dt: ", delta)
                print("npts: ", npts)
                print("t5: ", t5)
                print("b: ", beg)
                b, a = signal.butter(config["poles"],[config["low"],config["high"]], "bandpass", fs = 1/delta)
                wave_filt = signal.filtfilt(b, a, wave)
                time = np.linspace(start=beg,stop=(npts-1)*delta - beg,
                                   num=npts)
                print('t(min): ', time.min(0))

                plt.plot(time, wave_filt, color = 'k', linewidth = 0.5)
                plt.axvline(t5)
                #plt.xlim((0, 100))
                plt.show()
                break 

        break
    plt.close()
    return None

if __name__ == '__main__':
    #stp_generator()
    #data_colector()
    #check_collected_data()
    tweet_id=1582015080493092864
    repeating_list = possible_sequences(tweet_id, r_max = config['radius'])
    find_new_repeaters(tweet_id, repeating_list)
#    plot_sequence_candidates(tweet_id, repeating_list) 