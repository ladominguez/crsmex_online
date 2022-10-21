import sqlite3
import os
import json
import time
import pytz
from datetime import datetime
from tqdm import tqdm

config_file = open('../config.json')
config = json.load(config_file)


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
    con.close()

print(config['database'])
if not os.path.isfile(config['database']):
    create_table(config['database'])

con = sqlite3.connect(config['database'])
cursor = con.cursor()
with open(config['catalog'], 'r') as f:
    for line in tqdm(f):
        entries = line.split()
        entries[0:2] = ['T'.join(entries[0:2])]  # merges date and time columns
        unixtime = datetime.strptime(
            entries[0], "%Y/%m/%dT%H:%M:%S.%f").replace(tzinfo=pytz.UTC).timestamp()
        entries.insert(1, unixtime)
        entries.append(False)  # Set repeater to false at the beginning
        entries.append(None)  # Set sequence_id to None
        add_entry = '''INSERT INTO catalog(datetime, unixtime, latitude, longitude, depth, mag, eq_id, repeater, sequence_id) VALUES (?,?,?,?,?,?,?,?,?);'''
        cursor.execute(add_entry, entries)

con.commit()
con.close()
