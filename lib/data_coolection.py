import h5py
import epics
import threading
import time
import scipy.ndimage
import moveStage
import numbers
from ps4262 import ps4262


def hush():
    """
    Remove warnings from epics. These can be helpful, but we get a lot of
    warnings about 'Identical process variable names on multiple servers'
    """
    epics.ca.replace_printf_handler(lambda text: None)


# x-label, y-label, units

def val_or_retval(thing):
    """ Is this a value or a function? """
    if(callable(thing)):
        return(thing())
    else:
        return(thing)


class Dataset(object):
    """ This object sets up the saving of a HDF5 dataset """
    def __init__(self, dsname, data_fun):
        self.dsname = dsname  # String
        self.data = data_fun  # A function that returns data
        self.attrs = {}  # Attributes to the dataset

    def write(self, h5g):
        data = val_or_retval(self.data)
        ds = h5g.create_dataset(self.dsname, data=data, compression='gzip')
        for key, value in self.attrs.items():
            ds.attrs[key] = val_or_retval(value)


class Savedata(object):
    """ This object keeps track of things that should be saved to file for a device"""
    def __init__(self, groupname, dev_type):
        self.groupname = groupname
        self.attrs = {}  # Attr name -> attr value
        self.attrs['instrument_name'] = dev_type
        self.datasets = []  # Name, data, attrs, processor

    def add_dataset(self, ds):
        self.datasets.append(ds)

    def write(self, h5f):
        h5g = h5f.require_group(self.groupname)
        # Group attributes
        print(self.groupname)
        for key, val in self.attrs.items():
            # print(str(key) + ': ' + str(val_or_retval(val)) + ':' + str(val))
            h5g.attrs[key] = val_or_retval(val)
        # Datasets
        for dataset in self.datasets:
            dataset.write(h5g)

    def write_additional_meta(self, h5f, dict):
        h5g = h5f.require_group(self.groupname)
        for key, val in dict.items():
            h5g.attrs[key] = val


class Coolector(object):
    """
    Collect data from Cool devices, put them in HDF5 files.
    """
    pause = 0.001
    triggerID = 0
    _devices = []

    latest_file_name = None

    def __init__(self, session=None, sample=None, sample_uid=None, location=None, operator=None,
                 description=None, sub_experiment=None, directory=None):
        """
        Init function. Meta data as mandatory arguments.
        """
        if(not(sample and description and directory and sample_uid and location and
               sample_uid and operator and sub_experiment and session)):
            raise Exception('Supply sample, sample_uid, location, operator, ' +
                            'description, directory abd sub_experiment')
        self.sample = sample
        self.sample_uid = sample_uid
        self.glob_trig = 0

        self.savedata = Savedata('/', 'Configuration')
        self.savedata.attrs['sample_name'] = lambda: self.sample
        self.savedata.attrs['sample_guid'] = lambda: self.sample_uid
        self.savedata.attrs['location'] = location
        self.savedata.attrs['session'] = session
        self.savedata.attrs['operator_name'] = operator
        self.savedata.attrs['experiment_description'] = description
        self.savedata.attrs['sub_experiment'] = sub_experiment
        self.savedata.attrs['trigger_id'] = lambda: self.glob_trig
        self.savedata.attrs['internal_trigger_count'] = lambda: self.triggerID
        self.savedata.attrs['File creation  time'] = lambda: time.time()

        self.directory = directory
        if(not self.directory.endswith('/')):
            self.directory += '/'

    def change_sample(self, sample, sample_uid):
        moved = False
        for dev in self._devices:
            if(dev.move_to_sample(sample)):
                moved = True
        if moved:
            self.sample = sample
            self.sample_uid = sample_uid
        else:
            print('Do not know how to change samples, add a sample mover')
        
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

    def wait_for_data(self, timeout=15):
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
                for dev in self._devices:
                    print(dev.dev_type + ' is ready: ' + str(dev.is_ready_p()))
                print('Timed out while waiting for trigger!')
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

    def hw_trigger(self):
        """
        Send SW trigger to all connected devices
        """
        triggers = 0
        for dev in self._devices:
            if(dev.hw_trigger()):
                triggers = triggers + 1
        if triggers == 0:
            print('Found no devices avble to send a HW trigger')
        if triggers > 1:
            print('Several trigger generators attached')

    def write(self, trigger):
        """
        Write meta data + device data for all connected devices
        """
        # Get global trigger from device, or use internal counter
        self.triggerID += 1
        trigger = self.triggerID
        for dev in self._devices:
            glob_trig = dev.get_glob_trigger()
            if(glob_trig):
                print('Setting global trigger to ' + str(glob_trig))
                trigger = glob_trig
                self.glob_trigger = glob_trig

        # Create file, write to it
        fname = '{0}{1:016d}-{2}.h5'.format(self.directory, trigger, self.sample)
        print('Writing to ' + fname)
        with h5py.File(fname, 'w') as h5f:
            h5f.attrs['write_finished'] = False
            self.savedata.write(h5f)
            for dev in self._devices:
                dev.write(h5f)
            h5f.attrs['write_finished'] = True
        # All devices are read out, ready for new data
        self.latest_file_name = fname
        for dev in self._devices:
            dev.clear()

    def add_device(self, device):
        """
        Add a Cool_device to the coolector.
        """
        self._devices.append(device)

    def __enter__(self):
        """ Connect devices """
        if(self.directory == '/tmp/'):
            print('Saving to tmp!!!')
        for dev in self._devices:
            dev.connect()
        self.clear()
        return(self)

    def __exit__(self, type, value, traceback):
        """ Disconnect devices """
        if(self.directory == '/tmp/'):
            print('Saving to tmp!!!')
        for dev in self._devices:
            dev.disconnect()

    # Scans
    def wait_for_n_triggers(self, n, SW_trigger=False):
        with self as c:
            for trig in range(n):
                if(SW_trigger):
                    self.sw_trigger()
                else:
                    self.hw_trigger()
                print('Waiting for data!')
                c.wait_for_data()
                print(time.time())
                print("Got one! " + str(trig))

    def stage_scan_n_triggers(self, n, cool_stage, auto_exposure=False):
        for sample, position in cool_stage.sample_dict.items():
            self.sample = sample
            self.attrs['sample_name'] = sample
            cool_stage.move_stage(sample)
            # Auto exposure
            for dev in self._devices:
                if auto_exposure:
                    dev.auto_exposure()
            # Get triggers
            self.wait_for_n_triggers(n)


