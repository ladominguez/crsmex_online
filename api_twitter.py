import tweepy as tw
import pandas as pd
import logging
import os
import platform
import time as tt
import json
import sqlite3
from util import *
from datetime import datetime
import pytz

Tweets_max = 50
# your Twitter API key and API secret
my_api_key = os.environ["API_KEY_TWITTER"]
my_api_secret = os.environ["API_KEY_SECRET_TWITTER"]
root_crsmex = os.environ["ROOT_CRSMEX"]


# load configuration
config_file = open(os.path.join(root_crsmex, 'config.json'))
config = json.load(config_file)
local = pytz.timezone(config['time_zone'])

# Logging configuration
FORMAT = '%(asctime)-15s {%(filename)s:%(lineno)d} %(levelname)s - %(message)s'
log = logging.getLogger(name='CRSMEX')
log.setLevel(logging.INFO)
logging.basicConfig(format=FORMAT)

fh = logging.FileHandler(os.path.join(root_crsmex, 'logger.txt'))
fh.setFormatter(logging.Formatter(FORMAT))
fh.setLevel(logging.DEBUG)
log.addHandler(fh)

if platform.node == 'ubuntu-1cpu-1gb-us-nyc1':  # ubuntu-1cpu-1gb-us-nyc1 upcloud server
    from systemd.journal import JournalHandler
    log.addHandler(JournalHandler())
    log.setLevel(logging.DEBUG)

userID = 'SismologicoMX'

while True:
    auth = tw.OAuthHandler(my_api_key, my_api_secret)
    api = tw.API(auth, wait_on_rate_limit=True)
    log.info('Reading tweets.')
    tweets = api.user_timeline(screen_name=userID,
                               count=Tweets_max,
                               include_rts=False,
                               tweet_mode='extended')

    # store the API responses in a list
    tweets_copy = []
    for tweet in tweets:
        tweets_copy.append(tweet)

    # intialize the dataframe
    tweets_df = pd.DataFrame()
    tweets_list = []
    # populate the dataframe
    con = sqlite3.connect(os.path.join(root_crsmex, config['database']))
    cursor = con.cursor()
    print('Tweet copy: ', type(tweets_copy))

    new = 0
    for tweet in reversed(tweets_copy):
        hashtags = []
        try:
            for hashtag in tweet.entities["hashtags"]:
                hashtags.append(hashtag["text"])
            text = api.get_status(id=tweet.id, tweet_mode='extended').full_text
        except:
            pass
        try:
            time_utc, latitude, longitude, depth, magnitude = render_tweet_info(
                tweet, config['time_zone'])
            datetime = time_utc.strftime("%Y/%m/%dT%H:%M:%S")
        except:
            continue

        tweets_df = pd.concat([tweets_df, pd.DataFrame({'tweet_id': tweet.id,
                                                        'tweet_time': tweet.created_at,
                                                        'text': tweet.full_text}, index=[0])])

        print("====================================================================")
        print(tweet.full_text)
        print('type: ', type(tweet.id))
        print('time: ', datetime, ' Latitude: ', latitude,
              ' Longitude: ', longitude, ' depth: ', depth)
        print('mag: ', magnitude, ' tweet_id: ', tweet.id)
        entries = [datetime, time_utc.timestamp(), latitude,
                   longitude, depth, magnitude,
                   tweet.id, tweet.created_at, tweet.full_text,
                   False, False, False, 0]

        cursor.execute(
            "SELECT rowid FROM twitter WHERE tweet_id = ?", (tweet.id,))
        db_result = cursor.fetchone()
        if db_result is not None:
            print('tweet: ', tweet.id, ' is in the databse.')
        else:
            new += 1
            print('Inserting')
            add_entry = '''INSERT INTO twitter(datetime, unixtime, latitude, 
                                               longitude, depth, mag, 
                                               tweet_id, post_time, tweet_text, 
                                               data_downloaded, analyzed, repeater, 
                                               sequence_id) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?);'''
            cursor.execute(add_entry, entries)

        tweets_df = tweets_df.reset_index(drop=True)
    cursor.execute("SELECT * FROM catalog")
    Nc = len(cursor.fetchall())
    cursor.execute("SELECT * FROM twitter")
    Nt = len(cursor.fetchall())

    con.commit()
    con.close()
    log.info('Tweets: %d - new earthquakes: %d, Eq. in catalog: %d, Total Tweets: %d, Total: %d',
             len(tweets_df), new, Nc, Nt, Nt+Nc)
    tt.sleep(900)
#log.info('Number of tweets: %d ', len(tweets_df), 'New earthquakes: ', new, 'Events in the database: ', len(results))
