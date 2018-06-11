import numpy as np
import scipy.optimize as opt
import matplotlib.pyplot as plt

def main():
    #x0, y0 = 0.3, 0.7


    x = np.linspace(0, 200, 201)
    y = np.linspace(0, 200, 201)
    x, y = np.meshgrid(x, y)

    #create data
    amplitude, xo, yo, sigma_x, sigma_y, theta, offset =  30, 90, 100.23, 5.2, 15.1, 20 * np.pi/180 , 0.556
    data = twoD_Gaussian((x, y),amplitude, xo, yo, sigma_x, sigma_y, theta, offset)

    # plot twoD_Gaussian data generated above
    plt.figure()
    plt.imshow(data.reshape(201, 201))
    plt.colorbar()
    plt.show()


    initial_guess = (3,100,100,20,40,0,10)
    data_noisy = data + 3*np.random.normal(size=data.shape)

    plt.figure()
    plt.imshow(data_noisy.reshape(201, 201))
    plt.colorbar()
    plt.show()


    popt, pcov = opt.curve_fit(twoD_Gaussian, (x, y), data_noisy, p0=initial_guess)
    print('fit result: ' , *popt)

    data_fit = twoD_Gaussian((x, y),*popt)

    data_res= data_fit.reshape(201, 201) - data.reshape(201, 201)
    plt.figure()
    plt.imshow(data_res)
    plt.colorbar()
    plt.show()





def twoD_Gaussian(X, amplitude, xo, yo, sigma_x, sigma_y, theta, offset):
    x, y = X
    xo = float(xo)
    yo = float(yo)
    a = (np.cos(theta)**2)/(2*sigma_x**2) + (np.sin(theta)**2)/(2*sigma_y**2)
    b = -(np.sin(2*theta))/(4*sigma_x**2) + (np.sin(2*theta))/(4*sigma_y**2)
    c = (np.sin(theta)**2)/(2*sigma_x**2) + (np.cos(theta)**2)/(2*sigma_y**2)
    g = offset + amplitude*np.exp( - (a*((x-xo)**2) + 2*b*(x-xo)*(y-yo)+ c*((y-yo)**2)))
    return g.ravel()




main()
