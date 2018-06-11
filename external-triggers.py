import data_coolection as cool
import numpy as np
import time
# Supress warnings from EPICS
cool.hush()
c = cool.Coolector(sample='Dummy',
                   sample_uid='NA',
                   location='OCL',
                   operator='Haavard',
                   session='2018-06-OCL',
                   description='Playing with DAQ',
                   sub_experiment='Playing with DAQ',
                   # directory='/var/data/ocl/2018-02-28/calibration/')
                   directory='/tmp/')
# Add devices
ccs = cool.Thorlabs_spectrometer('CCS1', sw_trig=False)
c.add_device(ccs)
cam = cool.Manta_cam('CAM1', 'G.Zukio 50mm, 1.4', 50, 2.8,
                     sw_trig=False,
                     exposure=0.200,
                     gain=0,
                     exposure_max=0.1)
c.add_device(cam)

# stage = cool.LinearStage()
# stage.add_sample('dum1', 0)
# stage.add_sample('dum2', 1000)
# stage.add_sample('dum3', 2000)
# c.add_device(stage)

ps = cool.PicoscopePython(trig_per_min=0)
c.add_device(ps)

ecat = cool.ECatEL3318(1)
ecat.add_sample('HV4', 1)
ecat.move_to_sample('HV4')
c.add_device(ecat)

time.sleep(5)
for num in range(5):
    print('Trigger!')
    c.hw_trigger()
    time.sleep(0.5)

c.clear()

# print("Startging data collection")

# c.stage_scan_n_triggers(3, stage.sample_dict, )

c.wait_for_n_triggers(5, SW_trigger=False)
# with c:
#     for exp in np.arange(0.1, 2.0, 0.1):
#         ccs.set_exposure(exp)
#         c.clear()
#         for trig in range(10):
#             c.wait_for_data()
