import epics
import h5py
import threading
import time


def hush():
    """
    Remove warnings from epics. These can be helpful, but we get a lot of
    warnings about 'Identical process variable names on multiple servers'
    """
    epics.ca.replace_printf_handler(lambda text: None)


class Coolector(object):
    """
    Collect data from Cool devices, put them in HDF5 files
    """
    triggerID = 0
    __devices = []
    __listen = False
    thread = None

    def __listening(self):
        print('Listening!')
        while(self.__listen):
            ready = True
            for dev in self.__devices:
                if(not dev.is_ready_p()):
                    ready = False
            if(ready):
                self.triggerID += 1
                self.write(self.triggerID)
        print('Shutting down collection!')

    def sw_trigger(self):
        for dev in self.__devices:
            dev.sw_trigger()

    def write(self, trigger):
        timestamp = time.time()
        fname = '{0}{1:016d}-{2}.h5'.format(self.directory, trigger, self.sample)
        print('Writing to ' + fname)
        with h5py.File(fname, 'w') as h5f:
            attrs = h5f.get('/').attrs
            attrs['timestamp'] = timestamp
            attrs['trigger_id'] = trigger
            for attr, value in self.attrs.items():
                attrs[attr] = value
            for dev in self.__devices:
                dev.write(h5f)

    def __init__(self, sample=None, sample_uid=None, location=None, operator=None,
                 description=None, sub_experiment=None, directory=None):
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
        self.__devices.append(device)

    def start(self):
        if(self.__listen):
            print('Thread seems to already running! not starting a new one.')
        else:
            self.__listen = True
            self.thread = threading.Thread(target=self.__listening, args=())
            self.thread.start()
            print('Started thread!')

    def stop(self):
        self.__listen = False

    def disconnect(self):
        for dev in self.__devices:
            dev.disconnect()


class Cool_device(object):
    """
    Write device info to HDF5
    """
    port = None
    pathname = None
    dev_type = None
    is_ready = False
    meta_pvnames = []
    ds_pvnames = []
    connected_pvs = []

    def set_ready(self): self.is_ready = True

    def sw_trigger(): pass

    def is_ready_p(self): return(self.is_ready)

    def write(self, h5f):
        group = h5f.require_group(self.pathname)
        group.attrs['instrument_name'] = self.dev_type
        for pvname in self.meta_pvnames:
            group.attrs[pvname] = epics.caget(pvname)
        for pvname in self.ds_pvnames:
            group.create_dataset(pvname, data=epics.caget(pvname))
        self.is_ready = False

    def disconnect(self):
        for pv in self.connected_pvs:
            pv.disconnect()


class Manta_cam(Cool_device):
    """
    Manta camera
    """
    dev_type = 'Manta camera'

    def sw_trigger(self): epics.caput(self.port + ':det1:Acquire', 1)

    def __init__(self, port, SWTrig=False):
        """
        Initialize a manta camera
        """
        self.port = port
        self.pathname = 'data/images/' + port + '/'
        self.arraydata = port + ':image1:ArrayData'
        # PVs that will be dumped to file
        self.meta_pvnames[:] = [self.port + pvn for pvn in [':det1:SizeX_RBV',
                                                            ':det1:SizeY_RBV',
                                                            ':det1:Manufacturer_RBV',
                                                            ':det1:Model_RBV',
                                                            ':det1:AcquireTime_RBV',
                                                            ':det1:Gain_RBV',
                                                            ':det1:LEFTSHIFT_RBV',
                                                            ':det1:DataType_RBV']]
        # Set is_ready to True when there is new data
        pv = epics.PV(self.port + ':image1:ArrayData',
                      auto_monitor=True,
                      callback=lambda pvn=None, v=None, cv=None, **fw: self.set_ready())
        self.connected_pvs.append(pv)
        if(SWTrig):
            for pvname, value in {':image1:EnableCallbacks': 1,  # Enable
                                  ':image1:ArrayCallbacks': 1,  # Enable
                                  ':det1:ImageMode': 0,  # Get a single image
                                  ':det1:DataType': 1,  # UInt16, 12-bit
                                  ':det1:LEFTSHIFT': 0}.items():  # Disable
                epics.caput(port + pvname, value)
        else:
            raise Exception('Not yet implemented')

    def write(self, h5f):
        """
        Overload write to file function. Needed here in order to reshape
        the image from array to vector.
        """
        super(Manta_cam, self).write(h5f)
        raw = epics.caget(self.arraydata)
        raw = raw.reshape(epics.caget(self.port + ':det1:SizeY_RBV'),
                          epics.caget(self.port + ':det1:SizeX_RBV'))
        group = h5f.get(self.pathname)
        group.create_dataset(self.arraydata, data=raw)


class Thorlabs_spectrometer(Cool_device):
    """
    Thorlabs CCS spectrometer
    """
    dev_type = 'Thorlabs spectrometer'

    def sw_trigger(self): epics.caput(self.port + ':det1:Acquire', 1)

    def __init__(self, port, SWTrig=False):
        """
        Initialize a Thorlabs spectrometer
        """
        self.port = port
        self.pathname = 'data/spectra/' + port + '/'
        self.arraydata = port + ':trace1:ArrayData'
        # PVs that will be dumped to file
        self.meta_pvnames[:] = [self.port + pvn for pvn in [':det1:AcquireTime_RBV',
                                                            ':det1:Manufacturer_RBV',
                                                            ':det1:Model_RBV']]
        self.ds_pvnames = [port + pvn for pvn in [':trace1:ArrayData',
                                                  ':det1:TlAmplitudeData_RBV',
                                                  ':det1:TlWavelengthData_RBV']]
        # Set is_ready to True when there is new data
        pv = epics.PV(self.port + ':trace1:ArrayData',
                      auto_monitor=True,
                      callback=lambda pvn=None, v=None, cv=None, **fw: self.set_ready())
        self.connected_pvs.append(pv)
        if(SWTrig):
            for pvname, value in {':det1:ImageMode': 0,  # Single
                                  ':det1:TlAcquisitionType': 0,  # 1 is processed, set to 0 for raw
                                  ':det1:TriggerMode': 0,  # Internal
                                  ':trace1:EnableCallbacks': 1,  # Enable
                                  ':trace1:ArrayCallbacks': 1,  # Enable
                                  ':det1:TlAmplitudeDataTarget': 2,  # Thorlabs
                                  ':det1:TlWavelengthDataTarget': 0,
                                  ':det1:TlAmplitudeDataGet': 1,
                                  ':det1:TlWavelengthDataGet': 1}.items():  # Factory
                epics.caput(port + pvname, value)
        else:
            raise Exception('Not yet implemented')
