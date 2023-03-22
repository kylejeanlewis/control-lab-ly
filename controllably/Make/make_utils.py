# %% -*- coding: utf-8 -*-
"""
Created: Tue 2023/01/16 11:11:00
@author: Chang Jie

Notes / actionables:
-
"""
# Standard library imports
from abc import ABC, abstractmethod

# Third party imports

# Local application imports
print(f"Import: OK <{__name__}>")

class Maker(ABC):
    _default_flags = {}
    def __init__(self, **kwargs):
        self.connection_details = {}
        self.device = None
        self.flags = self._default_flags.copy()
        self.verbose = kwargs.get('verbose', False)
        return
    
    def __del__(self):
        self.shutdown()
    
    @abstractmethod
    def disconnect(self):
        ...
        
    @abstractmethod
    def shutdown(self):
        self.disconnect()
        self.resetFlags()
        return
        
    @abstractmethod
    def _connect(self, *args, **kwargs):
        """Connect to machine control unit"""
        self.connection_details = {}
        self.device = None
        return
    
    def connect(self):
        """
        Reconnect to device using existing port and baudrate
        
        Returns:
            `serial.Serial`: serial connection to machine control unit if connection is successful, else `None`
        """
        return self._connect(**self.connection_details)
    
    def isBusy(self) -> bool:
        """
        Check whether the device is busy
        
        Returns:
            `bool`: whether the device is busy
        """
        return self.flags.get('busy', False)
    
    def isConnected(self) -> bool:
        """
        Check whether the device is connected

        Returns:
            `bool`: whether the device is connected
        """
        if not self.flags.get('connected', False):
            print(f"{self.__class__} is not connected.")
        return self.flags.get('connected', False)
    
    def resetFlags(self):
        self.flags = self._default_flags.copy()
        return
    
    def setFlag(self, **kwargs):
        """
        Set a flag's truth value

        Args:
            `name` (str): label
            `value` (bool): flag value
        """
        if not all([type(v)==bool for v in kwargs.values()]):
            raise ValueError("Ensure all assigned flag values are boolean.")
        for key, value in kwargs.items():
            self.flags[key] = value
        return
    