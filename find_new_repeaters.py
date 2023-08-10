from re import I
from obspy.core import read, Stream
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
    times_repeater = {}
    waveforms_repeater = {}
    times_test_repeater = {}
    waveforms_test_repeater = {}
    stations_sequence = {}
    repeater_list_station = {}
    cc_thresholds = {}
    tshift_thresholds = {}
    datetimes_repeater = {}
    magnitude_repeater = {}
    matching_sequence = []
    #cc_max_per_sequence = []
    # Loops for every nearby sequence
    RepeaterFound = False

    for sequence in possible_sequences:
        stations_above_threshold = 0
        times_repeater[sequence] = {}
        waveforms_repeater[sequence] = {}
        times_test_repeater[sequence] = {}
        waveforms_test_repeater[sequence] = {}
        
        #cc_thresholds = []
        sequence_group = h5.get('S' + '%05d'%(sequence))
        stations_seq = list(sequence_group.attrs.get('stations'))
        sac = read(os.path.join(root_crsmex,'tmp',str(tweet_id),'*Z.sac'))
        stations_tweet = [tr.stats.sac.kstnm.strip() for tr in sac]
        process_stations = list(set(stations_seq).intersection(set(stations_tweet)))
        phases = read_pickle(os.path.join(root_crsmex,'tmp',str(tweet_id),'phases.pkl'))
        phases.set_index("station", drop = False, inplace = True)
        stations_sequence[sequence] = process_stations
        repeater_list_station[sequence] = []   
        cc_thresholds[sequence] = {}
        tshift_thresholds[sequence] = {}
        datetimes_repeater[sequence] = {}
        magnitude_repeater[sequence] = {}

        # Loops for each station
        for sta_tweet in process_stations:
            times_test_repeater[sequence][sta_tweet] = []
            waveforms_test_repeater[sequence][sta_tweet] = []
            times_repeater[sequence][sta_tweet] = []
            waveforms_repeater[sequence][sta_tweet] = []
            tp_master = phases.loc[sta_tweet]["P"]
            waveforms = sequence_group.get(sta_tweet)

            master_tweet = sac.select(station=sta_tweet)
            master_tweet.decimate(5)
            master = master_tweet[0].data
            t_master = master_tweet[0].times() + master_tweet[0].stats.sac.b - tp_master
            b, a = signal.butter(config["poles"],[config["low"],config["high"]], "bandpass", fs = master_tweet[0].stats.sampling_rate)
            master = signal.filtfilt(b, a, master)
            index_master,  = np.where((t_master >= -2.0) & ( t_master < (-2 + config["npts_win"]*(1/master_tweet[0].stats.sampling_rate))))
            
            times_test_repeater[sequence][sta_tweet].append(t_master)
            waveforms_test_repeater[sequence][sta_tweet].append(master)            

            # Loops for each waveform

            cc_per_station = []
            tshift_per_station = []
            datetimes_list = []
            magnitude_list = []

            for m, wave_key in enumerate(waveforms.keys()):
                wave = np.array(waveforms.get(wave_key))
                delta = waveforms.get(wave_key).attrs['delta']
                npts = waveforms.get(wave_key).attrs['npts']
                t5 = waveforms.get(wave_key).attrs['t5']
                beg = waveforms.get(wave_key).attrs['b']
                datetime = waveforms.get(wave_key).attrs['datetime']
                datetimes_list.append(datetime)
                magnitude_list.append(waveforms.get(wave_key).attrs['magnitude'])

                b, a = signal.butter(config["poles"],[config["low"],config["high"]], "bandpass", fs = 1/delta)
                wave_filt = signal.filtfilt(b, a, wave)
                time = np.linspace(start=beg,stop=(npts-1)*delta + beg,
                                   num=npts)
                time = time - (t5)
                times_test_repeater[sequence][sta_tweet].append(time)
                waveforms_test_repeater[sequence][sta_tweet].append(wave_filt)
                
                index_out,  = np.where((time >= -2.0) & ( time < (-2 + config["npts_win"]*delta)))
                
                test = wave_filt[index_out]
                cc, tshift = get_correlation_coefficient(master[index_master], test, delta)
                cc_per_station.append(cc)
                tshift_per_station.append(tshift)

        
            if np.max(cc_per_station) >= config["cc_lim"]:
                stations_above_threshold += 1
                times_repeater[sequence][sta_tweet] = times_test_repeater[sequence][sta_tweet]
                waveforms_repeater[sequence][sta_tweet] = waveforms_test_repeater[sequence][sta_tweet]
                #RepeaterFound = True
                matching_sequence.append(sequence)
                repeater_list_station[sequence].append(sta_tweet)
                #cc_max_per_sequence.append(np.max(cc_per_station))

                cc_thresholds[sequence][sta_tweet] = cc_per_station
                tshift_thresholds[sequence][sta_tweet] = tshift_per_station
                datetimes_repeater[sequence][sta_tweet] = datetimes_list
                magnitude_repeater[sequence][sta_tweet] = magnitude_list
                #print('repeater_list_station[', sequence, ']: ', repeater_list_station[sequence],  ' - ', sta_tweet)
                #print('cc_threshold[sequence]: ', )

        if not repeater_list_station[sequence]:
            repeater_list_station.pop(sequence)
        #print('tweet_id: ', tweet_id, ' sequence: ', sequence, ' station: ', sta_tweet, ' cc: ', cc_thresholds_max_per_sequence[sequence])
        #if any([x >= config["cc_lim"] for x in cc_thresholds_max_per_sequence[sequence][sta_tweet]]):

            #print('sequence: ', sequence, ' sta_tweet: ', sta_tweet, ' RepeaterFound: ', RepeaterFound)
            #matching_sequence.append(sequence)

    if not matching_sequence:
        return RepeaterFound, [], []

    cc_max_per_sequence = {}
    #print('matching_sequence: ', matching_sequence)
    for match in matching_sequence:
        #print('match: ', match)
        cc_max_per_station = []
        #print('repeater_list_station[match]: ', cc_thresholds[match])
        #print('cc_thresholds[match]: ', cc_thresholds[match])
        for sta_detected in repeater_list_station[match]:
            cc_max_per_station.append(np.max(cc_thresholds[match][sta_detected]))
            #print('sequence: ', match, ' sta_detected: ', sta_detected, 'cc_thresholds: ', np.max(cc_thresholds[match][sta_detected]))
        cc_max_per_sequence[match] = np.max(cc_max_per_station)
    
    cc_max = max(cc_max_per_sequence.values()) 
    match = max(cc_max_per_sequence, key = cc_max_per_sequence.get)

    if cc_max >= config['cc_lim']:
        if len(repeater_list_station[match]) >= config['no_min_sta']:
            log.info('Repeater found:' + tweet_id + ' sequence: ' + str(match) 
                     + ' no_sta: ' + str(len(repeater_list_station[match])) 
                     + ' sta: ' +  ','.join(repeater_list_station[match])
                     + ' cc_max: ' + '%.3f' % cc_max )
            RepeaterFound = True 

    
    if plotting and RepeaterFound:
            #print('times_repeater: ', len(times_repeater[match][sta_detected]))
        #print('matching_sequence: ', matching_sequence)
            #print('repeater_list_station: ', repeater_list_station)
        for sta_detected in repeater_list_station[match]: 
            #print('match: ', match, ' sta_detected: ', sta_detected)
            n_members = len(times_repeater[match][sta_detected])
            #print('Subplots: ', n_members)
            fig, ax = plt.subplots(nrows=n_members+1, ncols=1, squeeze=False, figsize = (14, 1.8*(n_members+2)),
                        sharex=True)
            color = iter(cm.rainbow(np.linspace(0, 1, n_members)))

            #print('match: ', match)
            #print('sta_detected: ', sta_detected)
            
            #print('times_repeater: ', times_repeater[match][sta_detected])

            for m, (time, wave_filt) in enumerate(zip(times_repeater[match][sta_detected], 
                                               waveforms_repeater[match][sta_detected])):
                                               #cc_thresholds[match][sta_detected],
                                               #tshift_thresholds[match][sta_detected])):

                if not m: # master label
                    label = ('%s - M%.2f'%_get_twitter_info(1635098967141916673)).replace('T',',')
                else:
                    label = datetimes_repeater[match][sta_detected][m-1] + ", M" + '%3.1f' % (magnitude_repeater[match][sta_detected][m-1]) + " cc: " + '%4.2f' % (cc_thresholds[match][sta_detected][m-1])

                ax[m,0].plot(time, wave_filt, color = 'k', linewidth = 0.5, label = label)
                ax[m,0].axvline(0)
                ax[m,0].grid(which='major')
                ax[m,0].grid(which='minor')
                ax[m,0].set_xlim((-3, config['window']))
                ax[m,0].legend()

                if m: # for repeaters in the sequence
                    tshift = 1*tshift_thresholds[match][sta_detected][m-1]
                    ax[n_members,0].plot(time, FFTshift(wave_filt/np.max(np.abs(wave_filt)),float(tshift/delta)), color = next(color), linewidth= 0.5)
                else: # For testing waveform (Tweet)
                    #print('match: ', match, ' sta_detected: ', sta_detected)
                    #print('cc_thresholds[match]: ', cc_thresholds[match])
                    ax[n_members,0].plot(time, wave_filt/np.max(np.abs(wave_filt)), color = next(color), linewidth= 0.5)
                ax[n_members,0].axvline(0)
                ax[n_members,0].grid(which='major')
                ax[n_members,0].grid(which='minor')
                ax[n_members,0].set_xlim((-3, config['window']))
            ax[0,0].set_title('Sequence ' +  '%05d'%(match) + ' - ' + sta_detected + ' - Testing Tweet: ' + str(tweet_id)) 
            plt.savefig(os.path.join(root_crsmex,'tmp',str(tweet_id), sta_detected + '.S' + '%05d'%(match) + '.png'))
            print('Saving: ', os.path.join(root_crsmex,'tmp',str(tweet_id), sta_detected + '.S' + '%05d'%(match) + '.png'))
            plt.close()
            
            # End waveform loop
        # End station loop
    # End sequence loop
    return RepeaterFound, matching_sequence, cc_thresholds

