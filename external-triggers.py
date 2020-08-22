import data_coolection as cool
import time
# Supress warning s from EPICS
cool.hush()
c = cool.Coolector(sample='NA',
                   sample_uid='NA',
                   location='OCL',
                   operator='Haavard and Cyrille',
                   session='May \'19 OCL',
                   description='Stage scan, combustion sprayed samples, new Faraday cup, places 300um sample',
                   sub_experiment='NA',
                   nominal_beam_current=350.0e-9,
                   directory='/var/data/ocl/2019-05-22/')
                   # directory='/tmp/')

cam_exposure = 0.15
ccs_exposure = 0.05

c.savedata.attrs['MeVs per proton'] = 0.5
# Add devices
cam = cool.Manta_cam('CAM1', 'Dummy', 50, 8.0,
                     sw_trig=False,
                     exposure=cam_exposure,
                     gain=0,
                     exposure_min=0.001,
                     exposure_max=1.0)
cam.enable_lens_controller()
time.sleep(2)
cam.savedata.attrs['photons_per_count'] = 5.7817
cam.savedata.attrs['lens_transmission'] = 0.87
cam.savedata.attrs['ND filter'] = 1.0
cam.savedata.attrs['distance_to_target'] = 1300
c.add_device(cam)

ccs = cool.Thorlabs_spectrometer('CCS1', exposure=ccs_exposure, sw_trig=False)
c.add_device(ccs)

stage = cool.LinearStage()
stage.add_sample('DARK_NOBEAM', 17000)
stage.add_sample('DARK_BEAM', 11800)
stage.add_sample('HV1', 11800)
stage.add_sample('HVP2R1', 8800)
stage.add_sample('HVCOMB-Al-Ni-50um', 6300)
stage.add_sample('HVCOMB-Al-Ni-100um', 3200)
stage.add_sample('HVCOMB-Al-Ni-200um', 500)
stage.add_sample('HVCOMB-Al-Ni-300um-Cooling', -2800)
c.add_device(stage)

ps = cool.PicoscopePython(trig_per_min=0, capture_duration=max(cam_exposure, ccs_exposure) * 1.25, 
                          sampling_interval=1e-4,
                          voltage_range=2, send_triggers=False)
c.add_device(ps)

c.add_device(cool.Raspi_trigger())

# ecat = cool.ECatEL3318(2)
# ecat.add_sample('DARK_NOBEAM', -1)
# ecat.add_sample('DARK_BEAM', -1)
# ecat.add_sample('HVCOMB-Al-Ni-50um', -1)
# ecat.add_sample('HVP2R1', 1)
# ecat.add_sample('HV1', 2)
# ecat.add_sample('HVCOMB-Al-Ni-100um', 3)
# ecat.add_sample('HVCOMB-Al-Ni-200um', 4)
# ecat.add_sample('HVCOMB-Al-Ni-300um-Cooling', 5)
# c.add_device(ecat)

for num in range(2):
    print('Trigger!')
    c.hw_trigger()
    time.sleep(0.5)

c.clear()

print("Starting data collection")

c.stage_scan_n_triggers(10, stage.sample_dict, auto_exposure=True, skip_dark_nb=False)
for n in range(3):
    c.stage_scan_n_triggers(10, stage.sample_dict, auto_exposure=True, skip_dark_nb=True)
print('Scan done!')
