import data_coolection as cool

# Supress warnings from EPICS
cool.hush()
c = cool.Coolector(session='Yttrium Tungstate tests',
                   sample='Monika',
                   #sample='DarkFrames',
                   sample_uid='NA',
                   location='Prototype lab',
                   operator='Haavard and Cyrille',
                   description='Calibrating irrad g-125 with PM100',
                   sub_experiment='No lens',
                   directory='/tmp/')
# Add devices
# c.attrs['Distance to lens aper'] = 37
# c.attrs['F-number'] = 4.0
# c.attrs['Distance to camera sensor'] = 39.5
# c.attrs['Distance to PM sensor'] = 38.5
# c.attrs['Distance units'] = 'cm'
# c.add_device(cool.Thorlabs_spectrometer('CCS1', sw_trig=True))
# cam = cool.Manta_cam('CAM1',
#                      sw_trig=True,
#                      exposure=0.002,
#                      gain=0,
#                      exposure_max=0.1)

# c.add_device(cam)
# c.add_device(cool.PM100('PM100', sw_trig=True))
c.add_device(cool.Thorlabs_spectrometer('CCS1', sw_trig=True))

with c:
    for trig in range(5):
        #cam.set_exposure(0.0003 + trig * 0.0002)
        c.sw_trigger()
        c.wait_for_data(timeout=130)
        print("Got one! " + str(trig))