def _read_sac_files(filename_wildcard):
    stream = Stream()
    for filename in glob.glob(filename_wildcard):
        try:
            stream += read(filename)
        except:
            continue
    
    return stream

def find_new_repeaters_rss(rss_id, possible_sequences, plotting=False):
    times_repeater = {}
    waveforms_repeater = {}
    times_test_repeater = {}
    waveforms_test_repeater = {}
    stations_sequence = {}
    repeater_list_station = {}
    cc_thresholds = {}
    tshift_thresholds = {}
    datetimes_repeater = {}
    magnitude_repeater = {}
    matching_sequence = []
    #cc_max_per_sequence = []
    # Loops for every nearby sequence
    RepeaterFound = False

    for sequence in possible_sequences:
        stations_above_threshold = 0
        times_repeater[sequence] = {}
        waveforms_repeater[sequence] = {}
        times_test_repeater[sequence] = {}
        waveforms_test_repeater[sequence] = {}
        
        #cc_thresholds = []
        sequence_group = h5.get('S' + '%05d'%(sequence))
        stations_seq = list(sequence_group.attrs.get('stations'))
        sac = _read_sac_files(os.path.join(root_crsmex,'tmp',str(rss_id),'*Z.sac'))
        stations_rss = [tr.stats.sac.kstnm.strip() for tr in sac]
        process_stations = list(set(stations_seq).intersection(set(stations_rss)))
        phases = read_pickle(os.path.join(root_crsmex,'tmp',str(rss_id),'phases.pkl'))
        phases.set_index("station", drop = False, inplace = True)
        stations_sequence[sequence] = process_stations
        repeater_list_station[sequence] = []   
        cc_thresholds[sequence] = {}
        tshift_thresholds[sequence] = {}
        datetimes_repeater[sequence] = {}
        magnitude_repeater[sequence] = {}

        # Loops for each station
        for sta_rss in process_stations:
            times_test_repeater[sequence][sta_rss] = []
            waveforms_test_repeater[sequence][sta_rss] = []
            times_repeater[sequence][sta_rss] = []
            waveforms_repeater[sequence][sta_rss] = []
            tp_master = phases.loc[sta_rss]["P"]
            waveforms = sequence_group.get(sta_rss)

            master_rss = sac.select(station=sta_rss)
            master_rss.decimate(5,no_filter=True)
            master = master_rss[0].data
            t_master = master_rss[0].times() + master_rss[0].stats.sac.b - tp_master
            b, a = signal.butter(config["poles"],[config["low"],config["high"]], "bandpass", fs = master_rss[0].stats.sampling_rate)
            master = signal.filtfilt(b, a, master)
            index_master,  = np.where((t_master >= -2.0) & ( t_master < (-2 + config["npts_win"]*(1/master_rss[0].stats.sampling_rate))))
            
            times_test_repeater[sequence][sta_rss].append(t_master)
            waveforms_test_repeater[sequence][sta_rss].append(master)            

            # Loops for each waveform

            cc_per_station = []
            tshift_per_station = []
            datetimes_list = []
            magnitude_list = []

            for m, wave_key in enumerate(waveforms.keys()):
                wave = np.array(waveforms.get(wave_key))
                delta = waveforms.get(wave_key).attrs['delta']
                npts = waveforms.get(wave_key).attrs['npts']
                t5 = waveforms.get(wave_key).attrs['t5']
                beg = waveforms.get(wave_key).attrs['b']
                datetime = waveforms.get(wave_key).attrs['datetime']
                datetimes_list.append(datetime)
                magnitude_list.append(waveforms.get(wave_key).attrs['magnitude'])

                b, a = signal.butter(config["poles"],[config["low"],config["high"]], "bandpass", fs = 1/delta)
                wave_filt = signal.filtfilt(b, a, wave)
                time = np.linspace(start=beg,stop=(npts-1)*delta + beg,
                                   num=npts)
                time = time - (t5)
                times_test_repeater[sequence][sta_rss].append(time)
                waveforms_test_repeater[sequence][sta_rss].append(wave_filt)
                
                index_out,  = np.where((time >= -2.0) & ( time < (-2 + config["npts_win"]*delta)))
                
                test = wave_filt[index_out]
                cc, tshift = get_correlation_coefficient(master[index_master], test, delta)
                cc_per_station.append(cc)
                tshift_per_station.append(tshift)

        
            if np.max(cc_per_station) >= config["cc_lim"]:
                stations_above_threshold += 1
                times_repeater[sequence][sta_rss] = times_test_repeater[sequence][sta_rss]
                waveforms_repeater[sequence][sta_rss] = waveforms_test_repeater[sequence][sta_rss]
                #RepeaterFound = True
                matching_sequence.append(sequence)
                repeater_list_station[sequence].append(sta_rss)
                #cc_max_per_sequence.append(np.max(cc_per_station))

                cc_thresholds[sequence][sta_rss] = cc_per_station
                tshift_thresholds[sequence][sta_rss] = tshift_per_station
                datetimes_repeater[sequence][sta_rss] = datetimes_list
                magnitude_repeater[sequence][sta_rss] = magnitude_list
                #print('repeater_list_station[', sequence, ']: ', repeater_list_station[sequence],  ' - ', sta_rss)
                #print('cc_threshold[sequence]: ', )

        if not repeater_list_station[sequence]:
            repeater_list_station.pop(sequence)
        #print('rss_id: ', rss_id, ' sequence: ', sequence, ' station: ', sta_rss, ' cc: ', cc_thresholds_max_per_sequence[sequence])
        #if any([x >= config["cc_lim"] for x in cc_thresholds_max_per_sequence[sequence][sta_rss]]):

            #print('sequence: ', sequence, ' sta_rss: ', sta_rss, ' RepeaterFound: ', RepeaterFound)
            #matching_sequence.append(sequence)

    if not matching_sequence:
        return RepeaterFound, [], []

    cc_max_per_sequence = {}
    #print('matching_sequence: ', matching_sequence)
    for match in matching_sequence:
        #print('match: ', match)
        cc_max_per_station = []
        #print('repeater_list_station[match]: ', cc_thresholds[match])
        #print('cc_thresholds[match]: ', cc_thresholds[match])
        for sta_detected in repeater_list_station[match]:
            cc_max_per_station.append(np.max(cc_thresholds[match][sta_detected]))
            #print('sequence: ', match, ' sta_detected: ', sta_detected, 'cc_thresholds: ', np.max(cc_thresholds[match][sta_detected]))
        cc_max_per_sequence[match] = np.max(cc_max_per_station)
    
    cc_max = max(cc_max_per_sequence.values()) 
    match = max(cc_max_per_sequence, key = cc_max_per_sequence.get)

    if cc_max >= config['cc_lim']:
        if len(repeater_list_station[match]) >= config['no_min_sta']:
            log.info('Repeater found:' + rss_id + ' sequence: ' + str(match) 
                     + ' no_sta: ' + str(len(repeater_list_station[match])) 
                     + ' sta: ' +  ','.join(repeater_list_station[match])
                     + ' cc_max: ' + '%.3f' % cc_max )
            RepeaterFound = True 

    
    if plotting and RepeaterFound:
            #print('times_repeater: ', len(times_repeater[match][sta_detected]))
        #print('matching_sequence: ', matching_sequence)
            #print('repeater_list_station: ', repeater_list_station)
        for sta_detected in repeater_list_station[match]: 
            #print('match: ', match, ' sta_detected: ', sta_detected)
            n_members = len(times_repeater[match][sta_detected])
            #print('Subplots: ', n_members)
            fig, ax = plt.subplots(nrows=n_members+1, ncols=1, squeeze=False, figsize = (14, 1.8*(n_members+2)),
                        sharex=True)
            color = iter(cm.rainbow(np.linspace(0, 1, n_members)))

            #print('match: ', match)
            #print('sta_detected: ', sta_detected)
            
            #print('times_repeater: ', times_repeater[match][sta_detected])

            for m, (time, wave_filt) in enumerate(zip(times_repeater[match][sta_detected], 
                                               waveforms_repeater[match][sta_detected])):
                                               #cc_thresholds[match][sta_detected],
                                               #tshift_thresholds[match][sta_detected])):

                if not m: # master label
                    label = ('%s - M%.2f'%_get_rss_info(rss_id)).replace('T',',')
                else:
                    label = datetimes_repeater[match][sta_detected][m-1] + ", M" + '%3.1f' % (magnitude_repeater[match][sta_detected][m-1]) + " cc: " + '%4.2f' % (cc_thresholds[match][sta_detected][m-1])

                ax[m,0].plot(time, wave_filt, color = 'k', linewidth = 0.5, label = label)
                ax[m,0].axvline(0)
                ax[m,0].grid(which='major')
                ax[m,0].grid(which='minor')
                ax[m,0].set_xlim((-3, config['window']))
                ax[m,0].legend()

                if m: # for repeaters in the sequence
                    tshift = 1*tshift_thresholds[match][sta_detected][m-1]
                    ax[n_members,0].plot(time, FFTshift(wave_filt/np.max(np.abs(wave_filt)),float(tshift/delta)), color = next(color), linewidth= 0.5)
                else: # For testing waveform (Tweet)
                    #print('match: ', match, ' sta_detected: ', sta_detected)
                    #print('cc_thresholds[match]: ', cc_thresholds[match])
                    ax[n_members,0].plot(time, wave_filt/np.max(np.abs(wave_filt)), color = next(color), linewidth= 0.5)
                ax[n_members,0].axvline(0)
                ax[n_members,0].grid(which='major')
                ax[n_members,0].grid(which='minor')
                ax[n_members,0].set_xlim((-3, config['window']))
            ax[0,0].set_title('Sequence ' +  '%05d'%(match) + ' - ' + sta_detected + ' - Testing Tweet: ' + str(rss_id)) 
            plt.savefig(os.path.join(root_crsmex,'tmp',str(rss_id), sta_detected + '.S' + '%05d'%(match) + '.png'))
            print('Saving: ', os.path.join(root_crsmex,'tmp',str(rss_id), sta_detected + '.S' + '%05d'%(match) + '.png'))
            plt.close()
            
            # End waveform loop
        # End station loop
    # End sequence loop
    return RepeaterFound, matching_sequence, cc_thresholds

