import h5py
import epics
import threading
import time
import numpy
import scipy.ndimage
import warnings
import numbers


def hush():
    """
    Remove warnings from epics. These can be helpful, but we get a lot of
    warnings about 'Identical process variable names on multiple servers'
    """
    epics.ca.replace_printf_handler(lambda text: None)


class Coolector(object):
    """
    Collect data from Cool devices, put them in HDF5 files.
    """
    pause = 0.001
    triggerID = 0
    _devices = []
    _listen = False
    thread = None

    def check_if_ready(self):
        """
        Are all devices ready for readi out?
        """
        ready = True
        for dev in self._devices:
            if(not dev.is_ready_p()):
                ready = False
        return(ready)

    def cd(self, dir):
        """ Change directory """
        self.directory = dir

    def wait_for_data(self):
        """
        Wait until all devices are ready, then read the all out
        """
        while(True):
            if(self.check_if_ready()):
                break
            time.sleep(self.pause)
        self.write(self.triggerID)

    def _listening(self):
        """
        Periodically check if devices are ready, if so, read out
        """
        print('Listening!')
        while(self._listen):
            if(self.check_if_ready()):
                self.write(self.triggerID)
            time.sleep(self.pause)
        print('Shutting down collection!')

    def sw_trigger(self):
        """
        Send SW trigger to all connected devices
        """
        for dev in self._devices:
            dev.sw_trigger()

    def write(self, trigger):
        """
        Write meta data + device data for all connected devices
        """
        # This is the accepted trigger count, there should be a way of getting
        # global trigger ID
        self.triggerID += 1
        timestamp = time.time()
        fname = '{0}{1:016d}-{2}.h5'.format(self.directory, trigger, self.sample)
        print('Writing to ' + fname)
        with h5py.File(fname, 'w') as h5f:
            attrs = h5f.get('/').attrs
            attrs['timestamp'] = timestamp
            attrs['trigger_id'] = trigger
            for attr, value in self.attrs.items():
                attrs[attr] = value
            for dev in self._devices:
                dev.write(h5f)
        # All devices are read out, we can now wait for new data
        for dev in self._devices:
            dev.is_ready = False
            dev.potentially_desynced = False

    def __init__(self, sample=None, sample_uid=None, location=None, operator=None,
                 description=None, sub_experiment=None, directory=None):
        """
        Init function. Meta data as mandatory arguments.
        """
        if(not sample and description and directory and sample_uid and location and
           sample_uid and operator and sub_experiment):
            raise Exception('Supply sample, sample_uid, location, operator, \
            description, directory abd sub_experiment')
        self.sample = sample
        self.attrs = {'sample_name': sample,
                      'sample_guid': sample_uid,
                      'location': location,
                      'operator_name': operator,
                      'experiment_description': description,
                      'sub_experiment': sub_experiment}
        self.directory = directory
        if(not self.directory.endswith('/')):
            self.directory += '/'

    def add_device(self, device):
        """
        Add a Cool_device to the coolector.
        """
        self._devices.append(device)
        device.is_ready = False

    def start_listening(self):
        """
        Start automatic data acquisition.
        """
        if(self.thread):
            print('Thread seems to already running! not starting a new one.')
        else:
            self._listen = True
            self.thread = threading.Thread(target=self._listening, args=())
            self.thread.start()
            print('Started thread!')

    def stop_listening(self):
        """
        Stop automatic data acquisition
        """
        self._listen = False

 
class Cool_device(object):
    """
    Base class for reading out a devices, and writing device info to HDF5
    """
    port = None
    pathname = None
    dev_type = None
    is_ready = False
    potentially_desynced = False
    array_data = None

    meta_pvnames = []
    connected_pvs = []

    def set_ready(self, value):
        """
        Mark device as ready for read out, copy data to object.
        This is intended as a callback funtion for a pv
        """
        if(self.is_ready):
            warnings.warn("New trigger before readout finished! potentially desynced event!")
            self.potentially_desynced = True
        else:
            self.array_data = value
        self.is_ready = True

    def sw_trigger(): pass

    def is_ready_p(self):
        return(self.is_ready)

    def write(self, h5f):
        """
        Write all pvs in meta_pvnames to file.
        """
        group = h5f.require_group(self.pathname)
        group.attrs['instrument_name'] = self.dev_type
        for pvname in self.meta_pvnames:
            group.attrs[pvname] = epics.caget(pvname)
        group.attrs['Potentially desynced'] = self.potentially_desynced

    def write_ds(self, group, dsname, pvname, data=False):
        if(not data):
            data = epics.caget(pvname)
        ds = group.create_dataset(dsname, data=data)
        ds.attrs['pvname'] = pvname

    def pv_to_hdf5(self, prefix, *pvs):
        """
        Make a list of pvnames that should be read out to hdf5
        """
        for pv in pvs:
            self.meta_pvnames.append(prefix + pv)


