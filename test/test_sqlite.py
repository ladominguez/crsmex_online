import sqlite3
from datetime import datetime

con = sqlite3.connect('catalog_backup.db')
cursor = con.cursor()
print('type(con): ', type(con))
print('type(cursor): ', type(cursor))

ID = 10
tweet_id = 1581813685726908417

get_previous_record_sql = '''SELECT intervals, dates, ids FROM repeaters WHERE ID = ?'''
get_twitter_info = '''SELECT datetime FROM twitter WHERE  tweet_id = ?'''

cursor.execute(get_twitter_info,(tweet_id,))
tweet_info = cursor.fetchone()

cursor.execute(get_previous_record_sql,(ID,))

update_sql = '''UPDATE repeaters SET no_repeaters = no_repeaters + 1,
                        intervals = intervals || ?,
                        dates = dates || ?,
                        ids = ids  || ? WHERE ID = ?'''

db_results = cursor.fetchone()
intervals, dates, ids = db_results
print(tweet_info)
print(db_results)
print('intervals: ', intervals.split(' ')[-1])
print('dates: ', dates.split(' ')[-1])
print('ids: ', ids.split(' ')[-1])

time_last = datetime.strptime(dates.split(' ')[-1], '%Y/%m/%d,%H:%M:%S.%f')
tweet_eq_time = datetime.strptime(tweet_info[0],'%Y/%m/%dT%H:%M:%S')
dt = tweet_eq_time - time_last
interval_new = '%.2f' % dt.total_seconds()
print('dt: ', interval_new)

cursor.execute(update_sql, (' ' + interval_new, ' ' + tweet_info[0].replace('T', ','), 
               ' ' + str(tweet_id), ID))
con.commit()
con.close()

