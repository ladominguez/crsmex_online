import pandas as pd

stnm      = ['CAIG', 'PNIG', 'PLIG', 'ZIIG', 'MMIG', 'TLIG', 'OXIG', 'MEIG', 'ARIG', 'DAIG', 'CRIG', 'PEIG', 'YOIG', 'TXIG', 'MGIG']
stla      = [17.0478,
             16.3923,
             18.3923,
             17.6067,
             18.2885,
             17.5627,
             17.0726,
             17.9249,
             18.2805,
             17.021298,
             16.736338,
             15.998617,
             16.856545,
             17.2532217,
             17.233614
             ]


stlo      = [-100.2673,
              -98.1271,
              -99.5023,
             -101.4650,
             -103.3456,
              -98.5665,
              -96.7330,
              -99.6197,
             -100.3475,
              -99.65069,
              -99.131171,
              -97.1472,
              -97.54565,
              -97.7676667,
              -98.633759
              ]

data = {'station' : stnm,
        'stla' : stla,
		'stlo' : stlo
		}

df = pd.DataFrame(data)
print(df)

df.to_pickle('../dat/stations.pkl')
