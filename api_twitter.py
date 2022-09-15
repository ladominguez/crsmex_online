import tweepy as tw
import pandas as pd
import os
from util import *

# your Twitter API key and API secret
my_api_key = os.environ["API_KEY_TWITTER"]
my_api_secret = os.environ["API_KEY_SECRET_TWITTER"]

auth = tw.OAuthHandler(my_api_key, my_api_secret)
api = tw.API(auth, wait_on_rate_limit=True)
userID = 'SismologicoMX'

tweets = api.user_timeline(screen_name=userID,
                                    count=100,
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
for tweet in tweets_copy:
    hashtags = []
    try:
        for hashtag in tweet.entities["hashtags"]:
            hashtags.append(hashtag["text"])
        text = api.get_status(id=tweet.id, tweet_mode='extended').full_text
    except:
        pass
    try:
        time, latitude, longitude, depth, magnitude = render_tweet_info(tweet)
    except:
        continue
    print(text)

    tweets_df = pd.concat([tweets_df,pd.DataFrame({'tweet_id': tweet.id, 
                                'tweet_time': tweet.created_at,
                                'text': tweet.full_text}, index=[0])])

                                
    tweets_df = tweets_df.reset_index(drop=True)
print(tweets_df.head())
