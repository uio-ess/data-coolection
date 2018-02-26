import lib.data_coolection as cool

# Supress warnings from EPICS
cool.hush()
c = cool.Coolector(sample='M660L4-NoLens',
                   sample_uid='NA',
                   location='Prototype lab',
                   operator='Haavard',
                   description='Calibrating g-125 with PM100',
                   sub_experiment='PM100',
                   directory='/tmp/')
# Add devices
c.attrs['Distance to lens aper'] = 37
c.attrs['F-number'] = 0
c.attrs['Distance to camera sensor'] = 40
c.attrs['Distance units'] = 'cm'
# c.add_device(cool.Thorlabs_spectrometer('CCS1', sw_trig=True))
c.add_device(cool.Manta_cam('CAM1',
                            sw_trig=True,
                            exposure=0.001,
                            gain=0,
                            exposure_max=0.1))
c.add_device(cool.PM100('PM100', sw_trig=True))

for trig in range(10):
    c.sw_trigger()
    c.wait_for_data(timeout=130)
    print("Got one! " + str(trig))
