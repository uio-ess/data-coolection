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


c = cool.Coolector(sample='StageScan',
                   sample_uid='NA',
                   location='OCL',
                   operator='Haavard',
                   description='Testing DAQ code in OCL',
                   sub_experiment='Scanning over samples on stage',
                   directory='/tmp/')
# Add devices

c.attrs['Distance to camera'] = 118.5
c.attrs['Distance units'] = 'cm'
c.attrs['F-number'] = 2.8

moveStage.set_power_off_delay(0)

ps = cool.PicoscopePython(trig_per_min=60)
c.add_device(ps)

cam = cool.Manta_cam('CAM1',
                     sw_trig=False,
                     exposure=0.100,
                     gain=0,
                     exposure_max=0.1)
c.add_device(cam)
c.add_device(cool.Thorlabs_spectrometer('CCS1', sw_trig=False, exposure=0.5))

print(samples)

for sample, pos in samples.items():
    c.attrs['sample'] = sample
    c.attrs['stage_pos'] = pos
    moveStage.move_to(pos)
    time.sleep(1)
    # cam.auto_exposure()
    cam.set_exposure(0.01)
    get_five_triggers(c)
    cam.set_exposure(0.05)
    get_five_triggers(c)
    cam.set_exposure(0.1)
    get_five_triggers(c)

# for trig in range(1000):
#     c.wait_for_data()

print('Done!')

ps._ps.edgeCounterEnabled = False
