# %% -*- coding: utf-8 -*-
"""
This module holds the base class for measurement instruments.

Classes:
    Instrument (ABC)
"""
# Standard library imports
from __future__ import annotations
from abc import ABC, abstractmethod
print(f"Import: OK <{__name__}>")

class Instrument(ABC):
    """
    Abstract Base Class (ABC) for Instrument objects (i.e. tools that interface with characterisation instruments).
    ABC cannot be instantiated, and must be subclassed with abstract methods implemented before use.
    
    ### Constructor
    Args:
        `verbose` (bool, optional): verbosity of class. Defaults to False.
    
    ### Attributes
    - `connection_details` (dict): dictionary of connection details (e.g. COM port / IP address)
    - `device` (Callable): device object that communicates with physical tool
    - `flags` (dict[str, bool]): keywords paired with boolean flags
    - `verbose` (bool): verbosity of class
    
    ### Methods
    #### Abstract
    - `disconnect`: disconnect from device
    - `reset`: reset the instrument
    - `_connect`: connection procedure for tool
    - `_query`: write command to and read response from device
    - `_read`: read response from device
    - `_write`: write command to device
    #### Public
    - `close`: close connection to device. Alias for `disconnect()`.
    - `connect`: establish connection with device
    - `isBusy`: checks and returns whether the device is busy
    - `isConnected`: checks and returns whether the device is connected
    - `open`: open connection to device. Alias for `connect()`.
    - `query`: write command to and read response from device
    - `read`: read response from device
    - `resetFlags`: reset all flags to class attribute `_default_flags`
    - `setFlag`: set flags by using keyword arguments
    - `shutdown`: shutdown procedure for tool
    - `write`: write command to device
    """
    
    _default_flags: dict[str, bool] = {'busy': False, 'connected': False}
    def __init__(self,
        verbose: bool = False,
        **kwargs
    ):
        """
        Instantiate the class

        Args:
            verbose (bool, optional): verbosity of class. Defaults to False.
        """
        self.connection_details = {}
        self.device = None
        self.flags = self._default_flags.copy()
        self.verbose = verbose
        return
    
    def __del__(self):
        self.shutdown()
        return
    
    @abstractmethod
    def disconnect(self):
        """Disconnect from device"""
    
    @abstractmethod
    def reset(self):
        """Reset the instrument"""
    
    @abstractmethod
    def _connect(self, *args, **kwargs):
        """Connection procedure for tool"""
        self.connection_details = {}
        self.device = None
        self.setFlag(connected=True)
        return
    
    @abstractmethod
    def _query(self, *args, **kwargs):
        """Write command to and read response from device"""
        
    @abstractmethod
    def _read(self, *args, **kwargs):
        """Read response from device"""
        
    @abstractmethod
    def _write(self, *args, **kwargs):
        """Write command to device"""
    
    def close(self):
        """Close connection to device. Alias for `disconnect`."""
        return self.disconnect()

    def connect(self):
        """Establish connection with device"""
        return self._connect(**self.connection_details)

    def isBusy(self) -> bool:
        """
        Checks and returns whether the device is busy
        
        Returns:
            bool: whether the device is busy
        """
        return self.flags.get('busy', False)
    
    def isConnected(self) -> bool:
        """
        Checks and returns whether the device is connected

        Returns:
            bool: whether the device is connected
        """
        if not self.flags.get('connected', False):
            print(f"{self.__class__} is not connected. Details: {self.connection_details}")
        return self.flags.get('connected', False)
    
    def open(self):
        """Open connection to device. Alias for `connect()`."""
        return self.connect()
    
    def query(self, *args, **kwargs):
        """Write command to and read response from device"""
        return self._query(*args, **kwargs)
        
    def read(self, *args, **kwargs):
        """Read response from device"""
        return self._read(*args, **kwargs)
    
    def resetFlags(self):
        """Reset all flags to class attribute `_default_flags`"""
        self.flags = self._default_flags.copy()
        return

    def setFlag(self, **kwargs):
        """
        Set flags by using keyword arguments

        Kwargs:
            key, value: (flag name, boolean) pairs
        """
        if not all([type(v)==bool for v in kwargs.values()]):
            raise ValueError("Ensure all assigned flag values are boolean.")
        for key, value in kwargs.items():
            self.flags[key] = value
        return
  
    def shutdown(self):
        """Shutdown procedure for tool"""
        self.reset()
        self.disconnect()
        return
    
    def write(self, *args, **kwargs):
        """Write command to device"""
        return self._write(*args, **kwargs)
   