#import visa
import epics
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

#def configure_cam():

#def configure_spectro():

def acquire_image_spectrum(push_acq_image,push_acq_spectr,im_pv,sizex,sizey):

    print("push acquisition of the N image + average image")
    push_acq_image.put(1)
    # push the spectrum acquisition +
    push_acq_spectr.put(1)
    #
    sleep(1)

    print("acquire image")

    # verify the connection
    while False:
        im_pv.wait_for_connection(timeout=1)

    im = im_pv.get()
    nx = im.shape

    nx = sizex.get()
    ny = sizey.get()

    #print('size image :', nx, ny)
    #print('size im' , im.shape)

    im0 = im.reshape(nx,ny)

    #print('size im' , im.shape)
    #print(im)
    return im.ravel(), nx , ny

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
    minute = 60
    N_minutes = 2
    delta_T = N_minutes * minute
    # number of shots in 8h shift
    NN = 90

    # define the PVs to deal with
    fit_res_bkg = PV('DTU:GaussParam1')
    fit_res_I0 = PV('DTU:GaussParam2')
    fit_res_cx = PV('DTU:GaussParam3')
    fit_res_cy = PV('DTU:GaussParam4')
    fit_res_sigx = PV('DTU:GaussParam5')
    fit_res_sigy = PV('DTU:GaussParam6')
    fit_res_theta = PV('DTU:GaussParam7')

    push_acq_image = PV('CAM1:det1:Acquire')
    push_acq_spectr = PV('CCS1:det1:Acquire')
    im_pv = PV('CAM1:image1:ArrayData')
    #sizex = PV('CAM1:det1:ArraySizeX_RBV')
    #sizey = PV('CAM1:det1:ArraySizeY_RBV')
    sizex = PV('CAM1:image1:ArraySize0_RBV')
    sizey = PV('CAM1:image1:ArraySize1_RBV')

    # define the file to write into the analysed images
    timestr = time.strftime("%Y-%m-%d_%H%M%S")
    fit_file_name = 'Sample_' + timestr + '.dat'
    #create an empty array 2D for the fit file


    for ii in range (0, NN):

        print('iteration # = ', ii)
        # acquire the last image from the camera
        im, nx , ny = acquire_image_spectrum(push_acq_image,push_acq_spectr,im_pv,sizex,sizey)
        #print('argout: ' , im )
        print('argout: ' , nx )
        print('argout: ' , ny )

        # prep for the fit


        amplitude, xo, yo, sigma_x, sigma_y, theta, offset = 50, nx/2, ny/2, nx/3, ny/3, 0, 0

        initial_guess = (amplitude, xo, yo, sigma_x, sigma_y, theta, offset)

        print('initial param: ', initial_guess)

        bounds = ([0]*7,[np.inf,nx,ny,nx,ny,2* np.pi ,1e4])
        print('bound conditions:' , bounds)

        x = np.linspace(0, nx-1, nx)
        y = np.linspace(0, ny-1, ny)
        x, y = np.meshgrid(x, y)

        # fit the image with 2D gaussian
        print('fitting ...')
        popt, pcov = opt.curve_fit(twoD_Gaussian, (x, y), im, p0=initial_guess, method='trf',bounds=bounds)
        print('fit result: ' , *popt)

        Amplitude = popt[0]
        c_x = popt[1]
        c_y = popt[2]
        sigma_x = np.absolute(popt[3])
        sigma_y = np.absolute(popt[4])
        theta = popt[5]
        bkg = popt[6]
        print('write fit result in PVs')

        fit_res_bkg.put(bkg)
        fit_res_I0.put(Amplitude)
        fit_res_cx.put(c_x)
        fit_res_cy.put(c_y)
        fit_res_sigx.put(sigma_x)
        fit_res_sigy.put(sigma_y)
        fit_res_theta.put(theta)



        if (ii==0):
            data_Table = np.array(popt,ndmin=2)
        else:
            data_array = np.array(popt,ndmin=2)
            data_Table = np.concatenate((data_Table,data_array),axis=0)

        # save result to PV and to file
        #ampli.put(Amplitude[ii])
        #cx.put(c_x[ii])
        #cy.put(c_y[ii])
        #sigmax.put(sigma_x[ii])
        #sigmay.put(sigma_y[ii])
        #theta_pv.put(theta[ii])
        #backG.put(bkg[ii])

        # write append to file

        data_fit = Table(data_Table, names=('amplitude', 'x0', 'y0', 'sigma_x', 'sigma_y', 'theta', 'Background'))
        astropy.io.ascii.write(data_fit, fit_file_name)


        print('pause', delta_T, 's')
        sleep(delta_T)

if __name__ == '__main__':
    main()
