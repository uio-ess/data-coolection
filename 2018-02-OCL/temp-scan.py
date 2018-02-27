import data_coolection as cool
import time

# This supresses EPICS warnings. Remove if something is wrong.
cool.hush()

c = cool.Coolector(sample='HV1',
                   sample_uid='NA',
                   location='OCL',
                   operator='Haavard, Grey, Cyrille, Erik',
                   description='Temp sacn on HV1, no beam',
                   sub_experiment='',
                   directory='/tmp/')
# Add devices

# ps = cool.PicoscopePython(trig_per_min=6, sampling_interval=1e-7)
# c.add_device(ps)

cam = cool.Manta_cam('CAM1',
                     sw_trig=True,
                     exposure=0.04,
                     gain=0,
                     exposure_max=0.1)
c.add_device(cam)
c.add_device(cool.Thorlabs_spectrometer('CCS1', sw_trig=True, exposure=3.0))
cam.attrs['Distance to camera'] = 118.5
cam.attrs['Distance units'] = 'cm'
cam.attrs['F-number'] = 2.8

c.add_device(cool.SuperCool())

with c:
    while(True):
        print('SW trig!')
        c.sw_trigger()
        print('Waiting for data!')
        c.wait_for_data()
        print("Got one! ")
        time.sleep(10)
