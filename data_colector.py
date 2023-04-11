from importlib.metadata import entry_points
from re import I, U
from subprocess import Popen, PIPE, DEVNULL, TimeoutExpired
from tkinter import W
from urllib.parse import _NetlocResultMixinBytes, _NetlocResultMixinStr
import pandas as pd
import sqlite3
import os
import glob
import json
import logging
from datetime import datetime, timedelta
from geopy.distance import great_circle
from util import load_configuration
from plotting_tools import plot_sequence_candidates

#p= Popen('/Users/antonio/bin/SSNstp',stdin=PIPE, stdout=DEVNULL, stderr=DEVNULL, bufsize=0)
# p.communicate(input.encode('ascii'))

# load configuration
config = load_configuration()
root_crsmex = os.environ["ROOT_CRSMEX"]
input="in " + config["stp_file_name"] + "\nexit\n"

# Logging configuration
FORMAT = '%(asctime)-15s {%(filename)s:%(lineno)d} %(levelname)s - %(message)s'
log = logging.getLogger(name='CRSMEX')
log.setLevel(logging.DEBUG)
logging.basicConfig(format=FORMAT)

fh = logging.FileHandler(os.path.join(root_crsmex, 'logger.txt'))
fh.setFormatter(logging.Formatter(FORMAT))
fh.setLevel(logging.DEBUG)
log.addHandler(fh)


def stp_generator():
    # Connecting to database
    con = sqlite3.connect(os.path.join(root_crsmex, config['database']))
    cursor = con.cursor()
    cmd_sql = r"SELECT datetime, latitude, longitude, depth, tweet_id, nearby_sta FROM twitter WHERE data_downloaded == 0;"
    df = pd.read_sql_query(cmd_sql, con)
    stations = pd.read_pickle(os.path.join(root_crsmex, config["stations"]))


    for index, entry in df.iterrows():

        eq_loc = (entry['latitude'], entry['longitude'])
        distance = []
        if not os.path.isdir(os.path.join(root_crsmex, 'tmp', entry['tweet_id'])):
            os.mkdir(os.path.join(root_crsmex, 'tmp', entry['tweet_id']))

        if not os.path.isfile(os.path.join(root_crsmex, 'tmp', entry['tweet_id'], 'get_data.stp')):
            fid = open(os.path.join(root_crsmex, 'tmp',
                                    entry['tweet_id'], 'get_data.stp'), 'w')
        else:
            continue # get_data.stp was generated although no data was downloaded.

        for n, station in stations.iterrows():
            sta_loc = (station['stla'], station['stlo'])
            distance.append(great_circle(eq_loc, sta_loc).km)
        stations['distance'] = distance
        starttime = datetime.strptime(
            entry['datetime'], '%Y/%m/%dT%H:%M:%S') - timedelta(seconds=config["before_time"])

        nearby_stations = stations.loc[stations['distance']
                                    <= config["max_dist"]]['station'].to_list()
        for close_sta in nearby_stations:
            stp_cmd = 'WIN IG ' + close_sta.strip() + ' HH_ ' + starttime.strftime('%Y/%m/%d,%H:%M:%S' +
                                                                                ' +' + str(config['record_length'])) + 's\n'
            fid.write(stp_cmd)
        
        update_nearby_sta = '''UPDATE twitter
                               SET nearby_sta = ?
                               WHERE tweet_id = ?'''
        cursor.execute(update_nearby_sta, (','.join(nearby_stations), entry['tweet_id']))
        con.commit()
    con.close
    return None

def data_colector():
    #con = sqlite3.connect(os.path.join(root_crsmex, config['database']))
    #cmd_sql = r"select datetime, latitude, longitude, depth, tweet_id, nearby_sta from twitter where data_downloaded == 0;"
    #df = pd.read_sql_query(cmd_sql, con)

    directories = os.listdir(os.path.join(root_crsmex,'tmp'))
    for directory in directories:
        if os.path.isdir(os.path.join(root_crsmex,'tmp',directory)):
            os.chdir(os.path.join(root_crsmex,'tmp',directory))
            if os.path.isfile(config['stp_file_name']):
                log.debug('Requesting data for ' + directory + ' ...')
                print('Requesting data for ' + directory + ' ...')
                p = Popen(config["SSNstp"],stdin=PIPE, stdout=DEVNULL, stderr=DEVNULL, bufsize=0) 
                try:
                    outs, err = p.communicate(input.encode('ascii'),timeout = config['timeout'])
                except TimeoutExpired:
                    p.kill()
                    log.info('Data requested for ' + directories + ' timeout. ')
                    print('Data requested for ' + directories + ' timeout. ')
    
                
               
    return None

