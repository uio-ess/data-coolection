import lib.data_coolection as cool
import h5py
import matplotlib.pyplot as plt

# Supress warnings from EPICS
cool.hush()
c = cool.Coolector(sample='TestPatternCoolDayAfter',
                   sample_uid='NA',
                   location='Prototype lab',
                   operator='Haavard',
                   description='Testing DAQ code with Manta g-125, PM100 and CCS100',
                   sub_experiment='NA',
                   directory='/tmp/')
# Add devices
cam = cool.Manta_cam('CAM1', sw_trig=True, auto_exposure=False,
                     exposure=0.300, gain=0, exposure_max=0.4)
c.add_device(cam)

plt.ion()
fig = plt.figure()

while(True):
    c.sw_trigger()
    c.wait_for_data()
    with h5py.File(c.latest_file_name, 'r') as f:
        image = f.get(cam.pathname + 'data')[:]
        ax = fig.add_subplot(111)
        ax.matshow(image)
        plt.draw()
        plt.pause(30)
