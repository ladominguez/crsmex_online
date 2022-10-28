import matplotlib.pyplot as plt
#import numpy
import sqlite3
import pandas
import matplotlib.dates as md
from datetime import datetime
from util import load_configuration
import pytz
import pygmt
import os 
from collections import namedtuple
from numpy import arange
import geopy.distance

config = load_configuration()
root_crsmex = os.environ["ROOT_CRSMEX"]
half_box = 0.5 # For plotting box around the test earthquake
radius = config['radius'] # Search radius
stations = pandas.read_pickle(os.path.join(root_crsmex, config["stations"]))
sequence = namedtuple('sequence',['ID', 'latitude', 'longitude', 'mag', 'no_repeaters'])

def draw_circle(latitude_center,longitude_center ,radius = 50):
    azimuth = arange(0, 365, 2)
    lat_out = []
    lon_out = []
    for az in azimuth:
        P = geopy.distance.distance(kilometers=radius).destination((latitude_center, longitude_center), 
                                     bearing=az)
        lat_out.append(P.latitude)
        lon_out.append(P.longitude)
    return lat_out, lon_out

def plot_catalog(catalog_file_name, time_lenght=''):
    tnow = datetime.now(tz=pytz.UTC).strftime("%Y/%m/%dT%H:%M:%S")
    cmd_sql = r"select  *  from catalog where unixtime >= (select strftime('%s',(select datetime('now','-48 hour'))));"
    con = sqlite3.connect(catalog_file_name)
    df = pandas.read_sql_query(cmd_sql, con)

    time_x = pandas.to_datetime(df['datetime'], format='%Y/%m/%dT%H:%M:%S')
    mag_y = df['mag']
    fig = pygmt.Figure()
    with pygmt.config(MAP_GRID_PEN_PRIMARY='3p,black,--',
                      MAP_GRID_PEN_SECONDARY='3p,black,--',
                      FONT_ANNOT_SECONDARY='12p,Palatino-Roman,black',
                      FONT_ANNOT_PRIMARY='12p,Palatino-Roman,black',
                      FONT_LABEL='12p,Palatino-Roman,black',
                      FORMAT_CLOCK_MAP="hh:mm",
                      FORMAT_DATE_MAP="o dd,yyyy",
                      FORMAT_TIME_SECONDARY_MAP="abbreviated"):

        fig.basemap(
            projection="X12c/5c",
            region=[
                time_x.min(),
                time_x.max(),
                0,
                6
            ],
            frame=["WSen", "sxa1D", "pxa6Hf1Hg1H+lTime",
                   'sya1f0.5g0.5+lMagnitude']
        )

        for k, x_line in enumerate(time_x.to_list()):
            fig.plot(
                x=[x_line, x_line],
                y=[0, mag_y[k]],
                pen="0.5p",
                color="red3"
            )

        fig.plot(
            x=time_x.to_list(),
            y=mag_y,
            style="a0.4c",
            pen="1p",
            color="dodgerblue"
        )

    fig.show()


