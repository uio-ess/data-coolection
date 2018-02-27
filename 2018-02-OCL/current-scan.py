import data_coolection as cool
import moveStage
import time

samples = {'HVC1.2': 0,
           'HV7': 5500,
           'HV10': 11000,
           'HV1': 15000}

# This supresses EPICS warnings. Remove if something is wrong.
cool.hush()


def get_five_triggers(coolector):
    c.clear()
    for trig in range(5):
        print('Waiting for data!')
        c.wait_for_data()
        print(time.time())
        print("Got one! " + str(trig))


c = cool.Coolector(sample='HVC1.2',
                   sample_uid='NA',
                   location='OCL',
                   operator='Haavard, Grey, Cyrille',
                   description='Testing current readout with beam',
                   sub_experiment='100nA, testing file sizes',
                   directory='/var/data/ocl/2018-02-27/')
# Add devices
c.attrs['Distance to camera'] = 118.5
c.attrs['Distance units'] = 'cm'
c.attrs['F-number'] = 2.8
c.attrs['stage_position'] = moveStage.get_position()

moveStage.set_power_off_delay(0)

ps = cool.PicoscopePython(trig_per_min=10, sampling_interval=1e-7)

c.add_device(ps)

cam = cool.Manta_cam('CAM1',
                     sw_trig=False,
                     exposure=0.200,
                     gain=0,
                     exposure_max=0.05)
c.add_device(cam)
c.add_device(cool.Thorlabs_spectrometer('CCS1', sw_trig=False, exposure=.5))

# print(samples)

for trig in range(5):
    c.wait_for_data()

print('Done!')

ps._ps.edgeCounterEnabled = False
