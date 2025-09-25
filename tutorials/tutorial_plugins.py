# %%
from copy import deepcopy
import logging
import time
import random
from types import SimpleNamespace
from typing import NamedTuple, Iterable

from controllably.core.device import Device, StreamingDevice, BaseDevice, Data, WRITE_FORMAT, READ_FORMAT
from controllably.core import factory
from controllably.core.logging import CustomLevelFilter

logger = logging.getLogger(__name__)

OtherData = NamedTuple('OtherData', [('strdata', str),('intdata', int),('floatdata', float),('booldata', bool)])
OTHER_FORMAT = '{strdata};{intdata};{floatdata};{booldata}\n'

def generate_sample_data():
    return f'test_output;{random.randint(0,1000)};{random.random():.5};{bool(random.randint(0,1))}\n'

class MockConnection:
    def __init__(self, name:str='MockConnection', **kwargs):
        self.name = name
        self._open = False
        self._waiting = False
        self.count = 0
    def __enter__(self):
        self.open()
        return self
    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
        return
    def open(self):
        self._open = True
    def close(self):
        self._open = False
    def is_open(self) -> bool:
        return self._open
    def in_waiting(self) -> bool:
        return self._waiting
    def write(self, data:Iterable) -> int|None:
        if not self._open:
            raise ConnectionError
        return len(data) if data is not None else None
    def read(self) -> bytes:
        if not self._open:
            raise ConnectionError
        time.sleep(0.01)
        return generate_sample_data().encode()
    def read_all(self) -> bytes:
        if not self._open:
            raise ConnectionError
        try:
            return next(self._read_all())
        except StopIteration:
            return b''
    def _read_all(self):
        while self.count < 5:
            time.sleep(0.01)
            self._waiting = True
            self.count += 1
            yield generate_sample_data().encode()
        self._waiting = False
        self.count = 0
        return

class DeviceTemplate(BaseDevice):
    def __init__(self, 
        name: str = 'DeviceTemplate',
        *args,
        init_timeout:int = 1, 
        data_type: NamedTuple = Data,
        read_format:str = READ_FORMAT,
        write_format:str = WRITE_FORMAT,
        simulation:bool = False, 
        verbose:bool = False,
        **kwargs
    ):
        super().__init__(
            init_timeout=init_timeout, simulation=simulation, verbose=verbose, 
            data_type=data_type, read_format=read_format, write_format=write_format, **kwargs
        )
        self.connection: MockConnection = MockConnection()
        self.name = name
        return
    
    @property
    def name(self) -> str:
        return self.connection_details.get('name', '')
    @name.setter
    def name(self, value:str):
        self.connection_details['name'] = value
        self.connection.name = value
        return

class PartTemplate:
    _default_flags: SimpleNamespace = SimpleNamespace(busy=False, verbose=False)
    def __init__(self, *, verbose:bool = False, **kwargs):
        """
        Instantiate the class

        Args:
            verbose (bool, optional): verbosity of class. Defaults to False.
        """
        kwargs['device_type'] = kwargs.get('device_type', DeviceTemplate)
        self.device: Device|StreamingDevice = kwargs.get('device', factory.create_from_config(kwargs))
        self.flags: SimpleNamespace = deepcopy(self._default_flags)
        
        self._logger = logger.getChild(f"{self.__class__.__name__}.{id(self)}")
        self.verbose = verbose
        return
    
    @property
    def connection_details(self) -> dict:
        """Connection details for the device"""
        return self.device.connection_details
    
    @property
    def is_busy(self) -> bool:
        """Whether the device is busy"""
        return self.flags.busy
    
    @property
    def is_connected(self) -> bool:
        """Whether the device is connected"""
        return self.device.is_connected
    
    @property
    def verbose(self) -> bool:
        """Verbosity of class"""
        return self.flags.verbose
    @verbose.setter
    def verbose(self, value:bool):
        assert isinstance(value,bool), "Ensure assigned verbosity is boolean"
        self.flags.verbose = value
        level = logging.DEBUG if value else logging.INFO
        CustomLevelFilter().setModuleLevel(self._logger.name, level)
        return
    
    def connect(self):
        """Connect to the device"""
        if not self.device.is_connected:
            self.device.connect()
            time.sleep(2)
        return
    
    def disconnect(self):
        """Disconnect from the device"""
        if self.device.is_connected:
            self.device.disconnect()
            time.sleep(1)
        return
    
    def resetFlags(self):
        """Reset all flags to class attribute `_default_flags`"""
        self.flags = deepcopy(self._default_flags)
        return
    
    def shutdown(self):
        """Shutdown procedure for tool"""
        self.disconnect()
        self.resetFlags()
        return


class PartOne(PartTemplate):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        return
    
    def method1(self, order, name, port, **kwargs):
        """
        method 1

        Args:
            order (int): order
            name (int): name
            port (str): port

        Returns:
            str: output
        """
        out = self.device.query(f"{order=}, {name=}, {port=}")
        time.sleep(3)
        return out 
    
    def method3(self):
        """
        method 3
        
        Returns:
            None
        """
        out = self.device.query('method3')
        time.sleep(1)
        return out
    
    def method5__(self):
        """
        method 5
        
        Returns:
            None
        """


class PartTwo(PartTemplate):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        return
    
    def method2(self, order, name, port, **kwargs):
        """
        method 2

        Args:
            order (int): order
            name (int): name
            port (str): port

        Returns:
            str: output
        """
        out = self.device.query(f"{order=}, {name=}, {port=}")
        time.sleep(3)
        return out  
    
    def method4(self):
        """
        method 4
        
        Returns:
            None
        """
        out = self.device.query('method4')
        time.sleep(1)
        return out
    
    def method6__(self):
        """
        method 6
        
        Returns:
            None
        """
