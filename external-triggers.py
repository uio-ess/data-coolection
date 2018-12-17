import data_coolection as cool
import time
# Supress warnings from EPICS
cool.hush()
c = cool.Coolector(sample='Initial sample scan',
                   sample_uid='NA',
                   location='OCL',
                   operator='Haavard',
                   session='DEC \'18 OCL',
                   description='Current scan no 2',
                   sub_experiment='Manual exposure',
                   nominal_beam_current=300.0e-9,
                   directory='/var/data/ocl/2018-12-14/')
                   # directory='/tmp/')

c.savedata.attrs['MeVs per proton'] = 1.0
# Add devices
cam = cool.Manta_cam('CAM1', 'Dummy', 50, 8.0,
                     sw_trig=False,
                     exposure=0.15,
                     gain=0,
                     exposure_min=0.001,
                     exposure_max=1.0)

cam.enable_lens_controller(focus=3390, aper='22')
time.sleep(2)
cam.efc.set_aperture('22')
cam.savedata.attrs['photons_per_count'] = 5.7817
cam.savedata.attrs['lens_transmission'] = 0.87
cam.savedata.attrs['ND filter'] = 1.0
cam.savedata.attrs['distance_to_target'] = 1300
c.add_device(cam)

ccs = cool.Thorlabs_spectrometer('CCS1', exposure=0.05, sw_trig=False)
c.add_device(ccs)

stage = cool.LinearStage()
stage.add_sample('DARK_NOBEAM', -1500)
stage.add_sample('DARK_BEAM', -5500)
stage.add_sample('HVP5R4NC', -1500)
stage.add_sample('HVP2R2NC', 2000)
stage.add_sample('HV7', 5300)
stage.add_sample('HV1', 8300)
stage.add_sample('HVP2R1C', 11600)
stage.add_sample('HV10', 16100)
c.add_device(stage)

ps = cool.PicoscopePython(trig_per_min=0, capture_duration=.15 * 1.25, sampling_interval=1e-6,
                          voltage_range=2)
c.add_device(ps)

ecat = cool.ECatEL3318(2)
ecat.add_sample('DARK_NOBEAM', -1)
ecat.add_sample('DARK_BEAM', -1)
ecat.add_sample('HVP5R4NC', -1)
ecat.add_sample('HVP2R2NC', -1)
ecat.add_sample('HV1', 1)
ecat.add_sample('HV7', 2)
ecat.add_sample('HVP2R1C', -1)
ecat.add_sample('HV10', 3)
c.add_device(ecat)

for num in range(2):
    print('Trigger!')
    c.hw_trigger()
    time.sleep(0.5)

c.clear()

print("Starting data collection")

c.stage_scan_n_triggers(10, stage.sample_dict, auto_exposure=False, skip_dark_nb=False)
for n in range(4):
    c.stage_scan_n_triggers(10, stage.sample_dict, auto_exposure=False, skip_dark_nb=True)
print('Scan done!')
