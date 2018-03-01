import data_coolection as cool

# This supresses EPICS warnings. Remove if something is wrong.
cool.hush()

c = cool.Coolector(sample='HVC1.2',
                   sample_uid='NA',
                   location='OCL',
                   operator='Haavard, Grey, Cyrille, Erik',
                   description='Temp scan, 70nA',
                   sub_experiment='Yttria Vanadate and SNS',
                   directory='/var/data/ocl/2018-02-28/')

# Linear stage
stage = cool.LinearStage()
# stage.add_sample('YttriumVanadata', 0)
# stage.add_sample('SNS', 5100)
# stage.add_sample('HV1', 8500)
stage.add_sample('HVC1.2', 12800)
stage.move_stage('HVC1.2')

c.add_device(stage)

# 0     Yttrium vanadate
# 5100  SNS
# 8500  HV1
# 12800 HVC1.2

# Manta camera
cam = cool.Manta_cam('CAM1',
                     sw_trig=False,
                     exposure=0.3,
                     gain=0,
                     exposure_max=0.5,
                     exposure_min=0.001)
cam.attrs['Distance to camera'] = 118.5
cam.attrs['Distance units'] = 'cm'
cam.attrs['F-number'] = 2.8
c.add_device(cam)

# Picoscope
ps = cool.PicoscopePython(trig_per_min=6)
c.add_device(ps)

# Thorlabs device
c.add_device(cool.Thorlabs_spectrometer('CCS1', sw_trig=False, exposure=1.0))

c.add_device(cool.SuperCool())

# Get 10 triggers on all devices on the stage, with auto exposure for devices that are able
# c.stage_scan_n_triggers(10, stage, auto_exposure=True)
c.wait_for_n_triggers(9999)

ps._ps.edgeCounterEnabled = False
print('Done!')
