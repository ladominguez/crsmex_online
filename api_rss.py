from data_colector import *
import time as tt
import feedparser as fp
from html.parser import HTMLParser
import uuid
import pandas as pd


class Parser(HTMLParser):
  # method to append the start tag to the list start_tags.
  def handle_starttag(self, tag, attrs):
    global start_tags
    start_tags.append(tag)
    # method to append the end tag to the list end_tags.
  def handle_endtag(self, tag):
    global end_tags
    end_tags.append(tag)
  # method to append the data between the tags to the list all_data.
  def handle_data(self, data):
    global all_data
    all_data.append(data)
  # method to append the comment to the list comments.
  def handle_comment(self, data):
    global comments
    comments.append(data)

# Logging configuration
FORMAT = '%(asctime)-15s {%(filename)s:%(lineno)d} %(levelname)s - %(message)s'
log = logging.getLogger(name='CRSMEX')
log.setLevel(logging.INFO)
logging.basicConfig(format=FORMAT)

fh = logging.FileHandler(os.path.join(root_crsmex, 'logger.txt'))
fh.setFormatter(logging.Formatter(FORMAT))
fh.setLevel(logging.DEBUG)
log.addHandler(fh)

# SQL commands
add_entry = '''INSERT INTO rss(datetime, unixtime, latitude, 
                                        longitude, depth, mag,  
                                        data_downloaded, analyzed, repeater, 
                                        sequence_id) VALUES (?,?,?,?,?,?,?,?,?,?);'''

if __name__ == '__main__':
    con = sqlite3.connect(os.path.join(root_crsmex, config['database']))

    while True:
        print("====================="+tt.strftime("%Y/%M/%d %H:%M:%S", tt.localtime()) + "===========================")
        rss=fp.parse(config['rss_feed'])
        rss_df = pd.DataFrame()
        cursor = con.cursor()

        for entry in rss.entries:
            all_data = []
            start_tags = []
            end_tags = []
            comments = []
            parser = Parser()
            Html_Data = entry['summary_detail']['value']
            parser.feed(Html_Data)
            date = all_data[0].split()[0].split(':')[1]
            time = all_data[0].split()[1]
            latitude = all_data[1].split()[1].split('/')[0]
            longitude = all_data[1].split()[1].split('/')[1]
            depth = all_data[2].split()[1]
            mag = entry['title'].split(',')[0]
            id = int(date.replace('-','') + time.replace(':','') + latitude.replace('.',''))
            print('date: ', date + ',' + time + ' lat: ' + str(latitude) + ' lon: ' + str(longitude) + ' depth: ' + depth + ' mag: ' + mag + ' id: ' + str(id))
            rss_df = pd.concat([rss_df, pd.DataFrame({'id' : uuid.uuid4().int,
                                                      'date' : date,
                                                      'latitude' : latitude,
                                                      'longitude' : longitude,
                                                      'depth' : depth, 
                                                      'magnitude' : mag}, index=[0])])
            entries = [datetime, time_utc.timestamp(), latitude,
                       longitude, depth, mag,
                       False, False, False, 0]            

            cursor.execute("SELECT rowid FROM rss WHERE rss_id = ?", (id,))
            db_result = cursor.fetchone()
            if not db_result:

        tt.sleep(30)




