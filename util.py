from datetime import datetime
import pytz

<<<<<<< HEAD
def render_tweet_info(tweet, t_zone):
	text = tweet.full_text
	content = text.split()
	if not content[0] == 'SISMO':
		raise ValueError('Tweet is not an earthquake. ' + text)
	if 'http' in text:
		raise ValueError('Earthquake already reported.')
	for k, word in enumerate(content):
		if word == 'Magnitud':
			magnitude = content[k+1]
		elif '/' in word and 'http' not in word:
			date= '/'.join(['20'+word.split('/')[2],word.split('/')[1],word.split('/')[0]])
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
	
	time_local = datetime.strptime(date + ',' + time_str, '%Y/%m/%d,%H:%M:%S')
	time_utc = pytz.timezone(t_zone).localize(time_local, is_dst=None).astimezone(pytz.utc)
	return (time_utc, latitude, longitude, depth, magnitude)
=======

def render_tweet_info(tweet, t_zone):
    text = tweet.full_text
    content = text.split()
    if not content[0] == 'SISMO':
        raise ValueError('Tweet is not an earthquake. ' + text)
    if 'http' in text:
        raise ValueError('Earthquake already reported.')
    for k, word in enumerate(content):
        if word == 'Magnitud':
            magnitude = content[k+1]
        elif '/' in word and 'http' not in word:
            date = '/'.join(['20'+word.split('/')[2],
                             word.split('/')[1], word.split('/')[0]])
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

    time_local = datetime.strptime(date + ',' + time_str, '%Y/%m/%d,%H:%M:%S')
    time_utc = pytz.timezone(t_zone).localize(
        time_local, is_dst=None).astimezone(pytz.utc)
    return (time_utc, latitude, longitude, depth, magnitude)
>>>>>>> get_data_from_stp
