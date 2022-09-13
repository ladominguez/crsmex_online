import obspy as ob
import glob
import os
import h5py
import pandas as pd
import numpy as np
#from pprint import pprint

root = '/Users/antonio/Dropbox/BSL/CRSMEX/Dendrograms/2020AGO07/sequence_xc9500_coh9500'
input1 = 'locmag.dat'
input2 = 'station_ids.info'
output = 'crsmex.h5'
colnames = ['date', 'time', 'latitude', 'longitude', 'depth', 'mag', 'id']
types = {'data': 'string',
         'time': 'string',
         'latitude': np.float64,
         'longitude': np.float64,
         'depth': 'float',
         'mag': 'float',
         'id': 'string'}

ls_dir = [name for name in glob.glob(root+'/seq*') if os.path.isdir(os.path.join('.', name))]
ls_dir.sort()

with h5py.File('hdf5_groups.h5', 'w') as hdf:
    groups = {}
    waveforms = {}
    for key, directory in enumerate(ls_dir):
        sequence = directory.split('/')[-1]
        df = pd.read_csv(directory + '/' + input1, delim_whitespace=True,
               names=colnames, dtype=types)
        sta = pd.read_csv(directory + '/' + input2, names=['station'])
        N = int(sequence.split('_N')[1])
        

        print(sequence, N)
        groups[key] = hdf.create_group(sequence)
        groups[key].create_dataset('latitudes', data=np.array(df['latitude']))
        groups[key].create_dataset('longitudes', data=np.array(df['longitude']))
        groups[key].create_dataset('magnitudes', data=np.array(df['mag']))
        groups[key].create_dataset('depth', data=np.array(df['depth']))
        groups[key].create_dataset('id', data=list(df['id']))
        groups[key].create_dataset('datetime', data=list(df['date'] + 'T' + df['time']))
        groups[key].create_dataset('stations', data=list(sta['station']))        
        groups[key].attrs['N'] = N
        groups[key].attrs['latitude'] = df['latitude'].mean()
        groups[key].attrs['longitude'] = df['longitude'].mean()
        groups[key].attrs['depth'] = df['depth'].mean()

        for k, sta in enumerate(list(sta['station'])):
            waveforms[k] = hdf.create_group(sequence + '/' + sta)
            sac = ob.read(os.path.join(directory, 'raw', '*' + sta + '*.sac'))
            w = {}
            for j, tr in enumerate(sac):
                w[j] = waveforms[k].create_dataset('waveform' + '%02d' % (j), data=tr.data)
                w[j].attrs['npts'] = tr.stats.npts
                w[j].attrs['delta'] = tr.stats.delta
                w[j].attrs['b'] = tr.stats.sac.b
                w[j].attrs['kcmpnm'] = tr.stats.sac.kcmpnm



        