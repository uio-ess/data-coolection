import data_coolection as cool
import time
# Supress warnings from EPICS
cool.hush()
c = cool.Coolector(sample='Office 391',
                   sample_uid='NA',
                   location='office 391',
                   operator='Haavard',
                   description='Testing updated DAQ code with CCS100 and picoscope. Trigggers on demand',
                   sub_experiment='NA',
                   directory='/tmp/')
# Add devices
c.add_device(cool.Thorlabs_spectrometer('CCS1', sw_trig=False))
# c.add_device(cool.Manta_cam('CAM1',
#                             sw_trig=False,
#                             exposure=0.00200,
#                             gain=0,
#                             exposure_max=0.1))

ps = cool.PicoscopePython(trig_per_min=0)
c.add_device(ps)

for num in range(2):
    print('Trigger!')
    c.hw_trigger()
    time.sleep(0.5)

c.clear()

print("Startging data collection")

c.wait_for_n_triggers(2008)
