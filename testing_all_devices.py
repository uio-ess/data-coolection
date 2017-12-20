import lib.data_coolection as cool

# Supress warnings from EPICS
cool.hush()
c = cool.Coolector(sample='M660L4',
                   sample_uid='NA',
                   location='Prototype lab',
                   operator='Haavard',
                   description='Testing DAQ code with Manta g-125, PM100 and CCS100',
                   sub_experiment='NA',
                   directory='/tmp/')
# Add devices
c.add_device(cool.Thorlabs_spectrometer('CCS1', sw_trig=True))
c.add_device(cool.Manta_cam('CAM1',
                            sw_trig=True,
                            auto_exposure=False,
                            exposure=0.000994,
                            gain=0,
                            exposure_max=0.1))
c.add_device(cool.PM100('PM100', sw_trig=True))


c.sw_trigger()
c.wait_for_data()
