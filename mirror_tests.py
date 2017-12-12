import lib.data_coolection as cool

# Supress warnings from EPICS
cool.hush()


def n_triggers(n, c):
    for trig in range(n):
        c.sw_trigger()
        c.wait_for_data()


def on_fiber():
    c = cool.Coolector(sample='MWWHL4',
                       sample_uid='NA',
                       location='Prototype lab',
                       operator='Haavard',
                       description='Testing protected mirrors with white LED',
                       sub_experiment='Directly on fiber bundle',
                       directory='/var/data/lab/2017-12-12-mirrortest/fiber')
    c.attrs['LED Power'] = '2mA'
    c.attrs['Wheel position'] = 1
    # Add devices
    c.add_device(cool.Thorlabs_spectrometer('CCS1',
                                            exposure=0.010,
                                            sw_trig=True))
    n_triggers(100, c)


def on_silver():
    c = cool.Coolector(sample='MWWHL4',
                       sample_uid='NA',
                       location='Prototype lab',
                       operator='Haavard',
                       description='Testing protected mirrors with white LED',
                       sub_experiment='Silver mirror, PF10-03-P01',
                       directory='/var/data/lab/2017-12-12-mirrortest/silver')
    c.attrs['LED Power'] = '2mA'
    c.attrs['Wheel position'] = 1
    # Add devices
    c.add_device(cool.Thorlabs_spectrometer('CCS1',
                                            exposure=0.010,
                                            sw_trig=True))
    n_triggers(100, c)


def on_gold():
    c = cool.Coolector(sample='MWWHL4',
                       sample_uid='NA',
                       location='Prototype lab',
                       operator='Haavard',
                       description='Testing protected mirrors with white LED',
                       sub_experiment='Gold mirror, PF10-01-M01',
                       directory='/var/data/lab/2017-12-12-mirrortest/gold')
    c.attrs['LED Power'] = '2mA'
    c.attrs['Wheel position'] = 1
    # Add devices
    c.add_device(cool.Thorlabs_spectrometer('CCS1',
                                            exposure=0.010,
                                            sw_trig=True))
    n_triggers(100, c)


def on_aluminium():
    c = cool.Coolector(sample='MWWHL4',
                       sample_uid='NA',
                       location='Prototype lab',
                       operator='Haavard',
                       description='Testing protected mirrors with white LED',
                       sub_experiment='Aluminium mirror, PF10-01-G01',
                       directory='/var/data/lab/2017-12-12-mirrortest/alu')
    c.attrs['LED Power'] = '2mA'
    c.attrs['Wheel position'] = 1
    # Add devices
    c.add_device(cool.Thorlabs_spectrometer('CCS1',
                                            exposure=0.010,
                                            sw_trig=True))
    n_triggers(100, c)


def on_dielectric():
    c = cool.Coolector(sample='MWWHL4',
                       sample_uid='NA',
                       location='Prototype lab',
                       operator='Haavard',
                       description='Testing protected mirrors with white LED',
                       sub_experiment='Dielectric mirror, BB1-E02',
                       directory='/var/data/lab/2017-12-12-mirrortest/dielectric')
    c.attrs['LED Power'] = '2mA'
    c.attrs['Wheel position'] = 1
    # Add devices
    c.add_device(cool.Thorlabs_spectrometer('CCS1',
                                            exposure=0.010,
                                            sw_trig=True))
    n_triggers(100, c)


def dark():
    c = cool.Coolector(sample='MWWHL4',
                       sample_uid='NA',
                       location='Prototype lab',
                       operator='Haavard',
                       description='Testing protected mirrors with white LED',
                       sub_experiment='Dark spectra',
                       directory='/var/data/lab/2017-12-12-mirrortest/dark')
    c.attrs['LED Power'] = '0mA'
    c.attrs['Wheel position'] = 1
    # Add devices
    c.add_device(cool.Thorlabs_spectrometer('CCS1',
                                            exposure=0.010,
                                            sw_trig=True))
    n_triggers(100, c)


dark()
