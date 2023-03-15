#from re import I
#from turtle import color
#from urllib.parse import _NetlocResultMixinStr
from obspy.core import read
from obspy.signal.trigger import ar_pick, pk_baer
from matplotlib import pyplot as plt
from util import load_configuration
import os
import glob
from numpy import sqrt, max, abs
from pandas import DataFrame, read_pickle
import time
import argparse
import matplotlib as mpl
import sqlite3
from geopy.distance import great_circle
from obspy.taup import TauPyModel

mpl.use('Agg')

plt.rcParams["figure.figsize"] = (10, 6)
plt.rcParams.update({'font.size': 16})

config = load_configuration()
root_crsmex = os.environ["ROOT_CRSMEX"]
stations = read_pickle(os.path.join(root_crsmex, config["stations"]))
stations.sort_values(by=['station'], inplace=True)
model = TauPyModel(os.path.join(root_crsmex, config["vel_model"]))
t0 = config['before_time']

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
s_pick = False  # If True, also pick the S phase, otherwise only the P phase.
slice_before = -2
slice_after  = 15

def normalize(array):
    return array/max(abs(array))


def phase_picker(directory,plotting=False):
    try:
        stream=read(os.path.join(root_crsmex,'tmp',directory,'*.sac'))
    except:
        return None

    con = sqlite3.connect(os.path.join(root_crsmex, config['database']))
    cursor = con.cursor()
    cursor.execute("SELECT latitude, longitude, depth FROM twitter WHERE tweet_id =?", (directory,))

    db_result = cursor.fetchone()
    if db_result is not None:
        latitude_eq, longitude_eq, depth = db_result
    else:
        raise Exception('Tweet ' + str(tweet.id) + ' not in the database.')

    stream.detrend()
    Nsubplots = len(stream.select(channel='HHZ'))
    m = 0

    P_list = []
    S_list = []
    Sta_list = []
    dist = []
    depths = []
    theoretical = []
    tslice_start_list = []
    tslice_stop_list = []

    for sta in stations['station']:
        st_sta = stream.select(station=sta)
        st_sta.detrend()
        st_sta.taper(max_percentage = 0.04)
        if st_sta:
            error_P = False
            error_S = False
            ds = st_sta.select(channel='HHZ')[0].stats.sampling_rate
            tstart = st_sta.select(channel='HHZ')[0].stats.starttime

            distance = great_circle((latitude_eq, longitude_eq),(st_sta[0].stats.sac.stla, st_sta[0].stats.sac.stlo)).kilometers/111.19
            arrivals = model.get_travel_times(source_depth_in_km=depth, distance_in_degree=distance,  phase_list=["p", "P"])
            tp_teo = round(arrivals[0].time,2) + t0

            tslice_start = tstart + tp_teo+slice_before 
            tslice_stop = tstart + tp_teo+slice_after
            slice_data = st_sta.slice(tslice_start, tslice_stop)

            
            try:
                tz = slice_data.select(channel='HHZ')[0].data
            except IndexError:
                pass
            try:
                te = slice_data.select(channel='HHE')[0].data
            except IndexError:
                pass
            try:
                tn = slice_data.select(channel='HHN')[0].data
            except IndexError:
                pass

            if len(slice_data) == 3:
                try:
                    p_pick, s_pick = ar_pick(tz, te, tn, ds, f1, f2, lta_p, 
                                             sta_p, lta_s, sta_p, m_p, m_s, l_p, l_s, True)
                except ValueError:
                    continue
            else:
                try:
                    p_pick_samples, _ = pk_baer(tz, slice_data.select(channel='HHZ')[0].stats.sampling_rate, 
                                                20, 60, 7.0, 12.0, 100, 100)
                except ValueError:
                    error_P = True
                    error_S = True
                else:
                    p_pick = p_pick_samples/slice_data.select(channel='HHZ')[0].stats.sampling_rate
                    error_S = True
            if error_P:
                p_pick = tp_teo + slice_before
            else: 
                p_pick = p_pick + tp_teo + slice_before

            if error_S:
                s_pick = s_pick + tp_teo + slice_before
            else:
                s_pick = s_pick + tp_teo + slice_before

            Sta_list.append(sta)
            P_list.append(round(p_pick,2))
            theoretical.append(tp_teo)
            S_list.append(round(s_pick,2))
            dist.append(round(distance,3))
            depths.append(depth)
            tslice_start_list.append(round(tp_teo+slice_before,2))
            tslice_stop_list.append(round(tp_teo+slice_after,2))
            del st_sta

    phases = DataFrame({'station' : Sta_list, 'P' : P_list, 
                        'P_theo' : theoretical, 'S' : S_list, 
                        'depth' : depths,'dist' : dist,
                        'tslice_start' : tslice_start_list,
                        'tslice_stop' : tslice_stop_list})
    print(phases)
    phases.to_pickle(os.path.join(root_crsmex,'tmp',directory,'phases.pkl'))

    if plotting:
        fig, ax = plt.subplots(nrows=int(Nsubplots), ncols=1, squeeze=False, sharex = True)
        fig.subplots_adjust(hspace=0)
        plt.setp(ax, xlim=(phases['P'].min()-5,phases['S'].max()+5))

        for m, row in enumerate(phases.sort_values(by=['dist']).itertuples()):
            stream.select(channel='HHZ', station = row.station).filter("highpass", freq=2.0)
            ax[m,0].plot(stream.select(channel='HHZ', station = row.station )[0].times(), 
            normalize(stream.select(channel='HHZ', station = row.station)[0].data),
                      linewidth=0.1,color='k',
                      label=sta)
            ax[m,0].axvline(row.tslice_start,color='black',ls='--')
            ax[m,0].axvline(row.tslice_stop,color='black',ls='-')
            ax[m,0].axvline(row.P,color='red',ls='--')
            ax[m,0].axvline(row.P_theo,color='green',ls='-', label = 'P_{theo}')
            ax[m,0].axvline(row.S,color='blue',ls='--')
            ax[m,0].autoscale(enable=True, axis='x', tight=True)
            ax[m,0].set_xlabel('time (s)')
            #ax[m,0].set_title('Station: ' + row.station,fontsize=16)
            ax[m,0].text(1.1*(phases['S'].max()+5), 0.2, row.station, fontsize= 14) 
            ax[m,0].text(phases['P'].min()-12 , 0.4, '%4.1f'%(row.dist*111.1) + 'km', fontsize= 8) 
            ax[m,0].grid(which='major')
            ax[m,0].grid(which='minor')
            ax[m,0].get_yaxis().set_visible(False)
            m += 1


                #ax[m,0].text(0.9*st_sta.select(channel='HHZ')[0].times().max(), 0.2, sta, fontsize= 14)
        #fig.tight_layout()
        fig.suptitle('Tweet id: ' + directory)
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
    #directory = '1587083891046752257'
    #plotting = True
    #print(os.path.join(root_crsmex,'tmp',directory,'*.sac'))
    phases = phase_picker(directory,plotting=plotting)
    #print(phases.sort_values(by=['dist']))