class Cool_device(object):
    """
    Base class for reading out a devices, and writing device info to HDF5
    """
    is_ready = False  # Flag that should be set to true when the device is ready for read out.
    potentially_desynced = False  # Did we recieve seceral triggers before writing finished?

    data = None
    timestamp = False
    triggercount = 0

    def __init__(self, port, pathname, dev_type, callback_pvname):
        self.connected_pvs = []
        # EPICS port, something like CAM1, CCS1. For non epics devices, make something up.
        self.port = port
        self._callback_pvname = callback_pvname  # Set to None for non-epivs devices
        self.dev_type = dev_type  # Descriptor for the device.

        self.savedata = Savedata(pathname, dev_type)
        if self.timestamp:
            self.savedata.attrs['Capture time'] = lambda: self.timestamp
        else:
            self.savedata.attrs['Capture time'] = lambda: time.time()
        self.savedata.attrs['trigger_count'] = lambda: self.triggercount
        self.savedata.attrs['Potentially desynced'] = lambda: self.potentially_desynced

    def get_glob_trigger(self):
        return(None)

    def move_to_sample(self, sample):
        return(False)

    def connect(self):
        # Set is_ready to True when there is new data using a callback
        print('Connecting ' + self.dev_type)
        if(self._callback_pvname):
            print('Connecting ' + self._callback_pvname)
            pv = epics.PV(self._callback_pvname,
                          auto_monitor=True,
                          callback=lambda pvname=None, value=None, timestamp=None, **fw: self.set_ready(pvname, value, timestamp))
            self.connected_pvs.append(pv)
        return(self)

    def disconnect(self):
        for pv in self.connected_pvs:
            pv.disconnect()
        self.connected_pvs = []

    def auto_exposure(self):
        """Do auto exposure. Trigger fun should give a single trigger working with
        the configured device."""
        pass

    def set_ready(self, pvn, value, timestamp):
        """
        Mark device as ready for read out, copy data to object.
        This is intended as a callback funtion for a EPICS pv
        """
        self.triggercount += 1
        print('Getting data to callback! ' + self.dev_type)
        if(not self.is_ready):
            print('Got data from ' + self.dev_type + ', aka: ' + str(pvn))
            self.data = value
            self.timestamp = timestamp
        else:
            print(self.dev_type + ": New trigger before readout finished! Potentially desynced event!")
            self.potentially_desynced = True
        self.is_ready = True

    def sw_trigger(self):
        """ Pass a SW trigger to the device """
        pass

    def hw_trigger(self):
        """ Pass a SW trigger to the device """
        pass

    def is_ready_p(self):
        """ Is the device ready for readout? EPICS devices rely on set_ready callback to set is_ready,
        non epics devices should probably overload """
        # print(self.dev_type + ' is ready? : ' + str(self.is_ready))
        return(self.is_ready)

    def clear(self):
        """ Clear data from device. For EPICS devices, sinply set is_ready to false. """
        self.is_ready = False
        self.potentially_desynced = False

    def write(self, h5f):
        """
        Write all pvs in meta_pvnames to attributes in group.
        Call write_datasets function.

        Overload if stuff needs to happen before write
        """
        self.savedata.write(h5f)

    def pv_to_attribute(self, prefix, *pvs):
        """
        Read pv values to attributes when needed
        """
        for pv in pvs:
            print(prefix + pv)
            self.savedata.attrs[prefix + pv] = lambda: epics.caget(prefix + pv)
        for pv in pvs:
            print(self.savedata.attrs[prefix + pv]())


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

    def get_reshaped_data(self):
        return(self.data.reshape(epics.caget(self.port + ':det1:SizeY_RBV'),
                                 epics.caget(self.port + ':det1:SizeX_RBV')))

    def __init__(self, port, lens_id, focal_length, f_number,
                 sw_trig=False,
                 exposure=None,
                 gain=None,
                 exposure_min=0.0003,
                 exposure_max=0.1,
                 photons_per_count=False):
        """
        Initialize a manta camera
        """
        super().__init__(port,
                         'data/images/' + port + '/',
                         'Manta camera',
                         port + ':image1:ArrayData')
        self.exposure_min = exposure_min
        self.exposure_max = exposure_max

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

        # Setting up data saving
        # Metadata that will be dumped to device
        sda = self.savedata.attrs
        sda['lens_id'] = lens_id
        sda['f_number'] = f_number
        sda['focal_length'] = focal_length
        sda['photons_per_count'] = photons_per_count
        sda[port + ':det1:SizeX_RBV'] = lambda: epics.caget(port + ':det1:SizeX_RBV')
        sda[port + ':det1:SizeY_RBV'] = lambda: epics.caget(port + ':det1:SizeY_RBV')
        sda[port + ':det1:Manufacturer_RBV'] = lambda: epics.caget(port + ':det1:Manufacturer_RBV')
        sda[port + ':det1:Model_RBV'] = lambda: epics.caget(port + ':det1:Model_RBV')
        sda[port + ':det1:AcquireTime_RBV'] = lambda: epics.caget(port + ':det1:AcquireTime_RBV')
        sda[port + ':det1:Gain_RBV'] = lambda: epics.caget(port + ':det1:Gain_RBV')
        sda[port + ':det1:LEFTSHIFT_RBV'] = lambda: epics.caget(port + ':det1:LEFTSHIFT_RBV')
        sda[port + ':det1:NumImagesCounter_RBV'] = lambda: epics.caget(port + ':det1:NumImagesCounter_RBV')
        sda[port + ':det1:DataType_RBV'] = lambda: epics.caget(port + ':det1:DataType_RBV')
        
        ds = Dataset('data', lambda: self.get_reshaped_data())
        ds.attrs['pvname'] = self._callback_pvname
        ds.attrs['x-label'] = 'Horizontal'
        ds.attrs['y-label'] = 'Vertical'
        ds.attrs['x-units'] = 'Pixels'
        ds.attrs['y-units'] = 'Pixels'
        self.savedata.add_dataset(ds)

    def auto_exposure(self):
        """ Auto exposure:
        - Set camera to single exposure modde
        - Find the correct exposure
        - Set camera back to initial configuration
        """
        print('Camera auto exposure!')
        self.connect()
        while(True):
            while(not self.is_ready_p()):
                time.sleep(0.1)
            exp = epics.caget(self.port + ':det1:AcquireTime_RBV')
            data = epics.caget(self.port + ':image1:ArrayData')
            data = data.reshape(epics.caget(self.port + ':det1:SizeY_RBV'),
                                epics.caget(self.port + ':det1:SizeX_RBV'))
            sm = scipy.ndimage.filters.median_filter(data, 9).max()
            max_image = 2**12 - 1
            exp = epics.caget(self.port + ':det1:AcquireTime_RBV')
            autoset = exp * (max_image * 0.5)/sm
            self.set_exposure(autoset)
            self.clear()
            if(autoset > self.exposure_max):
                print('Exposure set to max!')
                break
            if(autoset < self.exposure_min):
                print('Exposure set to min!')
                break
            if(autoset/exp > (1/1.5) and autoset/exp < 1.5):
                print('Exposure set to ' + str(autoset))
                break
        self.disconnect()
        return()


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
        super().__init__(port,
                         'data/spectra/' + port + '/',
                         self.dev_type,
                         port + ':trace1:ArrayData')

        # Initialize device
        for pvname, value in {':det1:TlAcquisitionType': 0,  # 1 is processed, set to 0 for raw
                              ':trace1:EnableCallbacks': 1,  # Enable
                              ':trace1:ArrayCallbacks': 1,  # Enable
                              ':det1:TlAmplitudeDataTarget': 2,  # Thorlabs
                              ':det1:TlWavelengthDataTarget': 0}.items():  # Factory
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

        epics.caput(port + ':det1:TlAmplitudeDataGet', 1)  # Get amplitudes
        epics.caput(port + ':det1:TlWavelengthDataGet', 1)  # Get waves

        # Set exposure from argument
        if(exposure):
            self.set_exposure(exposure)

        sda = self.savedata.attrs
        sda[port + ':det1:AcquireTime_RBV'] = lambda: epics.caget(port + ':det1:AcquireTime_RBV')
        sda[port + ':det1:NumImagesCounter_RBV'] = lambda: epics.caget(port + ':det1:NumImagesCounter_RBV')
        sda[port + ':det1:Model_RBV'] = epics.caget(self.port + ':det1:Model_RBV')
        sda[port + ':det1:Manufacturer_RBV'] = epics.caget(port + ':det1:Manufacturer_RBV')

        # Data sets
        pv1 = port + ':det1:TlWavelengthData_RBV'
        x_data = Dataset('x_values', lambda: epics.caget(pv1))
        x_data.attrs['pvname'] = pv1
        x_data.attrs['label'] = 'Wavelength'
        x_data.attrs['unit'] = 'nm'
        self.savedata.add_dataset(x_data)

        pv2 = port + ':trace1:ArrayData'
        y_data = Dataset('y_values', lambda: self.data)
        y_data.attrs['pvname'] = pv2
        y_data.attrs['label'] = 'Intensity'
        y_data.attrs['unit'] = 'Counts'
        self.savedata.add_dataset(y_data)

        pv3 = port + ':det1:TlAmplitudeData_RBV'
        scale_data = Dataset('y_scale', lambda: epics.caget(pv3))
        scale_data.attrs['pvname'] = pv3
        scale_data.attrs['label'] = 'Correction'
        scale_data.attrs['unit'] = 'Scale factor'
        self.savedata.add_dataset(scale_data)


