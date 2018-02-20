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
    latest_file_name = None

    def check_if_ready(self):
        """
        Are all devices ready for ready out?
        """
        ready = True
        for dev in self._devices:
            if(not dev.is_ready_p()):
                ready = False
        return(ready)

    def clear(self):
        """
        Clear devices of old data.
        """
        for dev in self._devices:
            dev.clear()

    def cd(self, dir):
        """ Change directory """
        self.directory = dir

    def wait_for_data(self, timeout=30):
        """
        Wait until all devices are ready, then read them all out.
        """
        tzero = time.time()
        got_data_p = False
        while(True):
            if(self.check_if_ready()):
                got_data_p = True
                break
            if(time.time() - tzero > timeout):
                break
            time.sleep(self.pause)
        if(got_data_p):
            self.write(self.triggerID)

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
        self.latest_file_name = fname
        for dev in self._devices:
            dev.clear()
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
        device.clear()

    # Code below starts a thread listening for triggers, instead of waiting in the main thread
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
    port = None  # EPICS port, something like CAM1, CCS1. For non epics devices, make something up.
    pathname = None  # Path to group in h5 files. Something like /data/images/ + port
    dev_type = None  # Descriptor for the device.
    is_ready = False  # Flag that should be set to true when the device is ready for read out.
    potentially_desynced = False  # Did we recieve seceral triggers before writing finished?

    meta_pvnames = []
    connected_pvs = []

    def set_ready(self, pvn, value):
        """
        Mark device as ready for read out, copy data to object.
        This is intended as a callback funtion for a EPICS pv
        """
        if(self.is_ready):
            warnings.warn("New trigger before readout finished! potentially desynced event!")
            self.potentially_desynced = True
        self.is_ready = True

    def sw_trigger():
        """ Pass a SW trigger to the device """
        pass

    def is_ready_p(self):
        """ Is the device ready for readout? EPICS devices rely on set_ready callback to set is_ready,
        non epics devices should probably overload """
        return(self.is_ready)

    def clear(self):
        """ Clear data from device. For EPICS devices, sinply set is_ready to false. """
        self.is_ready = False

    def write_datasets(self, group):
        """
        Many EPICS data sets need some formatting before writing, which can be done here.
        This is called from the write method.
        """
        pass

    def write(self, h5f):
        """
        Write all pvs in meta_pvnames to attributes in group.
        Call write_datasets function.
        """
        group = h5f.require_group(self.pathname)
        group.attrs['instrument_name'] = self.dev_type
        for pvname in self.meta_pvnames:
            group.attrs[pvname] = epics.caget(pvname)
        group.attrs['Potentially desynced'] = self.potentially_desynced
        self.write_datasets(group)

    def pv_to_hdf5(self, prefix, *pvs):
        """
        Helper function for formatting pv names with prefixes.
        """
        for pv in pvs:
            self.meta_pvnames.append(prefix + pv)


class Manta_cam(Cool_device):
    """
    Manta camera
    """
    dev_type = 'Manta camera'

    def sw_trigger(self):
        """ Set Acquire to True """
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

        # PVs that will be dumped to file
        self.pv_to_hdf5(self.port,
                        ':det1:SizeX_RBV',
                        ':det1:SizeY_RBV',
                        ':det1:Manufacturer_RBV',
                        ':det1:Model_RBV',
                        ':det1:AcquireTime_RBV',
                        ':det1:Gain_RBV',
                        ':det1:LEFTSHIFT_RBV',
                        ':det1:NumImagesCounter_RBV',
                        ':det1:DataType_RBV')

        # When port + :image1:ArrayData has new data, we are ready for read out
        # Callback function sets the is_ready flag to True
        pv = epics.PV(self.port + ':image1:ArrayData',
                      auto_monitor=True,
                      callback=lambda pvn=None, v=None, cv=None, **fw: self.set_ready(pvn, v))
        self.connected_pvs.append(pv)

        # Initialize device
        for pvname, value in {':image1:EnableCallbacks': 1,  # Enable
                              ':image1:ArrayCallbacks': 1,  # Enable
                              ':det1:DataType': 1,  # UInt16, 12-bit
                              ':det1:LEFTSHIFT': 0}.items():  # Disable
            epics.caput(port + pvname, value)

        # Initialization for SW triggers
        if(sw_trig):
            epics.caput(port + ':det1:ImageMode', 0)  # Get a single image
        # Initialization for HW triggers
        else:
            epics.caput(port + ':det1:Acquire', 0)
            epics.caput(port + ':det1:ImageMode', 2)  # Get images continously
            epics.caput(port + ':det1:TriggerMode', 1)  # Enable trigger mode
            epics.caput(port + ':det1:TriggerSelector', 0)  # Enable trigger mode
            epics.caput(port + ':det1:TriggerSource', 1)  # Enable trigger mode
            epics.caput(port + ':det1:Acquire', 1)

        # Set exposure and gain from init arguments
        if(exposure):
            self.set_exposure(exposure)
        if(isinstance(gain, numbers.Number)):  # We must be able to set this to 0
            self.set_gain(gain)

    def write_datasets(self, h5g):
        data = epics.caget(self.port + ':image1:ArrayData')
        data = data.reshape(epics.caget(self.port + ':det1:SizeY_RBV'),
                            epics.caget(self.port + ':det1:SizeX_RBV'))
        ds = h5g.create_dataset('data', data=data)
        ds.attrs['pvname'] = self.port + ':image1:ArrayData'
        # Auto exposure, this should happen after all pvs are written to file
        if(self.auto_exposure):
            sm = scipy.ndimage.filters.median_filter(data, 9).max()
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
        self.arraydatapv = port + ':trace1:ArrayData'

        # PVs that will be dumped to file
        self.pv_to_hdf5(self.port,
                        ':det1:AcquireTime_RBV',
                        ':det1:Manufacturer_RBV',
                        ':det1:NumImagesCounter_RBV',
                        ':det1:Model_RBV')

        # Set is_ready to True when there is new data using a callback
        pv = epics.PV(self.port + ':trace1:ArrayData',
                      auto_monitor=True,
                      callback=lambda pvn=None, v=None, cv=None, **fw: self.set_ready(pvn, v))
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
            for pvname, value in {':det1:Acquire': 0,
                                  ':det1:ImageMode': 1,  # Continuous
                                  ':det1:TriggerMode': 1}.items():  # External
                epics.caput(port + pvname, value)
            epics.caput(port + ':det1:Acquire', 1)

        # Set exposure from argument
        if(exposure):
            self.set_exposure(exposure)

    def write_datasets(self, h5g):
        pvname = self.port + ':det1:TlWavelengthData_RBV'
        ds = h5g.create_dataset('x_values', data=epics.caget(pvname))
        ds.attrs['pvname'] = pvname

        pvname = self.port + ':det1:TlAmplitudeData_RBV'
        ds = h5g.create_dataset('y_scale', data=epics.caget(pvname))
        ds.attrs['pvname'] = pvname

        pvname = self.port + ':trace1:ArrayData'
        ds = h5g.create_dataset('y_data', data=epics.caget(pvname))
        ds.attrs['pvname'] = pvname


