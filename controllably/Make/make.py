# -*- coding: utf-8 -*-
"""
This module holds the base class for maker tools.

## Classes:
    `Maker`: Base class for maker tools
    
<i>Documentation last updated: 2025-02-22</i>
"""
# Standard library imports
from __future__ import annotations
from copy import deepcopy
import logging
from types import SimpleNamespace

# Local application imports
from ..core import factory
from ..core.device import Device, StreamingDevice

# Configure logging
from controllably import CustomLevelFilter
logger = logging.getLogger(__name__)

class Maker:
    """
    Base class for maker tools.
    
    ### Constructor:
        `verbose` (bool, optional): verbosity of class. Defaults to False.
    
    ### Attributes and properties:
        `connection_details` (dict): connection details for the device
        `device` (Device): device object that communicates with physical tool
        `flags` (SimpleNamespace[str, bool]): flags for the class
        `is_busy` (bool): whether the device is busy
        `is_connected` (bool): whether the device is connected
        `verbose` (bool): verbosity of class
    
    ### Methods:
        `connect`: connect to the device
        `disconnect`: disconnect from the device
        `execute`: execute task
        `resetFlags`: reset all flags to class attribute `_default_flags`
        `run`: alias for `execute()`
        `shutdown`: shutdown procedure for tool
    """
    
    _default_flags: SimpleNamespace[str,bool] = SimpleNamespace(busy=False, verbose=False)
    def __init__(self, *, verbose:bool = False, **kwargs):
        """
        Instantiate the class

        Args:
            verbose (bool, optional): verbosity of class. Defaults to False.
        """
        self.device: Device|StreamingDevice = kwargs.get('device', factory.create_from_config(kwargs))
        self.flags: SimpleNamespace = deepcopy(self._default_flags)
        
        self._logger = logger.getChild(f"{self.__class__.__name__}.{id(self)}")
        self.verbose = verbose
        
        # Category specific attributes
        return
    
    def __del__(self):
        self.shutdown()
        return
    
    def __enter__(self):
        """Context manager enter method"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        """Context manager exit method"""
        self.disconnect()
        return False
    
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
        self.device.connect()
        return
    
    def disconnect(self):
        """Disconnect from the device"""
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
        self._logger.info("Executing task")
        raise NotImplementedError
    
    def run(self, *args, **kwargs):
        """Alias for `execute()`"""
        return self.execute(*args, **kwargs)
    