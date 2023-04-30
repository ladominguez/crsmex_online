from data_colector import *
import time as tt
import feedparser as fp
from html.parser import HTMLParser

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

if __name__ == '__main__':
    while True:
        print("====================="+tt.strftime("%Y/%M/%d %H:%M:%S", tt.localtime()) + "===========================")
        rss=fp.parse(config['rss_feed'])
        start_tags = [] 
        end_tags = []
        all_data = []
        comments = []
        parser = Parser()
        for entry in rss.entries:
            Html_Data = entry['summary_detail']['value']
            parser.feed(Html_Data)
            date = all_data[0].split()[0].split(':')[1]
            time = all_data[0].split()[1]
            latitude = all_data[1].split()[1].split('/')[0]
            longitude = all_data[1].split()[1].split('/')[1]
            depth = all_data[2].split()[1]
            mag = entry['title'].split(',')[0]
            print('date: ', date + ',' + time + ' lat: ' + str(latitude) + ' lon: ' + str(longitude) + ' depth: ' + depth + ' mag: ' + mag)
        tt.sleep(30)




