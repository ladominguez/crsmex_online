from data_colector import *
import time as tt
import feedparser as fp
from html.parser import HTMLParser
import uuid
import pandas as pd
from util import get_utc_time


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
                                        longitude, depth, mag, rss_id, 
                                        data_downloaded, analyzed, repeater) VALUES (?,?,?,?,?,?,?,?,?,?);'''

if __name__ == '__main__':
    con = sqlite3.connect(os.path.join(root_crsmex, config['database']))

    while True:
        print("====================="+tt.strftime("%Y/%M/%d %H:%M:%S", tt.localtime()) + "===========================")
        rss=fp.parse(config['rss_feed'])
        rss_df = pd.DataFrame()
        cursor = con.cursor()
        
        new_entries = 0
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
            id = int(date.replace('-','') + time.replace(':','') + "{:5.2f}".format(float(latitude)).replace('.','')) #latitude.replace('.',''))
            rss_df = pd.concat([rss_df, pd.DataFrame({'id' : uuid.uuid4().int,
                                                      'date' : date,
                                                      'latitude' : latitude,
                                                      'longitude' : longitude,
                                                      'depth' : depth, 
                                                      'magnitude' : mag}, index=[0])])
            datetime_str = date + ',' + time
            time_utc = get_utc_time(datetime_str,config["time_zone"])
            datetime_utc_str = time_utc.strftime("%Y/%m/%dT%H:%M:%S")
            
            entries = [datetime_utc_str, time_utc.timestamp(), latitude,
                       longitude, depth, mag, id,
                       False, False, False]            

            cursor.execute("SELECT rowid FROM rss WHERE rss_id = ?", (id,))
            db_result = cursor.fetchone()
            if not db_result:
               print('ADDING: date local: ', date + ',' + time + ' date_utc: ' + datetime_utc_str + ' lat: ' + str(latitude) + ' lon: ' + str(longitude) + ' depth: ' + depth + ' mag: ' + mag + ' id: ' + str(id))
               print(entries)
               cursor.execute(add_entry, entries)
               new_entries += 1

        log.debug(new_entries, " added to the database.")
        con.commit()
        #con.close()

        #print('Generating stp files: ')
        #stp_generator_rss()
        #print('Collecting data.')
        #data_colector_rss()
        #check_collected_data_rss()

        directories = glob.glob("./tmp/[0-9]*")
        for directory in directories:
            rss_id = directory.split('/')[2]
            print('rss: ', rss_id)
            repeating_list = possible_sequences_rss(rss_id, r_max = config['radius'])
            if repeating_list:
                print('list: ', repeating_list)
                print(rss_id, repeating_list)
                find_new_repeaters_rss(rss_id, repeating_list, plotting = False)
        tt.sleep(config["waiting_time"])