def plot_sequence_candidates(tweet_id, sequence_list):
    con = sqlite3.connect(os.path.join(root_crsmex, config['database']))
    cursor = con.cursor()
    cmd_sql1 = r"SELECT latitude, longitude FROM twitter WHERE tweet_id = " + str(tweet_id) + ';'
    cursor.execute(cmd_sql1)
    results = cursor.fetchone()
    latitude_eq, longitude_eq = results


    #ids = []
    #latitudes = []
    #longitudes = []
    #magnitudes = []
    #no_repeaters = []
    sequences = []
    for sequence_candidate in sequence_list:
        cmd_sql2 = r"SELECT ID, latitude, longitude, mag, no_repeaters  FROM repeaters WHERE ID = " + str(sequence_candidate) + ";"
        cursor.execute(cmd_sql2)
        results = cursor.fetchall()
        id, latitude, longitude, mag, no_repeaters = results[0]
        S = sequence(id, latitude, longitude, mag, no_repeaters)
        #ids.append(id)
        #latitudes.append(latitude)
        #longitudes.append(longitude)
        #magnitudes.append(mag)
        #no_repeaters.append(no_repeater)
        sequences.append(S)
   # sequences = pd.DataFrame({'id' : ids, 'latitude ' : latitudes, 'longitude' : longitude,
   #                           'magnitude' : magnitudes, 'no_repeaters' : no_repeater})
    print("N total: ", len(sequences))


    fig = pygmt.Figure()
    projection="M6i",
    region=[ longitude_eq - half_box,
             longitude_eq + half_box,
             latitude_eq - half_box,
             latitude_eq + half_box
            ]
         
    with pygmt.config(MAP_GRID_PEN_PRIMARY='3p,black,--',
                      MAP_GRID_PEN_SECONDARY='3p,black,--',
                      FONT_ANNOT_SECONDARY='12p,Palatino-Roman,black',
                      FONT_ANNOT_PRIMARY='12p,Palatino-Roman,black',
                      FONT_LABEL='12p,Palatino-Roman,black'):

        fig.basemap(projection = projection, 
                    region= region,
                    frame=["af", f"WSen"])
        fig.coast(land="gray88", 
                  water="white", 
                  shorelines="1p,black")
        fig.plot(x = longitude_eq, y = latitude_eq,  style = "a0.4i", color = "red", pen = "1p,black")

        # Plotting candidates
        pygmt.makecpt(cmap = "google/turbo", series = "2/8/1")
        for s in sequences:
            fig.plot(x=s.longitude, y=s.latitude, style="c0.2i", cmap = True, zvalue = s.no_repeaters, pen = "1p,black")
    
        # Plotting circle
        lat_circle, lon_circle = draw_circle(latitude_eq, longitude_eq, radius = radius)
        fig.plot(x = lon_circle, y = lat_circle, pen = "1p,black,--")
        lat_circle, lon_circle = draw_circle(latitude_eq, longitude_eq, radius = radius*0.5)
        fig.plot(x = lon_circle, y = lat_circle, pen = "1p,black,--")
        P1 = geopy.distance.distance(kilometers=radius).destination((latitude_eq, longitude_eq), bearing=45)
        fig.text(x = P1.longitude, y = P1.latitude, text = str(radius) + 'km', offset = "0.5c", font="12p,Helvetica-Bold") 
        P1 = geopy.distance.distance(kilometers=radius/2).destination((latitude_eq, longitude_eq), bearing=45)
        fig.text(x = P1.longitude, y = P1.latitude, text = str(radius/2) + 'km', offset = "0.5c", font="12p,Helvetica-Bold") 
        
        # Plotting SSN stations
        fig.plot(x = stations['stlo'].tolist(), y = stations['stla'].tolist(),  color = "red",
                 style = "t0.2i", pen = "1p,black")
        
        fig.text(x = stations['stlo'].tolist(), y = stations['stla'].tolist(),
                 text = stations['station'].tolist(), offset = "0.75c/0c")
                
        
        fig.plot(data = './inputs/trench.gmt', style="f0.8i/0.15i+l+t", pen="2p,black", color="gray69")
        fig.plot(data = './inputs/isolines/isoline20.txt ', style="qd4i", label="20 km", pen="1p,black,--")
        fig.plot(data = './inputs/isolines/isoline20.txt ', style="qd4i", label="40 km", pen="1p,black,--")
        fig.plot(data = './inputs/isolines/isoline20.txt ', style="qd4i", label="60 km", pen="1p,black,--")
        fig.text(x = longitude_eq, y = latitude_eq, text = 'Tweet: ' + str(tweet_id), offset = "0.75c", font="12p,Helvetica-Bold")
        fig.colorbar()
        
    fig.savefig('./img/possible_sequences_' + str(tweet_id) + '.png')

    #    
