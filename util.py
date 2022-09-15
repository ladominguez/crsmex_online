from datetime import datetime

def render_tweet_info(tweet):
	text = tweet.full_text
	content = text.split()
	if not content[0] == 'SISMO':
		raise ValueError('Tweet is not an earthquake. ' + text)
	for k, word in enumerate(content):
		if word == 'Magnitud':
			magnitude = content[k+1]
		elif '/' in word and 'http' not in word:
			date= '20' + word
		elif ':' in word and 'http' not in word:
			time_str = word
		elif word == 'Lat':
			latitude = content[k+1]
		elif word == 'Lon':
			longitude = content[k+1]
		elif word == 'Pf':
			depth = content[k+1]
		else:
			continue
	
	time = datetime.strptime(date + ',' + time_str, '%Y/%m/%d,%H:%M:%S')
	return (time, latitude, longitude, depth, magnitude)
