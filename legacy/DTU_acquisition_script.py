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

'''
Created on 26 Sep 2017
@author: cyrillethomas
@author: clementderrez

'''

os.environ['EPICS_MAX_ARRAY_BYTES']='15000000'
os.environ['EPICS_CA_ADDR_LIST']='10.0.19.247'

#def configure_cam():

#def configure_spectro():


def acquire_image_spectrum():

    print("push acquisition of the N image + average image")
    push_acq_image = PV('CAM1:det1:Acquire')
    push_acq_image.put(1)
    # push the spectrum acquisition +
    push_acq_spectr = PV('CCS1:det1:Acquire')
    push_acq_spectr.put(1)
    #
    sleep(10)

    print("acquire image")
    im_pv = PV('CAM1:image1:ArrayData')
    im = im_pv.get()
    sizex = PV('CAM1:det1:ArraySizeX_RBV')
    sizey = PV('CAM1:det1:ArraySizeY_RBV')

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



# define the time interval between shots
minute = 1
N_minutes = 10
delta_T = N_minutes * minute
# number of shots in 8h shift
NN = 8 * 6

# define the PVs to deal with
fit_res = PV('DTU:GaussParams')

# define the file to write into the analysed images
timestr = time.strftime("%Y-%m-%d_%H%M%S")
fit_file_name = 'Sample_' + timestr

for ii in range (0, NN):


    im, nx , ny = acquire_image_spectrum()


    print('argout: ' , im )
    print('argout: ' , nx )
    print('argout: ' , ny )




    amplitude, xo, yo, sigma_x, sigma_y, theta, offset = 50, 600, 700, 20, 20, 0, 0
    initial_guess = (amplitude, xo, yo, sigma_x, sigma_y, theta, offset)




    x = np.linspace(0, nx-1, nx)
    y = np.linspace(0, ny-1, ny)
    x, y = np.meshgrid(x, y)

    popt, pcov = opt.curve_fit(twoD_Gaussian, (x, y), im, p0=initial_guess)
    print('fit result: ' , *popt)

    Amplitude[ii] = popt[0]
    c_x[ii] = popt[1]
    c_y[ii] = popt[2]
    sigma_x[ii] = popt[3]
    sigma_y[ii] = popt[4]
    theta[ii] = popt[5]
    bkg[ii] = popt[6]

    fit_res.put(popt)

    # save result to PV and to file
    #ampli.put(Amplitude[ii])
    #cx.put(c_x[ii])
    #cy.put(c_y[ii])
    #sigmax.put(sigma_x[ii])
    #sigmay.put(sigma_y[ii])
    #theta_pv.put(theta[ii])
    #backG.put(bkg[ii])

    # write append to file
    data_fit = Table([Amplitude,c_x,c_y,sigma_x,sigma_y,theta,bkg], names=["amplitude", "x0", "y0", "sigma_x", "sigma_y", "theta", "Background"])
    ascii.write(data, fit_file_name)



    sleep(delta_T)
