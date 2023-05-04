import sqlite3
import os
import json
import time
from tkinter import W
import pytz
from datetime import datetime
from tqdm import tqdm

config_file = open('../config.json')
config = json.load(config_file)
root_crsmex = os.environ["ROOT_CRSMEX"]

def create_table(filename):
    """
    Creates a table ready to accept our data.

    write code that will execute the given sql statement
    on the database
    """
    con = sqlite3.connect(filename)
    create_table_catalog = """ CREATE TABLE catalog(
        ID          INTEGER PRIMARY KEY     AUTOINCREMENT,
        datetime    CHAR(22)                NOT NULL,
		unixtime    FLOAT                   NOT NULL,
		latitude    FLOAT                   NOT NULL,
		longitude   FLOAT                   NOT NULL,
		depth       FLOAT                   NOT NULL,
		mag         FLOAT                   NOT NULL,
		eq_id       INTEGER                 NOT NULL,
        repeater    BOOLEAN                 NOT NULL,
        sequence_id INTEGER
    )
    """
    con.execute(create_table_catalog)
    con.commit()

    create_table_twitter = """ CREATE TABLE twitter(
        ID          INTEGER PRIMARY KEY     AUTOINCREMENT,
        datetime    CHAR(22)                NOT NULL,
		unixtime    FLOAT                   NOT NULL,
		latitude    FLOAT                   NOT NULL,
		longitude   FLOAT                   NOT NULL,
		depth       FLOAT                   NOT NULL,
		mag         FLOAT                   NOT NULL,
        tweet_id    VARCHAR(30)             NOT NULL,
		post_time   CHAR(22)                NOT NULL,
		tweet_text  TEXT                    NOT NULL,
		data_downloaded BOOLEAN             NOT NULL,
		analyzed        BOLLEAN             NOT NULL,
        repeater    BOOLEAN                 NOT NULL,
        sequence_id INTEGER,
		nearby_sta TEXT
	    
    )
    """
    con.execute(create_table_twitter)
    con.commit()

    create_table_rss = """ CREATE TABLE rss(
        ID          INTEGER PRIMARY KEY     AUTOINCREMENT,
        datetime    CHAR(22)                NOT NULL,
		unixtime    FLOAT                   NOT NULL,
		latitude    FLOAT                   NOT NULL,
		longitude   FLOAT                   NOT NULL,
		depth       FLOAT                   NOT NULL,
		mag         FLOAT                   NOT NULL,
        rss_id    VARCHAR(30)             NOT NULL,
		data_downloaded BOOLEAN             NOT NULL,
		analyzed        BOLLEAN             NOT NULL,
        repeater    BOOLEAN                 NOT NULL,
        sequence_id INTEGER,
		nearby_sta TEXT
	    
    )
    """
    con.execute(create_table_rss)
    con.commit()

    create_table_repeaters = """ CREATE TABLE repeaters(
	     ID            INTEGER PRIMARY KEY     AUTOINCREMENT,
		 latitude      FLOAT                   NOT NULL,
		 longitude     FLOAT                   NOT NULL,
		 depth         FLOAT                   NOT NULL,
		 mag           FLOAT                   NOT NULL,
		 no_repeaters  INTEGER                 NOT NULL,
		 intervals     TEXT                    NOT NULL,
		 dates         TEXT                    NOT NULL,
		 ids           TEXT                    NOT NULL
	)
	"""
    con.execute(create_table_repeaters)
    con.commit()
    con.close()
    return None

def fill_catalog():
    con = sqlite3.connect(config['database'])
    cursor = con.cursor()
    add_entry = '''INSERT INTO catalog(datetime, unixtime, 
                               latitude, longitude, depth, mag, 
                               eq_id, repeater, sequence_id) 
                               VALUES (?,?,?,?,?,?,?,?,?);'''

    num_lines = sum(1 for line in open(config['catalog'],'r'))
    with open(config['catalog'], 'r') as f:
        for k, line in enumerate(tqdm(f,  total=num_lines)):
            entries = line.split()
            entries[0:2] = ['T'.join(entries[0:2])]  # merges date and time columns
            unixtime = datetime.strptime(
                entries[0], "%Y/%m/%dT%H:%M:%S.%f").replace(tzinfo=pytz.UTC).timestamp()
            entries.insert(1, unixtime)
            entries.append(False)  # Set repeater to false at the beginning
            entries.append(None)  # Set sequence_id to None
            cursor.execute(add_entry, entries)

    con.commit()
    con.close()

    return None

def fill_repeaters():
    con = sqlite3.connect(config['database'])
    cursor = con.cursor()
    add_entry = '''INSERT INTO repeaters(latitude, longitude, depth, mag, 
                               no_repeaters, intervals, dates, ids) 
                               VALUES (?,?,?,?,?,?,?,?);'''

    with open(os.path.join(root_crsmex,config["input_crsmex"]), 'r') as f:
        for line in f:
            entry = []
            line_split = line.split(";")
            location = [float(m.strip()) for m in line_split[0].split()]
            entry.append(location[1]) # latitude
            entry.append(location[2]) # longitude
            entry.append(location[3]) # depth
            entry.append(location[4]) # magnitude
            entry.append(int(line_split[1])) # No. repeaters
            entry.append(line_split[2].strip()) # intervals in seconds
            entry.append(line_split[3].strip()) # dates
            entry.append(line_split[4].strip()) # ids
            cursor.execute(add_entry, entry)

    con.commit()
    con.close()
            


    return None


if __name__ == '__main__':
    print(config['database'])
    if not os.path.isfile(config['database']):
        create_table(config['database'])
    else:
        print('Database exists.')
        exit()

    
    fill_catalog();
    fill_repeaters()

