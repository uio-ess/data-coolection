import lib.data_coolection as cool
import time

if __name__ == '__main__':
    # Supress warnings from EPICS
    cool.hush()
    # Set up the data collector
    c = cool.Coolector(sample='M660L4',
                       sample_uid='NA',
                       location='Prototype lab',
                       operator='Haavard',
                       description='Testing DAQ code with Manta g-235 and CCS100',
                       sub_experiment='NA',
                       directory='/var/data/lab/2017-12-07/test/')
    # Add devices
    c.add_device(cool.Thorlabs_spectrometer('CCS1', sw_trig=True))
    cam = cool.Manta_cam('CAM1',
                         sw_trig=True,
                         auto_exposure=True,
                         exposure=0.000994,
                         gain=0,
                         exposure_max=0.1)
    c.add_device(cam)

    c.attrs['sub_experiment'] = 'Testing manual SW triggers with manual readout'
    c.attrs['extra_attribute'] = 123

    for trig in range(10):
        print('TRIG!')
        c.sw_trigger()
        c.wait_for_data()

    # disable auto exposure for fast triggers
    cam.auto_exposure = False

    c.attrs['sub_experiment'] = 'Testing manual triggers with automatic readout'
    # Strart listening for triggers
    c.start_listening()
    for trig in range(10):
        print('TRIG!')
        c.sw_trigger()
        time.sleep(.1)
    # Stop listening for triggers
    c.stop_listening()
