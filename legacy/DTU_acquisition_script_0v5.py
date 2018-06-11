#!/usr/bin/env python3.4
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
TIMESTAMP = time.strftime("%H:%M:%S")
TIMESTAMP1 = time.strftime("%Y-%m-%d-%H:%M:%S")
FILENAME = 'HV10-2>-' + TIMESTAMP1 + '.hdf5'

# metadata  on the setup
cam_F_number =  4  

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
    minute = 5 # 60s / 3
    N_minutes = 1
    # delta_T in s 	
    delta_T = N_minutes * minute
    delta_T1 = 3
    # number of shots in 8h shift
    NN = 1800
    
    spectr_100=[]
    spectr_200=[]

    # open PV handles 
    # save_image = PV('CAM1:HDF1:WriteFile')
    # save_image_ROI = PV('CAM1:HDF2:WriteFile')

    # save_spectrum_CCS100 = PV('CCS1:HDF1:WriteFile')
    # save_spectrum_CCS200 = PV('CCS2:HDF1:WriteFile')

    start_cam_acquisition = PV('CAM1:det1:Acquire')

    get_image = PV('CAM1:image1:ArrayData')
    get_image_ROI = PV('CAM1:image2:ArrayData')
    
    get_CCS200_spectr = PV('CCS1:trace1:ArrayData')
    get_CCS200_wavel = PV('CCS1:det1:TlWavelengthData_RBV')


    get_CCS100_spectr = PV('CCS2:trace1:ArrayData')
    get_CCS100_wavel = PV('CCS2:det1:TlWavelengthData_RBV')

    get_CCS200_acq_time = PV('CCS1:det1:AcquireTime_RBV')
    get_CCS100_acq_time = PV('CCS2:det1:AcquireTime_RBV')
  
    get_cam_acq_time = PV('CAM1:det1:AcquireTime_RBV')
    get_cam_gain = PV('CAM1:det1:Gain_RBV')
    get_cam_timespt = PV('CAM1:image1:TimeStamp_RBV')
    get_cam_X = PV('CAM1:det1:ArraySizeX_RBV')
    get_cam_Y = PV('CAM1:det1:ArraySizeY_RBV')
    get_cam_ROI_X = PV('CAM1:image2:ArraySize0_RBV')
    get_cam_ROI_Y = PV('CAM1:image2:ArraySize1_RBV')


    get_picoscop_trace = PV('PICO1:trace1:ArrayData')
    get_picoscop_coupling = PV('PICO1:det1:A:Coupling_RBV')
    get_picoscop_range = PV('PICO1:det1:A:Range_RBV')
    get_picoscop_time_base = PV('PICO1:det1:TimeBase_RBV')
    get_picoscop_Nsampl = PV('PICO1:det1:NumSamples_RBV')
    get_picoscop_T_interval = PV('PICO1:det1:TimeInterval_RBV')



    get_picoscop_timespt = PV('PICO1:trace1:TimeStamp_RBV')
    get_sp_100_timespt = PV('CCS2:trace1:TimeStamp_RBV')
    get_sp_200_timespt = PV('CCS1:trace1:TimeStamp_RBV')


    logging.info('Configured and started')
    
    f=h5py.File(FILENAME,'w')
    f.attrs['file_name']        = FILENAME
    f.attrs['file_time']        = TIMESTAMP
    f.attrs['HDF5_Version']     = h5py.version.hdf5_version

    for ii in range (0, NN):

        if ii>0:
            f=h5py.File(FILENAME,'a')
        print('iteration # = ', ii)
        print("acquisition of the image + ROI ")
        my_grp=f.create_group(str(ii))
                
        # save_image.put(1)
        # save_image_ROI.put(1)
        print('camera on')
        start_cam_acquisition.put(1)

        #start_cam_acquisition.put(1)
        sleep(0.2)
        image_0 = get_image.get(timeout=10)
        image_0_ROI = get_image_ROI.get(timeout=10)

        time_cam = get_cam_acq_time.get(timeout=10)
        gain_cam = get_cam_gain.get(timeout=10)


        # save spectra
        #print("acquisition of spectra ")
        #save_spectrum_CCS100.put(1)
        #save_spectrum_CCS200.put(1)
        spectr_200 = get_CCS200_spectr.get(timeout=10)
        spectr_100 = get_CCS100_spectr.get(timeout=10)
        #print(spectr_100.shape)

        wavelength_200 = get_CCS200_wavel.get(timeout=10)
        wavelength_100 = get_CCS100_wavel.get(timeout=10)

        time_200 = get_CCS200_acq_time.get(timeout=10)
        time_100 = get_CCS100_acq_time.get(timeout=10)


        cam_timespt = get_cam_timespt.get(timeout=10)
        cam_X = get_cam_X.get(timeout=10)
        cam_Y = get_cam_Y.get(timeout=10)
        cam_ROI_X = get_cam_ROI_X.get(timeout=10)
        cam_ROI_Y = get_cam_ROI_Y.get(timeout=10)
        picoscop_trace = get_picoscop_trace.get(timeout=10)
        picoscop_coupling = get_picoscop_coupling.get(timeout=10)
        picoscop_range = get_picoscop_range.get(timeout=10)
        picoscop_time_base = get_picoscop_time_base.get(timeout=10)
        picoscop_Nsampl = get_picoscop_Nsampl.get(timeout=10)
        picoscop_T_interval = get_picoscop_T_interval.get(timeout=10)

        picoscop_timespt = get_picoscop_timespt.get(timeout=10)
        sp_100_timespt = get_sp_100_timespt.get(timeout=10)
        sp_200_timespt = get_sp_200_timespt.get(timeout=10)

        
        print('pause ', delta_T1, 's')
        sleep(delta_T1)
        
        #print(spectr_100)
        my_grp.create_dataset('dataset_spectr100', data=spectr_100)
        my_grp.create_dataset('dataset_spectr200', data=spectr_200)
        my_grp.create_dataset('dataset_cam', data=image_0)
        my_grp.create_dataset('dataset_camROI', data=image_0_ROI)
        my_grp.create_dataset('dataset_camTime', data=time_cam)
        my_grp.create_dataset('dataset_camGain', data=gain_cam)
        my_grp.create_dataset('dataset_spectr100Time', data=time_100)
        my_grp.create_dataset('dataset_spectr200Time', data=time_200)
        my_grp.create_dataset('dataset_wavelength_200', data=wavelength_200)
        my_grp.create_dataset('dataset_wavelength_100', data=wavelength_100)

        my_grp.create_dataset('dataset_cam_timespt', data=cam_timespt)
        my_grp.create_dataset('dataset_cam_X', data=cam_X)
        my_grp.create_dataset('dataset_cam_Y', data=cam_Y)
        my_grp.create_dataset('dataset_cam_ROI_X', data=cam_ROI_X)
        my_grp.create_dataset('dataset_cam_ROI_Y', data=cam_ROI_Y)
        my_grp.create_dataset('dataset_pico_trace', data=picoscop_trace)
        my_grp.create_dataset('dataset_pico_cpl', data=picoscop_coupling)
        my_grp.create_dataset('dataset_pico_Tbase', data=picoscop_time_base)
        my_grp.create_dataset('dataset_pico_Nsampl', data=picoscop_Nsampl)
        my_grp.create_dataset('dataset_picoscop_T_interval', data=picoscop_T_interval)
        my_grp.create_dataset('dataset_pico_timespt', data=picoscop_timespt)
        my_grp.create_dataset('dataset_spectr100_timespt', data=sp_100_timespt)
        my_grp.create_dataset('dataset_spectr200_timespt', data=sp_200_timespt)
        my_grp.create_dataset('dataset_cam_F_number', data=cam_F_number)


        #
        f.close() 
        #sleep(1)

        print("acquire image")
        logging.info('new image acquired')

        print('pause', 3*delta_T1, 's')
        sleep(3*delta_T1)
        # pause and restart camera acquisition
        print('camera off')
        start_cam_acquisition.put(0)

        print('pause', delta_T, 's')
        sleep(delta_T)
        #print('camera on')
        #start_cam_acquisition.put(1)

        #print('pause', delta_T1, 's')
        #sleep(delta_T1)

if __name__ == '__main__':
    main()