class PicoscopePython(Cool_device):
    """
    Picoscope 4264 from ps4262.py
    """
    dev_type = 'PicoScope 4264, python'
    data = None

    def get_glob_trigger(self):
        # Get trigger number for last caught trigger
        print('Picoscope trigger count!')
        return(self.triggercount)
            
    def __init__(self, voltage_range=5, sampling_interval=1e-6,
                 capture_duration=0.66, trig_per_min=30):
        super().__init__('ps4264', 'data/oscope/ps4264py/', self.dev_type, None)
        self._ps = ps4262(VRange=voltage_range, requestedSamplingInterval=sampling_interval,
                          tCapture=capture_duration, triggersPerMinute=trig_per_min)
        # Configuring data for saving
        current = Dataset('y_data', lambda: self.data['current'])
        current.attrs['label'] = 'Current'
        current.attrs['unit'] = 'A'
        self.savedata.add_dataset(current)
        # Lambdas kalled during write(), queue should be 0
        self.potentially_desynced = len(self._ps.data) > 0
        self.savedata.attrs['Queue length'] = lambda: len(self._ps.data)
        self.metadata = {}

    def write(self, h5f):
        super().write(h5f)
        self.savedata.write_additional_meta(h5f, self.metadata)

    def is_ready_p(self):
        """If we do not have fresh data, wait for it. If we do, we are ready."""
        if(self.is_ready):
            return(True)
        if(len(self._ps.data) > 0):
            self.data = self._ps.data.popleft()
            self.timestamp = self.data['timestamp']
            self.triggercount = self._ps.edgesCaught
            self.is_ready = True
            self.metadata = self._ps.getMetadata()
        return(self.is_ready)

    def clear(self):
        """Should set _ps.data to None"""
        self.is_ready = False
        self._ps.data.clear()

    def sampling(self, sampling_interval, duration):
        """ Hor long, and at what frequency, will the recorded waveforms be? """
        self._ps.setTimeBase(requestedSamplingInterval=sampling_interval,
                             tCapture=duration)

    def triggers_per_minute(self, tpm):
        """ Set tmp to 0 for single pulse generation """
        self._ps.setFGrn(triggersPerMinute=tpm)

    def hw_trigger(self):
        print('PS will trigger!')
        self._ps.setFGen(triggersPerMinute=-1)
        time.sleep(.05)  # Should not ask for triggers to fast
        return(True)


