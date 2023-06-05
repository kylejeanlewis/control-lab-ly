# %% -*- coding: utf-8 -*-
"""
This module holds the base class for maker tools.

Classes:
    Maker (ABC)
"""
# Standard library imports
from __future__ import annotations
from abc import ABC, abstractmethod
print(f"Import: OK <{__name__}>")

class Maker(ABC):
    """
    Abstract Base Class (ABC) for Maker objects (i.e. tools that process materials / samples).
    ABC cannot be instantiated, and must be subclassed with abstract methods implemented before use.
    
    ### Constructor
    Args:
        `verbose` (bool, optional): verbosity of class. Defaults to False.
    
    ### Attributes
    - `channel` (int): channel id
    - `connection_details` (dict): dictionary of connection details (e.g. COM port / IP address)
    - `device` (Callable): device object that communicates with physical tool
    - `flags` (dict[str, bool]): keywords paired with boolean flags
    - `verbose` (bool): verbosity of class
    
    ### Methods
    #### Abstract
    - `execute`: execute task
    - `shutdown`: shutdown procedure for tool
    - `_connect`: connection procedure for tool
    #### Public
    - `connect`: establish connection with device
    - `disconnect`: disconnect from device
    - `isBusy`: checks and returns whether the device is busy
    - `isConnected`: checks and returns whether the device is connected
    - `resetFlags`: reset all flags to class attribute `_default_flags`
    - `setFlag`: set flags by using keyword arguments
    """
    
    _default_flags: dict[str, bool] = {'busy': False, 'connected': False}
    def __init__(self, verbose:bool = False, **kwargs):
        """
        Instantiate the class

        Args:
            verbose (bool, optional): verbosity of class. Defaults to False.
        """
        self.channel = 0
        self.connection_details = {}
        self.device = None
        self.flags = self._default_flags.copy()
        self.verbose = verbose
        return
    
    def __del__(self):
        self.shutdown()
        
    @abstractmethod
    def execute(self, *args, **kwargs):
        """Execute task"""
        
    @abstractmethod
    def shutdown(self):
        """Shutdown procedure for tool"""
        self.disconnect()
        self.resetFlags()
        return
        
    @abstractmethod
    def _connect(self, *args, **kwargs):
        """Connection procedure for tool"""
        self.connection_details = {}
        self.device = None
        self.setFlag(connected=True)
        return
    
    def connect(self):
        """Reconnect to device using existing connection details"""
        return self._connect(**self.connection_details)
    
    def disconnect(self):
        """Disconnect from device"""
        try:
            self.device.close()
        except Exception as e:
            if self.verbose:
                print(e)
        self.setFlag(connected=False)
        return
    
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
        self.flags.update(kwargs)
        # for key, value in kwargs.items():
        #     self.flags[key] = value
        return
    