import lib.data_coolection as cool

if __name__ == '__main__':
    # Supress warnings from EPICS
    cool.hush()
    # Set up the data collector
    c = cool.Coolector(sample='M660L4',
                       sample_uid='NA',
                       location='Prototype lab',
                       operator='Haavard',
                       description='Testing Manta 235 in prototype',
                       sub_experiment='NA',
                       directory='/var/lab/2017-12-07/gain0')
    # Add devices
    cam = cool.Manta_cam('CAM1',
                         sw_trig=True,
                         auto_exposure=False,
                         exposure=0.000994,
                         exposure_max=0.1)
    c.add_device(cam)

    def get_ten_triggers(gain):
        c.directory = '/var/data/lab/2017-12-07/gain' + str(gain) + '/'
        print(c.directory)
        cam.set_gain(gain)
        for trig in range(10):
            c.sw_trigger()
            c.wait_for_data()

    get_ten_triggers(0)
    get_ten_triggers(10)
    get_ten_triggers(20)
    get_ten_triggers(30)
    get_ten_triggers(40)