class LinearStage(Cool_device):
    """ Code for setting up, reading position and moving the linear stage """
    dev_type = 'Standa linear stage'

    def __init__(self):
        super().__init__('standa',
                         'data/linearstage/standa/',
                         self.dev_type,
                         None)
        # self.pos = moveStage.get_position()
        moveStage.set_power_off_delay(0)
        self.sample_dict = {}
        # Save data
        self.savedata.attrs['Samples'] = lambda: list(self.sample_dict.keys())
        self.savedata.attrs['Positions'] = lambda: list(self.sample_dict.values())
        self.savedata.attrs['current_position'] = lambda: moveStage.get_position()

    def add_sample(self, name, position):
        self.sample_dict[name] = position

    def move_to_sample(self, sample):
        self.pos = self.sample_dict[sample]
        self.sample_name = sample
        moveStage.move_to(self.pos)
        time.sleep(0.1)
        return(True)

    def write_datasets(self, h5g):
        h5g.attrs['Current_position'] = self.pos
        h5g.attrs['Current_sample'] = self.sample_name
        for sample, pos in self.sample_dict.items():
            h5g.attrs[sample] = pos

    def is_ready_p(self):
        return(True)


class SuperCool(Cool_device):
    dev_type = 'LairdTech temperature regulator'

    def __init__(self):
        self.port = 'LT59'
        super().__init__('LT59', 'data/temperature/LT59/', self.dev_type, None)
        self.triggercount = 0

        # Initialize device
        epics.caput('LT59:Retrieve', 1)
        epics.caput('LT59:Temp1Mode', 1)
        epics.caput('LT59:Temp1CoeffA', 3.9083E-3)
        epics.caput('LT59:Temp1CoeffB', -5.7750E-7)
        epics.caput('LT59:Temp1CoeffC', 1000)
        epics.caput('LT59:Mode', 6)
        epics.caput('LT59:Send', 1)

        # Set up data saving
        self.pv_to_attribute('',
                             'LT59:Temp1Mode',
                             'LT59:Temp1CoeffA_RBV',
                             'LT59:Temp1CoeffB_RBV',
                             'LT59:Temp1CoeffC_RBV',
                             'LT59:Mode_RBV',
                             'LT59:Temp1_RBV',
                             'LT59:StartStop_RBV')

    def write(self, h5g):
        epics.caput('LT59:Retrieve', 1)
        time.sleep(0.1)
        super().write(h5g)

    def is_ready_p(self):
        return(True)


class PM100(Cool_device):
    """
    Thorlabs PM100USB
    """
    dev_type = 'Thorlabs PM100USB'
    n_samples = 500

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
        super().__init__(port,
                         'data/powermeter/' + self.port + '/',
                         self.dev_type,
                         None)
        self.port = port
        self.pm_pv = self.port + ':MEAS:POW'

        # Saving data
        x_data = Dataset('x_values', lambda: self.times)
        x_data.attrs['label'] = 'Measurement time'
        x_data.attrs['units'] = 'seconds'
        self.savedata.add_dataset(x_data)

        y_data = Dataset('y_values', lambda: self.array_data)
        y_data.attrs['label'] = 'Power'
        y_data.attrs['units'] = 'Watts'
        y_data.attrs['pvname'] = self.pm_pv
        self.savedata.add_dataset(y_data)

    def write(self, h5f):
        # We must trigger an uptade to WAV_RBV before the PV is written to file
        epics.caput(self.port + ':SENS:CORR:WAV_RBV.PROC', 1)
        time.sleep(0.01)
        super().write(h5f)
