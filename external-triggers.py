import data_coolection as cool
import time
# Supress warnings from EPICS
cool.hush()
c = cool.Coolector(sample='StageScan',
                   sample_uid='NA',
                   location='OCL',
                   operator='Haavard and Grey',
                   session='JUN \'18 OCL',
                   description='Stage scan',
                   sub_experiment='Stage scan',
                   nominal_beam_current=210.0e-9,
                   directory='/var/data/ocl/2018-06-13/')
                   # directory='/tmp/')
# Add devices
cam = cool.Manta_cam('CAM1', 'G.Zukio 50mm, 1.4', 50, 4.0,
                     sw_trig=False,
                     exposure=0.200,
                     gain=0,
                     exposure_max=0.4)

cam.savedata.attrs['photons_per_count'] = 5.7817
cam.savedata.attrs['lens_transmission'] = 0.95
cam.savedata.attrs['distance_to_target'] = 1120

c.add_device(cam)

ccs = cool.Thorlabs_spectrometer('CCS1', sw_trig=False)
c.add_device(ccs)

stage = cool.LinearStage()
stage.add_sample('HV1', -1400)
stage.add_sample('HVC1.2', 2700)
stage.add_sample('SNS', 5700)
stage.add_sample('HV7', 11047)
stage.add_sample('HV10', 14800)
c.add_device(stage)

ps = cool.PicoscopePython(trig_per_min=0)
c.add_device(ps)

ecat = cool.ECatEL3318(1)
ecat.add_sample('HV1', 1)
ecat.add_sample('HVC1.2', 2)
ecat.add_sample('SNS', 3)
ecat.add_sample('HV7', 4)
ecat.add_sample('HV10', 5)
c.add_device(ecat)

for num in range(2):
    print('Trigger!')
    c.hw_trigger()
    time.sleep(0.5)

c.clear()

# print("Startging data collection")

c.stage_scan_n_triggers(11, stage.sample_dict, auto_exposure=True)

# c.wait_for_n_triggers(5, SW_trigger=False)
# with c:
#     for exp in np.arange(0.1, 2.0, 0.1):
#         ccs.set_exposure(exp)
#         c.clear()
#         for trig in range(10):
#             c.wait_for_data()

print('Scan done!')
