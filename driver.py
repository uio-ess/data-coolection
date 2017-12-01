import lib.data_coolection as cool
import time

cool.hush()
c = cool.Coolector(sample='Roof',
                   sample_uid='1234567',
                   location='Romsdalsgata',
                   operator='Haavard',
                   description='Testing the code for the first time',
                   sub_experiment='NA', directory='/tmp')
c.add_device(cool.Thorlabs_spectrometer('CCS1', True))
c.add_device(cool.Manta_cam('CAM1', True))
c.start()
for trig in range(20):
    print('TRIG!')
    c.sw_trigger()
    time.sleep(0.2)
c.stop()
c.disconnect()
