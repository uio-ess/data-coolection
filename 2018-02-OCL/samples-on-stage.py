import data_coolection as cool

# This supresses EPICS warnings. Remove if something is wrong.
cool.hush()

c = cool.Coolector(sample='StageScan',
                   sample_uid='NA',
                   location='OCL',
                   operator='Haavard, Grey, Cyrille, Erik',
                   description='Testing DAQ code in OCL',
                   sub_experiment='Scanning over samples on stage',
                   directory='/tmp/')

# Linear stage
stage = cool.LinearStage()
stage.add_sample('HVC1.2', 0)
stage.add_sample('HV7', 5500)
# stage.add_device('HV10', 11000)
# stage.add_device('HV1', 15000)
c.add_device(stage)

# Manta camera
cam = cool.Manta_cam('CAM1',
                     sw_trig=False,
                     exposure=0.0011,
                     gain=0,
                     exposure_max=0.5,
                     exposure_min=0.001)
cam.attrs['Distance to camera'] = 118.5
cam.attrs['Distance units'] = 'cm'
cam.attrs['F-number'] = 2.8
c.add_device(cam)

# Thorlabs device
c.add_device(cool.Thorlabs_spectrometer('CCS1', sw_trig=False, exposure=0.5))

# Picoscope
ps = cool.PicoscopePython(trig_per_min=60)
c.add_device(ps)

# Get 10 triggers on all devices on the stage, with auto exposure for devices that are able
c.stage_scan_n_triggers(10, stage, auto_exposure=True)
ps._ps.edgeCounterEnabled = False
