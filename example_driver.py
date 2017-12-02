import lib.data_coolection as cool
import time

# Supress warnings from EPICS
cool.hush()
# Set up the data collector
c = cool.Coolector(sample='Roof',
                   sample_uid='1234567',
                   location='Romsdalsgata',
                   operator='Haavard',
                   description='Testing the code for the first time',
                   sub_experiment='NA',
                   directory='/tmp')
# Add devices
c.add_device(cool.Thorlabs_spectrometer('CCS1', True))
c.add_device(cool.Manta_cam('CAM1', True))
c.add_device(cool.RNG('RNG0', True))
# Start listening for triggers
c.start()
for trig in range(20):
    print('TRIG!')
    c.sw_trigger()
    time.sleep(0.2)
# Stop listening for triggers
c.stop()
# Disconnect PVs
c.disconnect()