class Picoscope(Cool_device):
    """
    Picoscope 4262
    """
    dev_type = 'Thorlabs spectrometer'

    def sw_trigger(self): epics.caput(self.port + ':det1:Acquire', 1)

    def __init__(self, port, channel='A', range=0, sw_trig=False):
        """
        Initialize a picoscope
        """
        self.port = port
        self.pathname = 'data/wavefront/' + port + '/'
        self.arraydatapv = port + ':trace1:ArrayData'

        # PVs that will be dumped to file
        self.pv_to_hdf5(self.port,
                        ':det1:Serial_RBV',
                        # ':det1:Manufacturer_RBV',
                        ':det1:Model_RBV',
                        ':det1:TimeBase_RBV',
                        ':det1:DataType_RBV',
                        ':det1:ArrayCounter_RBV')

        # Set is_ready to True when there is new data using a callback
        pv = epics.PV(self.port + ':trace1:ArrayData',
                      auto_monitor=True,
                      callback=lambda pvn=None, v=None, cv=None, **fw: self.set_ready(pvn, v))
        self.connected_pvs.append(pv)

        # Initialize device
        for pvname, value in {':trace1:EnableCallbacks': 1,  # Enable
                              ':det1:ArrayCallbacks': 1}.items():  # Get waves
            epics.caput(port + pvname, value)

        for pvname, value in {'Enabled': 1,
                              'Coupling': 0,
                              'Range': range}.items():
            epics.caput(port + ':det1:' + channel + ':' + pvname, value)

        if(sw_trig):
            for pvname, value in {':det1:ExtTriggerEnabled': 0}.items():  # Internal
                epics.caput(port + pvname, value)
        else:
            # Acquire is toggeled, without this the picoscope is read out
            # without waiting for triggers
            for pvname, value in {':det1:Acquire': 0,
                                  ':det1:ExtTrigEnabled': 1,
                                  ':det1:ExtTrigRange': 1,
                                  ':det1:ExtTrigThr': 1000,
                                  ':det1:ExtTrigThrDir': 0}.items():
                epics.caput(port + pvname, value)
            epics.caput(port + ':det1:Acquire', 1)

    def write_datasets(self, h5g):
        pvname = self.port + ':trace1:ArrayData'
        ds = h5g.create_dataset('y_data', data=epics.caget(pvname))
        ds.attrs['pvname'] = pvname


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

    def write_datasets(self, h5g):
        ds = h5g.create_dataset('x_values', data=self.times)
        ds.attrs['pvname'] = 'Time from trigger'
        ds = h5g.create_dataset('y_values', data=self.array_data)
        ds.attrs['pvname'] = self.pm_pv

    def write(self, h5f):
        # We must trigger an uptade to WAV_RBV before the PV is written to file
        epics.caput(self.port + ':SENS:CORR:WAV_RBV.PROC', 1)
        time.sleep(0.01)
        super().write(h5f)


class RNG(Cool_device):
    """
    Print some random numbers to HDF5 as an example of a non epics device
    """
    dev_type = 'rng'
    datavec = None

    def populate(self):
        """ Some thing must set self.is_ready to true when device is ready for readout """
        self.datavec = numpy.random.rand(100)
        self.is_ready = True

    def sw_trigger(self):
        if(not self.is_ready):
            threading.Thread(target=self.populate, args=()).start()

    def __init__(self, port, sw_trig=False):
        self.port = port
        self.pathname = 'data/rng/' + self.port + '/'

    def write_datasets(self, h5g):
        h5g.create_dataset('y_values', data=self.datavec)
