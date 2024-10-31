# -*- coding: utf-8 -*-
"""
This module holds the base class for maker tools.

Classes:
    Maker (ABC)
"""
# Standard library imports
from __future__ import annotations
from copy import deepcopy
import logging
from types import SimpleNamespace

# Local application imports
from ..core.connection import DeviceFactory, Device

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.debug(f"Import: OK <{__name__}>")

class Maker:
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
    #### Public
    - `connect`: establish connection with device
    - `disconnect`: disconnect from device
    - `isBusy`: checks and returns whether the device is busy
    - `isConnected`: checks and returns whether the device is connected
    - `resetFlags`: reset all flags to class attribute `_default_flags`
    - `setFlag`: set flags by using keyword arguments
    """
    
    _default_flags: SimpleNamespace[str,bool] = SimpleNamespace(busy=False, verbose=False)
    def __init__(self, *, verbose:bool = False, **kwargs):
        """
        Instantiate the class

        Args:
            verbose (bool, optional): verbosity of class. Defaults to False.
        """
        self.device: Device = kwargs.get('device', DeviceFactory.createDeviceFromDict(kwargs))
        self.flags: SimpleNamespace = deepcopy(self._default_flags)
        self.verbose = verbose
        
        # Category specific attributes
        return
    
    def __del__(self):
        self.shutdown()
        return
    
    @property
    def connection_details(self) -> dict:
        """Get connection details"""
        return self.device.connection_details
    
    @property
    def is_busy(self) -> bool:
        """Check and return whether the device is busy"""
        return self.flags.busy
    
    @property
    def is_connected(self) -> bool:
        """Get connection status"""
        return self.device.is_connected
    
    @property
    def verbose(self) -> bool:
        """Get verbosity of class"""
        return self.flags.verbose
    @verbose.setter
    def verbose(self, value:bool):
        """Set verbosity of class"""
        assert isinstance(value,bool), "Ensure assigned verbosity is boolean"
        self.flags.verbose = value
        self.device.verbose = value
        level = logging.INFO if value else logging.WARNING
        logger.setLevel(level)
        for handler in logger.handlers:
            if isinstance(handler, type(logging.StreamHandler())):
                handler.setLevel(level)
        return
    
    def connect(self):
        """Reconnect to device using existing connection details"""
        self.device.connect()
        return
    
    def disconnect(self):
        """Disconnect from device"""
        self.device.disconnect()
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

    # Category specific properties and methods
    def execute(self, *args, **kwargs):
        """Execute task"""
        logger.info("Executing task")
        raise NotImplementedError
    
    def run(self, *args, **kwargs):
        """Alias for `execute()`"""
        return self.execute(*args, **kwargs)
    