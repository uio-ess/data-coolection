'''
Created on 11 Oct 2017
Plot the spectrum intensity result from the irradiated samples 
@author: clementderrez
@author: cyrillethomas

'''

import numpy as np
import matplotlib.pyplot as plt
#from mpl_toolkits.mplot3d import Axes3D
#from matplotlib import cm
import os
import h5py
from time import sleep
import glob

DELAY = 5

while True:
    plt.close("all")
    fig = plt.figure()
    fig.suptitle('max spectr100 values')
    #ax = fig.gca(projection='3d')
    #ax.set_title('spectrum timeline')
    #ax.view_init(elev=20., azim=-35)
    file = 'HV10_test_run123:14:14.hdf5'
    #files = glob.glob('spectra*.*')
    arr = []
    spectr_max = []
    index_max = []
    peak_lambda = [] 

    #n = 1
    #z = np.array([1.0 for point in files])
    h5file = h5py.File(file, 'r')
    for t in range(0,20):
        try:
            h5groups = sorted(list(h5file.keys()))
        except:
            continue
        else:
            break
    print(h5groups)

    for gr in h5groups:
        #h5file = h5py.File(f, 'r')
        dataset = h5file.get('/'+ str(gr) + '/dataset_spectr100')
        dataset_lam = h5file.get('/'+ str(gr) + '/dataset_wavelength_200')
        arr = np.array(dataset)
        lambda_0 = np.array(dataset_lam)
        try:
            spectr_max = np.append(spectr_max,np.amax(arr[0:3645]))
            idx = np.argmax(arr[0:3645])
            index_max  = np.append(index_max,idx)
            lambda_01 = lambda_0[idx]
            peak_lambda = np.append(peak_lambda,lambda_01)
        except:
            continue
        #ax.plot(arr[0,:], arr[1,:], zs=n, zdir = 'z')
        #ax.set_zlabel('file index')
    
    h5file.close()
    print('max spectr',spectr_max)
    print('lambda_0',lambda_0)
    print('index', index_max)
    print('peaks' , peak_lambda)
    
    plt.subplot(211)
    plt.plot(spectr_max)
    plt.subplot(212)
    plt.plot(peak_lambda)
    
    plt.show()
    sleep(DELAY)
