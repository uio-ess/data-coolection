import data_coolection as cool
import time
# Supress warnings from EPICS
cool.hush()
c = cool.Coolector(sample='StageScan',
                   sample_uid='NA',
                   location='OCL',
                   operator='Haavard',
                   session='JUN \'18 OCL',
                   description='Stage scan',
                   sub_experiment='Yttrium Tungstate, HVC2 and HV1',
                   nominal_beam_current=120.0e-9,
                   directory='/var/data/ocl/2018-06-14/')
                   # directory='/tmp/')

# Add devices
cam = cool.Manta_cam('CAM1', 'G.Zukio 50mm, 1.4', 50, 4.0,
                     sw_trig=False,
                     exposure=0.5,
                     gain=0,
                     exposure_max=0.7)

cam.savedata.attrs['photons_per_count'] = 5.7817
cam.savedata.attrs['lens_transmission'] = 0.95
cam.savedata.attrs['distance_to_target'] = 1120

c.add_device(cam)

ccs = cool.Thorlabs_spectrometer('CCS1', exposure=2.00, sw_trig=False)
c.add_device(ccs)

stage = cool.LinearStage()
# stage.add_sample('HVC1.2', 700)
# stage.add_sample('SNS', 5200)
# stage.add_sample('HV1', 11300)
# stage.add_sample('HV10', 15300)
# stage.add_sample('HVC2', 700)
# stage.add_sample('HV1', 5200)
stage.add_sample('YW1_H', 12000)
stage.add_sample('YW1', 15000)

c.add_device(stage)

ps = cool.PicoscopePython(trig_per_min=0, capture_duration=0.02, sampling_interval=1e-6)
c.add_device(ps)

# ecat = cool.ECatEL3318(1)
# ecat.add_sample('HV1', 1)
# ecat.add_sample('HVC1.2', 2)
# ecat.add_sample('SNS', 3)
# ecat.add_sample('HV7', 4)
# ecat.add_sample('HV10', 5)
# c.add_device(ecat)

for num in range(2):
    print('Trigger!')
    c.hw_trigger()
    time.sleep(0.5)
    
c.clear()

print("Startging data collection")

c.stage_scan_n_triggers(11, stage.sample_dict, auto_exposure=False)
# c.heat_scan_sample('SNS', auto_exposure=True, pause=5)

print('Scan done!')
