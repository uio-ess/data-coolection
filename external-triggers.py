import lib.data_coolection as cool

# Supress warnings from EPICS
cool.hush()
c = cool.Coolector(sample='Office 391',
                   sample_uid='NA',
                   location='office 391',
                   operator='Haavard',
                   description='Testing DAQ code with Manta g-125 and CCS100. Trigger rate 2Hz',
                   sub_experiment='NA',
                   directory='/tmp/')
# Add devices
c.add_device(cool.Thorlabs_spectrometer('CCS1', sw_trig=False))
c.add_device(cool.Manta_cam('CAM1',
                            sw_trig=False,
                            auto_exposure=False,
                            exposure=0.00200,
                            gain=0,
                            exposure_max=0.1))

for trig in range(10):
    c.wait_for_data()
    print("Got one! " + str(trig))
