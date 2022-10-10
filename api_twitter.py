import tweepy as tw
import pandas as pd
import os
import json
import sqlite3
from util import *

# load configuration
config_file = open('config.json')
config = json.load(config_file) 

# your Twitter API key and API secret
my_api_key = os.environ["API_KEY_TWITTER"]
my_api_secret = os.environ["API_KEY_SECRET_TWITTER"]

auth = tw.OAuthHandler(my_api_key, my_api_secret)
api = tw.API(auth, wait_on_rate_limit=True)
userID = 'SismologicoMX'


tweets = api.user_timeline(screen_name=userID,
                                    count=500,
                                    include_rts = False,
                                    tweet_mode = 'extended')


# store the API responses in a list
tweets_copy = []
for tweet in tweets:
    tweets_copy.append(tweet)


# intialize the dataframe
tweets_df = pd.DataFrame()
tweets_list = []
# populate the dataframe
con = sqlite3.connect(config['database'])
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
        time, latitude, longitude, depth, magnitude = render_tweet_info(tweet)
        datetime = time.strftime("%Y/%m/%dT%H:%M:%S")
    except:
        continue

    tweets_df = pd.concat([tweets_df,pd.DataFrame({'tweet_id': tweet.id, 
                                'tweet_time': tweet.created_at,
                                'text': tweet.full_text}, index=[0])])
     
    print("====================================================================");
    print(tweet.full_text)
    print('type: ', type(tweet.id))
    print('time: ', datetime, ' Latitude: ', latitude, ' Longitude: ', longitude, ' depth: ', depth)
    print('mag: ', magnitude, ' tweet_id: ', tweet.id);
    entries = [datetime,   latitude, longitude, depth, magnitude, 0, True, tweet.id, False, 0]
    cursor.execute("SELECT rowid FROM catalog WHERE tweet_id = ?", (tweet.id,))
    db_result=cursor.fetchone()
    if db_result is not None:
        print('tweet: ', tweet.id, ' is in the databse.')
    else:
        new +=1
        print('Inserting')
        add_entry = '''INSERT INTO catalog(datetime, latitude, longitude, depth, mag, eq_id, tweet, tweet_id, repeater, sequence_id) VALUES (?,?,?,?,?,?,?,?,?,?);'''
        cursor.execute(add_entry,entries)
                                
    tweets_df = tweets_df.reset_index(drop=True)
cursor.execute("SELECT * FROM catalog")
results = cursor.fetchall()


con.commit()
con.close()
print('Entries: ', len(results))
print('Number of tweets: ', len(tweets_df))
print('New earthquakes: ', new)


