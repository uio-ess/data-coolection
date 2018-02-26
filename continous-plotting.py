import lib.data_coolection as cool
import h5py
import matplotlib.pyplot as plt

# Supress warnings from EPICS
cool.hush()
c = cool.Coolector(sample='Dummy',
                   sample_uid='NA',
                   location='Prototype lab',
                   operator='Haavard',
                   description='Heating M1 with mount in the prototype',
                   sub_experiment='NA',
                   directory='/tmp/')
# Add devices
cam = cool.Manta_cam('CAM1', sw_trig=True, exposure=0.0010, gain=0, exposure_max=0.4)
c.add_device(cam)

plt.ion()
# plt.colorbar(0, 4096)
fig = plt.figure()

cam.auto_exposure()

while(True):
    c.sw_trigger()
    c.wait_for_data()
    with h5py.File(c.latest_file_name, 'r') as f:
        image = f.get(cam.pathname + 'data')[:]
        ax = fig.add_subplot(111)
        ax.matshow(image)
        plt.draw()
        plt.pause(0.2)
