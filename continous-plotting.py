import data_coolection as cool
import h5py
import time
import matplotlib.pyplot as plt

# Supress warnings from EPICS
cool.hush()
c = cool.Coolector(sample='Dummy',
                   sample_uid='NA',
                   location='Prototype lab',
                   operator='Haavard',
                   session='Heating M1 with mount in the prototype',
                   description='Heating M1 with mount in the prototype',
                   sub_experiment='NA',
                   directory='/tmp/')
# Add devices
cam = cool.Manta_cam('CAM1', "Nikkor 600, f4", "600", "8", sw_trig=True,
                     exposure=.22, gain=0, exposure_max=1.5)
c.add_device(cam)

print('Added camera')
# plt.ion()
# plt.colorbar(0, 4096)
fig = plt.figure()

# # cam.auto_exposure()

def integrate_sq(image, minx, maxx, miny, maxy):
    width = image.shape[0]
    height = image.shape[1]
    # print(width, height)
    # val = 1000
    # for i in range(height):
    #     for j in range(10):
    #         image[minx+j, i] = val
    #         image[maxx+j, i] = val
    # for i in range(width):
    #     for j in range(10):
    #         image[i, miny+j] = val
    #         image[i, maxy+j] = val

    sum = 0
    for i in range(minx, maxx):
        for j in range(miny, maxy):
            sum += image[i, j]
    print(sum/((maxx - minx) * (maxy - miny)))
    ax = fig.add_subplot(111)
    ax.matshow(image)
    plt.draw()
    plt.pause(1)


with c:
    while(True):
        # print('Trigger!')
        c.sw_trigger()
        c.wait_for_data()
        with h5py.File(c.latest_file_name, 'r') as f:
            image = f.get(cam.savedata.groupname + 'data')[:]
            integrate_sq(image, 400, 500, 250, 350)
            time.sleep(0.5)
