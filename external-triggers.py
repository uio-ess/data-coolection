import data_coolection as cool
import numpy as np
import time
# Supress warnings from EPICS
cool.hush()
c = cool.Coolector(sample='SpectrometerDarkFrames',
                   sample_uid='NA',
                   location='OCL',
                   operator='Haavard',
                   session='2018-02-OCL',
                   description='Calibration data for OCL 2018-02. Lights off, door closed, table covered. Taken a few days after the experiment',
                   sub_experiment='Spectrometer dark frames wirth shutter times np.arange(0.1,2.0,0.1)',
                   directory='/var/data/ocl/2018-02-28/calibration/')
                   # directory='/tmp/')
# Add devices
ccs = cool.Thorlabs_spectrometer('CCS1', sw_trig=False)
c.add_device(ccs)
# cam = cool.Manta_cam('CAM1', 'G.Zukio 50mm, 1.4', 50, 2.8,
#                      sw_trig=False,
#                      exposure=0.00200,
#                      gain=0,
#                      exposure_max=0.1)
# c.add_device(cam)

ps = cool.PicoscopePython(trig_per_min=60)
# c.add_device(ps)

for num in range(2):
    print('Trigger!')
    c.hw_trigger()
    time.sleep(0.5)

c.clear()

# print("Startging data collection")

# c.wait_for_n_triggers(5, SW_trigger=False)
with c:
    for exp in np.arange(0.1, 2.0, 0.1):
        ccs.set_exposure(exp)
        c.clear()
        for trig in range(10):
            c.wait_for_data()