def check_collected_data():
    con = sqlite3.connect(os.path.join(root_crsmex, config['database'])) 
    cursor = con.cursor()
    directories = os.listdir(os.path.join(root_crsmex,'tmp'))

    for directory in directories:
        cmd_sql = r"SELECT nearby_sta, tweet_id FROM twitter WHERE tweet_id= " + directory + ";"
        cursor.execute(cmd_sql)
        results = cursor.fetchall()
        if len(results) >= 2:
            raise NameError('Duplicated records with the same tweet id.')
        
        stations, tweet_id = results[0]
        Nsta=len(stations.split(','))
        files_found = glob.glob(os.path.join(root_crsmex,'tmp',tweet_id,'*.sac'))
        print('Expected: ', Nsta, ' tweet_id: ', tweet_id, ' sta_collected: ', str(len(files_found)/3), ' perc: ', str(len(files_found)*100/(3*Nsta)))
        
        if (len(files_found)/(Nsta*3)) >= 0.7:
            print('UPDATING: ', tweet_id)
            update_downloaded_data = '''UPDATE twitter
                                   SET data_downloaded = ?
                                   WHERE tweet_id = ?'''
            cursor.execute(update_downloaded_data, (True, tweet_id))
            con.commit()
    con.close()

    return None
        
def _reset_downnloads_in_database():
    '''
    Modifies the sql database so all the twitter appear undownloaded. For debugging purposes only.
    '''

    con = sqlite3.connect(os.path.join(root_crsmex, config['database']))
    cursor = con.cursor()
    cmd_sql = '''UPDATE twitter SET data_downloaded = ?
                 WHERE data_downloaded =?'''
    cursor.execute(cmd_sql, (False, True))
    log.debug('Reseting data_downloaded from database. ' + str(cursor.rowcount) + ' lines edited.') 
    con.commit()
    con.close()
    return None



def possible_sequences(tweet_id, r_max=50):
    con = sqlite3.connect(os.path.join(root_crsmex, config['database'])) 
    cursor = con.cursor()

    cmd_sql1 = '''SELECT latitude, longitude, nearby_sta FROM twitter WHERE data_downloaded == 1 AND tweet_id = '''  + str(tweet_id) + ''';''';
    cmd_sql2 = '''SELECT latitude, longitude, id FROM repeaters;'''
    #twitter = pd.read_sql_query(cmd_sql1, con)
    repeaters = pd.read_sql_query(cmd_sql2, con)    
    #cursor = con.cursor()
    cursor.execute(cmd_sql1)

    results = cursor.fetchall()
    if not results:
        #print(cmd_sql1)
        return []
    
    #for index1, tweet in twitter.iterrows():
    id_list = []
    tweet_lat, tweet_lon,  nearby_sta = results[0] 
    #print('Length repeaters: ', len(repeaters))
    for index2, repeat in repeaters.iterrows():
        eq_tweet = (tweet_lat, tweet_lon)
        eq_repeat = (repeat['latitude' ], repeat['longitude'])
        distance = great_circle(eq_tweet, eq_repeat).km
        #print(tweet['tweet_id'],distance)
        if distance <= r_max:
            #print(distance, repeat['ID'], tweet_id, eq_tweet)
            id_list.append(int(repeat['ID']))
        
    con.close()
    return id_list



if __name__ == '__main__':
    #stp_generator()
    #data_colector()

    #check_collected_data()
    #tweet_id=1582015080493092864
    repeating_list = possible_sequences(tweet_id, r_max = config['radius'])
    plot_sequence_candidates(tweet_id, repeating_list) 
    #_reset_downnloads_in_database()