def _get_twitter_info(tweet_id):
    con = sqlite3.connect(os.path.join(root_crsmex, config['database']))
    cursor = con.cursor()
    get_twitter_info = '''SELECT datetime, mag FROM twitter WHERE tweet_id = ?;'''
    cursor.execute(get_twitter_info,(tweet_id,))
    db_results = cursor.fetchone() 
    return db_results 

def _get_rss_info(rss_id):
    con = sqlite3.connect(os.path.join(root_crsmex, config['database']))
    cursor = con.cursor()
    get_rss_info = '''SELECT datetime, mag FROM rss WHERE rss_id = ?;'''
    cursor.execute(get_rss_info,(rss_id,))
    db_results = cursor.fetchone() 
    return db_results 

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
    #check_collected_data_rss()
    #exit()
    #tweet_id=1582015080493092864
    #tweet_id = 1581813685726908417
    directories = glob.glob("./tmp/[0-9]*")
    #directories = glob.glob("./tmp/202303041044001680")    
    count = 0
    for k, directory in enumerate(directories):
        #if k == 200:
        #    break
        rss_id = directory.split('/')[2]
        repeating_list = possible_sequences_rss(rss_id, r_max = config['radius'])
        #print('repeating_list: ', repeating_list)
        #print(k)
        #repeating_list = [297]
        if repeating_list:
            #print('list: ', repeating_list)
            #print(tweet_id, repeating_list)
            count += 1
            find_new_repeaters_rss(rss_id, repeating_list, plotting = True)
    
    print('Count: ', count)

#        if not repeating_list:


#    plot_sequence_candidates(tweet_id, repeating_list) 
