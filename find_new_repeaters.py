from re import I
import obspy as ob
import os
import h5py
from scipy import signal
from util import load_configuration
import glob
import numpy as np
from matplotlib import pyplot as plt
from data_colector import possible_sequences
from matplotlib.pyplot import cm
from crsmex import get_correlation_coefficient, FFTshift
from pandas import DataFrame, read_pickle
from sklearn import preprocessing


plt.rcParams.update({'font.size': 16})
#from plotting_tools import plot_sequence_candidates

# load configuration
config = load_configuration()
root_crsmex = os.environ["ROOT_CRSMEX"]
h5 = h5py.File(config["h5_file"])


def find_new_repeaters(tweet_id, possible_sequences, plotting = False):
    for sequence in possible_sequences:
        sequence_group = h5.get('S' + '%05d'%(sequence))
        stations_seq = list(sequence_group.attrs.get('stations'))
        sac = ob.read(os.path.join(root_crsmex,'tmp',str(tweet_id),'*Z.sac'))
        stations_tweet = [tr.stats.sac.kstnm.strip() for tr in sac]
        process_stations = list(set(stations_seq).intersection(set(stations_tweet)))
        phases = read_pickle(os.path.join(root_crsmex,'tmp',str(tweet_id),'phases.pkl'))
        phases.set_index("station", drop = False, inplace = True)
        for sta_tweet in process_stations:
            tp_master = phases.loc[sta_tweet]["P"]
            waveforms = sequence_group.get(sta_tweet)

            n_members = len(waveforms.keys())
            master_tweet = ob.read(os.path.join(root_crsmex,'tmp',str(tweet_id),'*' + sta_tweet + '*Z.sac'))
            master_tweet.decimate(5)
            master = master_tweet[0].data
            t_master = master_tweet[0].times() + master_tweet[0].stats.sac.b - tp_master
            b, a = signal.butter(config["poles"],[config["low"],config["high"]], "bandpass", fs = master_tweet[0].stats.sampling_rate)
            master = signal.filtfilt(b, a, master)
            index_master,  = np.where((t_master >= -2.0) & ( t_master < (-2 + config["npts_win"]*(1/master_tweet[0].stats.sampling_rate))))

            if plotting:
                fig, ax = plt.subplots(nrows=n_members+1, ncols=1, squeeze=False, figsize = (14, 1.8*(n_members+1)),
                                    sharex=True)
                color = iter(cm.rainbow(np.linspace(0, 1, n_members)))

                ax[0,0].plot(t_master, master,  color = 'k', linewidth = 0.5, label = str(tweet_id))
                ax[0,0].plot(t_master[index_master], master[index_master],  color = 'r', linewidth = 0.8)
                ax[0,0].axvline(0)
                ax[0,0].legend()
                ax[0,0].grid(which='major')
                RepeaterFound = False
                 
            for m, wave_key in enumerate(waveforms.keys()):
                wave = np.array(waveforms.get(wave_key))
                delta = waveforms.get(wave_key).attrs['delta']
                npts = waveforms.get(wave_key).attrs['npts']
                t5 = waveforms.get(wave_key).attrs['t5']
                beg = waveforms.get(wave_key).attrs['b']
                datetime = waveforms.get(wave_key).attrs['datetime']
                mag = waveforms.get(wave_key).attrs['magnitude']
 

                b, a = signal.butter(config["poles"],[config["low"],config["high"]], "bandpass", fs = 1/delta)
                wave_filt = signal.filtfilt(b, a, wave)
                time = np.linspace(start=beg,stop=(npts-1)*delta + beg,
                                   num=npts)
                time = time -(t5)

                index_out,  = np.where((time >= -2.0) & ( time < (-2 + config["npts_win"]*delta)))
                
                #if not m:
                #    master = wave_filt[index_out]
                #    tshift = 0
                #else:
                test = wave_filt[index_out]
                cc, tshift = get_correlation_coefficient(master[index_master], test, delta)
                if cc >= 0.2:
                    print('Repeater found:', tweet_id, ' sequence: ', sequence, ' sta:', sta_tweet)
                    print('cc: ', cc)
                    print('ts: ', tshift) 
                    RepeaterFound = True


                if plotting:
                    ax[m+1,0].plot(time, wave_filt, color = 'k', linewidth = 0.5, label = datetime +", M" + '%3.1f'%(mag) + " cc: " + '%4.2f' % (cc))
                    ax[m+1,0].plot(time[index_out], wave_filt[index_out], color = 'red', linewidth = 1)
                    ax[m+1,0].axvline(0)
                    ax[m+1,0].grid(which='major')
                    ax[m+1,0].grid(which='minor')
                    ax[m+1,0].set_xlim((-3, config['window']))
                    ax[m+1,0].legend()
                    #ax[n_members,0].plot(time, FFTshift(wave_filt/np.max(np.abs(wave_filt)),float(tshift/delta)), color = next(color),
                    #                     linewidth= 0.9)
                    #ax[n_members,0].grid(which='major')
                    #ax[n_members,0].grid(which='minor')
                    #ax[n_members,0].axvline(0)
                    #ax[n_members,0].set_xlim((- 2, 27))
            if plotting and RepeaterFound:
                fig.suptitle('Sequence ' +  '%05d'%(sequence) + ' - ' + sta_tweet + ' - Testing Tweet: ' + str(tweet_id)) 
                plt.savefig(os.path.join(root_crsmex,'tmp',str(tweet_id), sta_tweet + '.S' + '%05d'%(sequence) + '.png'))
                print('Saving: ', os.path.join(root_crsmex,'tmp',str(tweet_id), sta_tweet + '.S' + '%05d'%(sequence) + '.png'))
            if plotting:
                plt.close()
            
        
            
    
#    if plotting:                 
#        plt.close()
    return None

if __name__ == '__main__':
    #stp_generator()
    #data_colector()
    #check_collected_data()
    #tweet_id=1582015080493092864
    tweet_id = 1581813685726908417
    directories = glob.glob("./tmp/[0-9]*")
    directories = glob.glob("./tmp/1581994291362029568")    
    for directory in directories:
        tweet_id = directory.split('/')[2]
        repeating_list = possible_sequences(tweet_id, r_max = config['radius'])
        if repeating_list:
            print(tweet_id, repeating_list)
            find_new_repeaters(tweet_id, repeating_list, plotting = True)

#        if not repeating_list:


#    plot_sequence_candidates(tweet_id, repeating_list) 
