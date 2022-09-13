import tweepy as tw
import pandas as pd
import os

# your Twitter API key and API secret
my_api_key = os.environ["API_KEY_TWITTER"]
my_api_secret = os.environ["API_KEY_SECRET_TWITTER"]

auth = tw.OAuthHandler(my_api_key, my_api_secret)
api = tw.API(auth, wait_on_rate_limit=True)

search_query = "SISMO @SismologicoMX"
# get tweets from the API
tweets = tw.Cursor(api.search_tweets,
              q=search_query,
              lang="es",
              since="2022-09-01").items(50)

# store the API responses in a list
tweets_copy = []
for tweet in tweets:
    tweets_copy.append(tweet)

print("Total Tweets fetched:", len(tweets_copy))


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

    print('text:', text)	
    pd.concat([tweets_df, pd.DataFrame({'user_name': tweet.user.name,
                                               'user_location': tweet.user.location,\
                                               'user_description': tweet.user.description,
                                               'user_verified': tweet.user.verified,
                                               'date': tweet.created_at,
                                               'text': text,
                                               'hashtags': [hashtags if hashtags else None],
                                               'source': tweet.source})])
#    tweets_df = tweets_df.reset_index(drop=True)

# show the dataframe
print(tweets_df.head())