class Manta_cam(Cool_device):
    """
    Manta camera
    """
    dev_type = 'Manta camera'

    def sw_trigger(self):
        """ Set Ackuire to True """
        epics.caput(self.port + ':det1:Acquire', 1)

    def set_exposure(self, exposure):
        """
        Set exposure if it is within acceptable limits.
        """
        exposure = max(exposure, self.exposure_min)
        exposure = min(exposure, self.exposure_max)
        print('Setting exposure to: ' + str(exposure))
        epics.caput(self.port + ':det1:AcquireTime', exposure)
        time.sleep(0.1)

    def set_gain(self, gain):
        """
        Set gain.
        """
        print('Setting gain to: ' + str(gain))
        epics.caput(self.port + ':det1:Gain', gain)
        time.sleep(0.1)

    def __init__(self, port,
                 sw_trig=False,
                 auto_exposure=False,
                 exposure=None,
                 gain=None,
                 exposure_min=0.0003,
                 exposure_max=0.1):
        """
        Initialize a manta camera
        """
        # Deal with init arguments
        self.auto_exposure = auto_exposure
        if(auto_exposure):
            print('Auro exposure is slow! May need a couple of seconds between triggers')
        self.exposure_min = exposure_min
        self.exposure_max = exposure_max
        self.port = port
        self.pathname = 'data/images/' + port + '/'
        self.arraydata = port + ':image1:ArrayData'

        # PVs that will be dumped to file
        self.pv_to_hdf5(self.port, 
                        ':det1:SizeX_RBV',
                        ':det1:SizeY_RBV',
                        ':det1:Manufacturer_RBV',
                        ':det1:Model_RBV',
                        ':det1:AcquireTime_RBV',
                        ':det1:Gain_RBV',
                        ':det1:LEFTSHIFT_RBV',
                        ':det1:DataType_RBV')

        # When port + :image1:ArrayData has new data, we are ready for read out
        # Callback function sets the is_ready flag to True
        pv = epics.PV(self.port + ':image1:ArrayData',
                      auto_monitor=True,
                      callback=lambda pvn=None, v=None, cv=None, **fw: self.set_ready(v))
        self.connected_pvs.append(pv)


        # Initialize device
        for pvname, value in {':image1:EnableCallbacks': 1,  # Enable
                              ':image1:ArrayCallbacks': 1,  # Enable
                              ':det1:DataType': 1,  # UInt16, 12-bit
                              ':det1:LEFTSHIFT': 0}.items():  # Disable
            epics.caput(port + pvname, value)

        if(sw_trig):
            epics.caput(port + ':det1:ImageMode', 0)  # Get a single image
        else:
            epics.caput(port + ':det1:ImageMode', 1)  # Get images continously
            warnings.warn('Not yet implemented, missing external trigger setting')

        # Set exposure and gain from init arguments
        if(exposure):
            self.set_exposure(exposure)
        if(isinstance(gain, numbers.Number)): # We must be able to set this to 0
            self.set_gain(gain)

    def write(self, h5f):
        """
        Overload write to file function. Needed here in order to reshape
        the image from array to vector.
        """
        # Call parent funciton to write pv metadata
        super().write(h5f)
        raw = epics.caget(self.arraydata)
        raw = raw.reshape(epics.caget(self.port + ':det1:SizeY_RBV'),
                          epics.caget(self.port + ':det1:SizeX_RBV'))
        group = h5f.require_group(self.pathname)
        ds = group.create_dataset('data', data=raw)
        ds.attrs['pvname'] = self.arraydata
        # Correct exposure based on image if auto_exposure is True
        # This must occur after super(), so metadata is written before it is changed
        if(self.auto_exposure):
            sm = scipy.ndimage.filters.median_filter(raw, 9).max()
            max_image = 2**12 - 1
            exp = epics.caget(self.port + ':det1:AcquireTime_RBV')
            autoset = exp * (max_image * 0.5)/sm
            self.set_exposure(autoset)


