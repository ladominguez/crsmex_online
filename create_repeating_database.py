import sqlite3
import os
import json
from tqdm import tqdm

config_file = open('config.json')
config = json.load(config_file) 



def create_table(filename):
    """
    Creates a table ready to accept our data.

    write code that will execute the given sql statement
    on the database
    """
    con = sqlite3.connect(filename)
    create_table = """ CREATE TABLE catalog(
        ID          INTEGER PRIMARY KEY     AUTOINCREMENT,
        datetime    CHAR(22)                NOT NULL,
		latitude    FLOAT                   NOT NULL,
		longitude   FLOAT                   NOT NULL,
		depth       FLOAT                   NOT NULL,
		mag         FLOAT                   NOT NULL,
		eq_id       INTEGER                 NOT NULL
    )
    """
    con.execute(create_table)
    con.close()

if not os.path.isfile(config['database']):
	create_table(config['database'])	

con = sqlite3.connect(config['database'])
cursor = con.cursor()
with open(config['catalog'],'r') as f:
    for line in tqdm(f):
        entries = line.split()
        entries[0:2] = ['T'.join(entries[0:2])] # merges date and time columns
        add_entry = '''INSERT INTO catalog(datetime, latitude, longitude, depth, mag, eq_id) VALUES (?,?,?,?,?,?);'''
        cursor.execute(add_entry,entries)

con.commit()
con.close()



