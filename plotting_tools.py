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


config = load_configuration()
root_crsmex = os.environ["ROOT_CRSMEX"]

sequence = namedtuple('sequence',['ID', 'latitude', 'longitude', 'mag', 'no_repeaters'])

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

    sequences = []
    for sequence_candidate in sequence_list:
        cmd_sql = r"SELECT ID, latitude, longitude, mag, no_repeaters  FROM repeaters WHERE ID = " + str(sequence_candidate) + ";"
        cursor.execute(cmd_sql)
        results = cursor.fetchall()
        id, latitude, longitude, mag, no_repeaters = results[0]
        S = sequence(id, latitude, longitude, mag, no_repeaters)
        print('======')
        print('ID: ', S.ID)
        print('lat: ', S.latitude)
        print('lon: ', S.longitude)
        print('mag: ', S.mag)
        print('N: ', S.no_repeaters)



    #fig = pygmt.Figure()
    #with pygmt.config(MAP_GRID_PEN_PRIMARY='3p,black,--',
    #                  MAP_GRID_PEN_SECONDARY='3p,black,--',
    #                  FONT_ANNOT_SECONDARY='12p,Palatino-Roman,black',
    #                  FONT_ANNOT_PRIMARY='12p,Palatino-Roman,black',
    #                  FONT_LABEL='12p,Palatino-Roman,black',
    #                  FORMAT_CLOCK_MAP="hh:mm",
    #                  FORMAT_DATE_MAP="o dd,yyyy",
    #                  FORMAT_TIME_SECONDARY_MAP="abbreviated"):

    #    fig.basemap(
    #        projection="X12c/5c",
    #        region=[
    #            time_x.min(),
    #            time_x.max(),
    #            0,
    #            6
    #        ],
    #        frame=["WSen", "sxa1D", "pxa6Hf1Hg1H+lTime",
    #               'sya1f0.5g0.5+lMagnitude']
    #    )
