import data_coolection as cool
import moveStage
import time

# samples = {'HVC1.2': 0,
#            'HV7': 5500,
#            'HV10': 11000,
#            'HV1': 15000}

# This supresses EPICS warnings. Remove if something is wrong.
cool.hush()


def get_five_triggers(coolector):
    c.clear()
    for trig in range(5):
        print('Waiting for data!')
        c.wait_for_data()
        print(time.time())
        print("Got one! " + str(trig))


c = cool.Coolector(sample='HV1',
                   sample_uid='NA',
                   location='OCL',
                   operator='Haavard',
                   description='Temp sacn on HV1',
                   sub_experiment='',
                   directory='/var/data/ocl/2018-02-27/')
# Add devices

c.attrs['Distance to camera'] = 118.5
c.attrs['Distance units'] = 'cm'
c.attrs['F-number'] = 2.8

# moveStage.set_power_off_delay(0)

ps = cool.PicoscopePython(trig_per_min=6, sampling_interval=1e-7)
c.add_device(ps)

cam = cool.Manta_cam('CAM1',
                     sw_trig=False,
                     exposure=0.04,
                     gain=0,
                     exposure_max=0.1)
c.add_device(cam)
c.add_device(cool.Thorlabs_spectrometer('CCS1', sw_trig=False, exposure=3.0))

c.add_device(cool.SuperCool())


while(True):
    print('Waiting for data!')
    c.wait_for_data()
    print("Got one! ")

ps._ps.edgeCounterEnabled = False