class Thorlabs_spectrometer(Cool_device):
    """
    Thorlabs CCS100 spectrometer
    """
    dev_type = 'Thorlabs spectrometer'

    def sw_trigger(self): epics.caput(self.port + ':det1:Acquire', 1)

    def set_exposure(self, exposure):
        """
        Set exposure
        """
        print('Setting exposure to: ' + str(exposure))
        epics.caput(self.port + ':det1:AcquireTime', exposure)
        time.sleep(0.1)

    def __init__(self, port, sw_trig=False, exposure=None):
        """
        Initialize a Thorlabs spectrometer
        """
        self.port = port
        self.pathname = 'data/spectra/' + port + '/'
        self.arraydata = port + ':trace1:ArrayData'

        # PVs that will be dumped to file
        self.pv_to_hdf5(self.port,
                        ':det1:AcquireTime_RBV',
                        ':det1:Manufacturer_RBV',
                        ':det1:Model_RBV')

        self.y_values = port + ':trace1:ArrayData'
        self.x_values = port + ':det1:TlWavelengthData_RBV'
        self.y_scale = port + ':det1:TlAmplitudeData_RBV'

        # Set is_ready to True when there is new data using a callback
        pv = epics.PV(self.port + ':trace1:ArrayData',
                      auto_monitor=True,
                      callback=lambda pvn=None, v=None, cv=None, **fw: self.set_ready(v))
        self.connected_pvs.append(pv)

        # Initialize device
        for pvname, value in {':det1:TlAcquisitionType': 0,  # 1 is processed, set to 0 for raw
                              ':trace1:EnableCallbacks': 1,  # Enable
                              ':trace1:ArrayCallbacks': 1,  # Enable
                              ':det1:TlAmplitudeDataTarget': 2,  # Thorlabs
                              ':det1:TlWavelengthDataTarget': 0,  # Factory
                              ':det1:TlAmplitudeDataGet': 1,  # Get amplitudes
                              ':det1:TlWavelengthDataGet': 1}.items():  # Get waves
            epics.caput(port + pvname, value)
        if(sw_trig):
            for pvname, value in {':det1:ImageMode': 0,  # Single
                                  ':det1:TriggerMode': 0}.items():  # Internal
                epics.caput(port + pvname, value)
        else:
            for pvname, value in {':det1:ImageMode': 1,  # Continuous
                                  ':det1:TriggerMode': 1}.items():  # External
                epics.caput(port + pvname, value)
                warnings.warn('Not yet implemented')

        # Set exposure from argument
        if(exposure):
            self.set_exposure(exposure)

    def write(self, h5f):
        group = h5f.require_group(self.pathname)
        self.write_ds(group, 'x_values', self.x_values)
        self.write_ds(group, 'y_values', self.y_values, self.array_data)
        self.write_ds(group, 'y_scale', self.y_scale)
        super().write(h5f)


class PM100(Cool_device):
    """
    Thorlabs PM100USB
    """
    dev_type = 'Thorlabs PM100USB'
    n_samples = 100

    times = []

    def populate(self):
        """ Fill a list of PM values with timestamps, sample for 10 seconds """
        pmvals = []
        scan_mode = epics.caget(self.port + ':MEAS:POW.SCAN')
        epics.caput(self.port + ':MEAS:POW.SCAN', 9)

        # Use callback to populate list
        pv = epics.PV(self.port + ':MEAS:POW')
        pv.add_callback(
            lambda pvname=None, value=None, char_value=None, **fw:
            pmvals.append((value, time.time())))

        time.sleep(10)
        pv.disconnect()
        epics.caput(self.port + ':MEAS:POW.SCAN', scan_mode)
        self.array_data = [a[0] for a in pmvals]
        self.times = [a[1] for a in pmvals]
        # We are done and ready for read out
        self.is_ready = True

    def sw_trigger(self):
        "Trigger starts data collection thread"
        if(not self.is_ready):
            threading.Thread(target=self.populate, args=()).start()

    def __init__(self, port, sw_trig=False):
        """ Initialize pm100 """
        self.port = port
        self.pm_pv = self.port + ':MEAS:POW'
        self.pathname = 'data/powermeter/' + self.port + '/'
        self.meta_pvnames = [self.port + ':SENS:CORR:WAV_RBV']

    def write(self, h5f):
        # We must trigger an uptade to WAV_RBV before the PV is written to file
        epics.caput(self.port + ':SENS:CORR:WAV_RBV.PROC', 1)
        time.sleep(0.01)
        super().write(h5f)
        group = h5f.require_group(self.pathname)
        self.write_ds(group, 'y_values', self.pm_pv, self.array_data)
        ds = group.create_dataset('x_values', data=self.times)
        ds.attrs['pvname'] = 'time from trigger'


class RNG(Cool_device):
    """
    Print some random numbers to HDF5 as an example of a non epics device
    """
    dev_type = 'rng'
    datavec = None

    def populate(self):
        self.datavec = numpy.random.rand(100)
        self.is_ready = True

    def sw_trigger(self):
        if(not self.is_ready):
            threading.Thread(target=self.populate, args=()).start()

    def __init__(self, port, sw_trig=False):
        self.port = port
        self.pathname = 'data/rng/' + self.port + '/'

    def write(self, h5f):
        super().write(h5f)
        group = h5f.require_group(self.pathname)
        group.attrs['length'] = 100
        group.create_dataset('y_values', data=self.datavec)
