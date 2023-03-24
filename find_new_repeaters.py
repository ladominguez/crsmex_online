from re import I
import obspy as ob
import os
import h5py
import sqlite3
from scipy import signal
from util import load_configuration
import glob
import numpy as np
from matplotlib import pyplot as plt
from data_colector import *
from matplotlib.pyplot import cm
from crsmex import get_correlation_coefficient, FFTshift
from pandas import DataFrame, read_pickle
from sklearn import preprocessing
import logging
import platform

plt.rcParams.update({'font.size': 16})
from plotting_tools import plot_sequence_candidates

# load configuration
config = load_configuration()
root_crsmex = os.environ["ROOT_CRSMEX"]
h5 = h5py.File(config["h5_file"])

# Logging configuration
FORMAT = '%(asctime)-15s {%(filename)s:%(lineno)d} %(levelname)s - %(message)s'
log = logging.getLogger(name='CRSMEX')
log.setLevel(logging.INFO)
logging.basicConfig(format=FORMAT)

fh = logging.FileHandler(os.path.join(root_crsmex, 'logger.txt'))
fh.setFormatter(logging.Formatter(FORMAT))
fh.setLevel(logging.WARNING)
log.addHandler(fh)


if platform.node() == 'ubuntu-1cpu-1gb-us-nyc1':  # ubuntu-1cpu-1gb-us-nyc1 upcloud server
    from systemd.journal import JournalHandler
    log.addHandler(JournalHandler())
    log.setLevel(logging.WARNING)


def find_new_repeaters(tweet_id, possible_sequences, plotting=False):
    matching_sequence = []
    cc_thresholds = []
    for sequence in possible_sequences:
        RepeaterFound = False
        sequence_group = h5.get('S' + '%05d'%(sequence))
        stations_seq = list(sequence_group.attrs.get('stations'))
        sac = ob.read(os.path.join(root_crsmex,'tmp',str(tweet_id),'*Z.sac'))
        stations_tweet = [tr.stats.sac.kstnm.strip() for tr in sac]
        process_stations = list(set(stations_seq).intersection(set(stations_tweet)))
        phases = read_pickle(os.path.join(root_crsmex,'tmp',str(tweet_id),'phases.pkl'))
        phases.set_index("station", drop = False, inplace = True)
        #print('tweet_id: ', tweet_id)
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
                if cc >= config["cc_lim"]:
                    log.info('Repeater found:' + tweet_id + ' sequence: ' + str(sequence) + ' sta: ' +  sta_tweet
                             + ' cc: ' +  str(cc) + ' ts: ' + str(tshift)) 
                    RepeaterFound = True
                    matching_sequence.append(sequence)
                    cc_thresholds.append(sequence)
                    if plotting:
                        print('Subplots: ', n_members + 2)
                        fig, ax = plt.subplots(nrows=n_members+2, ncols=1, squeeze=False, figsize = (14, 1.8*(n_members+2)),
                                    sharex=True)
                        color = iter(cm.rainbow(np.linspace(0, 1, n_members)))

                        ax[0,0].plot(t_master, master,  color = 'k', linewidth = 0.5, label = str(tweet_id))
                        ax[0,0].legend()
                        ax[0,0].axvline(0)
                        ax[0,0].grid(which='major')
                        #ax[n_members+1,0].plot(t_master[index_master], master[index_master]/np.max(np.abs(master[index_master])),  color = 'r', linewidth = 0.5)
                        ax[n_members+1,0].plot(t_master[index_master], master[index_master]/np.max(np.abs(master[index_master])),  color = 'r', linewidth = 0.5)
                        ax[n_members+1,0].axvline(0)
                        #ax[n_members+1,0].legend()
                        ax[n_members+1,0].grid(which='major')

                if plotting and RepeaterFound:
                    ax[m+1,0].plot(time, wave_filt, color = 'k', linewidth = 0.5, label = datetime +", M" + '%3.1f'%(mag) + " cc: " + '%4.2f' % (cc))
                    #ax[m+1,0].plot(time[index_out], wave_filt[index_out], color = 'red', linewidth = 1)
                    ax[m+1,0].axvline(0)
                    ax[m+1,0].grid(which='major')
                    ax[m+1,0].grid(which='minor')
                    ax[m+1,0].set_xlim((-3, config['window']))
                    ax[m+1,0].legend()
                    tshift=0
                    #ax[n_members+1,0].plot(time, FFTshift(wave_filt/np.max(np.abs(wave_filt)),float(tshift/delta)), color = next(color),
                    #                     linewidth= 0.5)
                    #ax[n_members+1,0].grid(which='major')
                    #ax[n_members+1,0].grid(which='minor')
                    #ax[n_members+1,0].set_xlim((-3, config['window']))
            if plotting and RepeaterFound:
                fig.suptitle('Sequence ' +  '%05d'%(sequence) + ' - ' + sta_tweet + ' - Testing Tweet: ' + str(tweet_id)) 
                plt.savefig(os.path.join(root_crsmex,'tmp',str(tweet_id), sta_tweet + '.S' + '%05d'%(sequence) + '.png'))
                print('Saving: ', os.path.join(root_crsmex,'tmp',str(tweet_id), sta_tweet + '.S' + '%05d'%(sequence) + '.png'))
                plt.close()
    return RepeaterFound, matching_sequence, cc_thresholds

