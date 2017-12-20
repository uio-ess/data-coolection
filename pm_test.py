import lib.data_coolection as cool

# Supress warnings from EPICS
cool.hush()
c = cool.Coolector(sample='Rooflights',
                    sample_uid='NA',
                    location='UiO Office',
                    operator='Haavard',
                    description='Testing DAQ code with PM100',
                    sub_experiment='NA',
                    directory='/tmp/')
# Add devices
c.add_device(cool.PM100('PM100', sw_trig=True))

print('trigger!')
c.sw_trigger()
c.wait_for_data()
print('Done!')
