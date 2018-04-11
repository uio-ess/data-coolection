'''
Created on 11 Oct 2017

@author: clementderrez
'''

import numpy as np

import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm

import h5py
from time import sleep
import glob

DELAY = 600
#files = next(os.walk('.'))[2]

while True:
    plt.close("all")
    fig = plt.figure()
    ax = fig.gca(projection='3d')
    ax.set_title('spectrum timeline')
    ax.view_init(elev=20., azim=-35)
    files = glob.glob('spectra*.*')
    arr = []
    n = 1
    z = np.array([1.0 for point in files])
    for f in files:
        h5file = h5py.File(f, 'r')
        dataset = h5file.get('entry/data/data')
        arr = np.array(dataset)*n
        ax.plot(arr[0,:], arr[1,:], zs=n, zdir = 'z')
        ax.set_zlabel('file index')
        n+=1
        h5file.close()
    
    plt.show()
    sleep(DELAY)