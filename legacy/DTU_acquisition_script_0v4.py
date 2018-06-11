#import visa
import epics
import logging
import sys
from epics import PV
import h5py
import time
import numpy as np
import scipy.optimize as opt
import os
#import matplotlib.pyplot as plt
from time import sleep
import astropy
from astropy.table import Table, Column, MaskedColumn

'''
Created on 26 Sep 2017
@author: cyrillethomas
@author: clementderrez

'''
os.environ['EPICS_MAX_ARRAY_BYTES']='15000000'
os.environ['EPICS_CA_ADDR_LIST']='10.0.19.247'
logging.basicConfig(filename='DUT_logger.log',level=logging.DEBUG)
logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')


def twoD_Gaussian(X, amplitude, xo, yo, sigma_x, sigma_y, theta, offset):
    x, y = X
    xo = float(xo)
    yo = float(yo)
    a = (np.cos(theta)**2)/(2*sigma_x**2) + (np.sin(theta)**2)/(2*sigma_y**2)
    b = -(np.sin(2*theta))/(4*sigma_x**2) + (np.sin(2*theta))/(4*sigma_y**2)
    c = (np.sin(theta)**2)/(2*sigma_x**2) + (np.cos(theta)**2)/(2*sigma_y**2)
    g = offset + amplitude*np.exp( - (a*((x-xo)**2) + 2*b*(x-xo)*(y-yo)+ c*((y-yo)**2)))
    return g.ravel()


def main():
    # define the time interval between shots
    minute = 20 # 60s / 3
    N_minutes = 1
    # delta_T in s 	
    delta_T = N_minutes * minute
    # number of shots in 8h shift
    NN = 9000
    
    save_image = PV('CAM1:HDF1:WriteFile')
    save_image_ROI = PV('CAM1:HDF2:WriteFile')

    save_spectrum_CCS100 = PV('CCS1:HDF1:WriteFile')
    save_spectrum_CCS200 = PV('CCS2:HDF1:WriteFile')
    
    logging.info('Configured and started')

    for ii in range (0, NN):

        print('iteration # = ', ii)
        print("push acquisition of the image + ROI ")
        save_image.put(1)
	save_image_ROI.put(1)

        # save spectra
        print("push acquisition of spectra ")
        save_spectrum_CCS100.put(1)
        save_spectrum_CCS200.put(1)
	
        #
        sleep(1)

        print("acquire image")
        logging.info('new image acquired')

        print('pause', delta_T, 's')
        sleep(delta_T)

if __name__ == '__main__':
    main()