def _get_twitter_info(tweet_id):
    con = sqlite3.connect(os.path.join(root_crsmex, config['database']))
    cursor = con.cursor()
    get_twitter_info = '''SELECT datetime ''' 

def modify_repeater_database(tweet_id, matching_sequence):
    Success = False

    if len(matching_sequence) == 0:
        return Success
    elif len(matching_sequence) == 1:
        con = sqlite3.connect(os.path.join(root_crsmex, config['database']))
        cursor = con.cursor()
        get_previous_record_sql = '''SELECT dates FROM repeaters WHERE ID = ?'''
        get_twitter_info = '''SELECT datetime FROM twitter WHERE  tweet_id = ?'''
        update_sql = '''UPDATE repeaters SET no_repeaters = no_repeaters + 1,
                        intervals = intervals || ?,
                        dates = dates || ?,
                        ids = ids  || ? WHERE ID = ?'''
        cursor.execute(get_twitter_info,(tweet_id,))
        tweet_info = cursor.fetchone()
        cursor.execute(get_previous_record_sql,(matching_sequence,))
        db_results = cursor.fetchone()
        dates = db_results
        time_last = datetime.strptime(dates.split(' ')[-1], '%Y/%m/%d,%H:%M:%S.%f')
        tweet_eq_time = datetime.strptime(tweet_info[0],'%Y/%m/%dT%H:%M:%S')
        dt = tweet_eq_time - time_last
        interval_new = '%.2f' % dt.total_seconds()

        cursor.execute(update_sql, (' ' + interval_new, ' ' + tweet_info[0].replace('T', ','), 
               ' ' + str(tweet_id), matching_sequence))
        con.commit()
        con.close()
        log.info('Sucessfully added tweet ' + str(tweet_id) + ' to repeating sequence ' + matching_sequence + '.')
        Success = True
    else:
        log.warning('More than one sequence matches twitter id ' + tweet_id + ' earthquake was not added to any sequence.')

        
    return Success

            
    
#    if plotting:                 
#        plt.close()
    return None

if __name__ == '__main__':
    #stp_generator()
    #data_colector()
    #check_collected_data()
    #exit()
    #tweet_id=1582015080493092864
    #tweet_id = 1581813685726908417
    directories = glob.glob("./tmp/[0-9]*")
    #directories = glob.glob("./tmp/1587083561303429120")    
    for directory in directories:
        print('Processing: ', directory)
        tweet_id = directory.split('/')[2]
        repeating_list = possible_sequences(tweet_id, r_max = config['radius'])
        if repeating_list:
            #print('list: ', repeating_list)
            #print(tweet_id, repeating_list)
            find_new_repeaters(tweet_id, repeating_list, plotting = True)

#        if not repeating_list:


#    plot_sequence_candidates(tweet_id, repeating_list) 
