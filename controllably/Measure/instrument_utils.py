# %% -*- coding: utf-8 -*-
"""
Created: Tue 2022/11/02 17:13:35
@author: Chang Jie

Notes / actionables:
- add multi channel support
"""
# Standard library imports
from __future__ import annotations
from abc import ABC, abstractmethod
# Local application imports
print(f"Import: OK <{__name__}>")

class Instrument(ABC):
    _default_flags: dict[str, bool] = {'busy': False, 'connected': False}
    def __init__(self,
        verbose: bool = False,
        **kwargs
    ):
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
        ...
    
    @abstractmethod
    def reset(self):
        ...
    
    @abstractmethod
    def _connect(self, *args, **kwargs):
        """Connect to machine control unit"""
        self.connection_details = {}
        self.device = None
        self.setFlag(connected=True)
        return
    
    @abstractmethod
    def _query(self, *args, **kwargs):
        ...
        
    @abstractmethod
    def _read(self, *args, **kwargs):
        ...
        
    @abstractmethod
    def _write(self, *args, **kwargs):
        ...
    
    def close(self):
        return self.disconnect()

    def connect(self):
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
            print(f"{self.__class__} is not connected. Details: {self.connection_details}")
        return self.flags.get('connected', False)
    
    def open(self):
        return self.connect()
    
    def query(self, *args, **kwargs):
        return self._query(*args, **kwargs)
        
    def read(self, *args, **kwargs):
        return self._read(*args, **kwargs)
    
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
  
    def shutdown(self):
        self.reset()
        self.disconnect()
        return
    
    def write(self, *args, **kwargs):
        return self._write(*args, **kwargs)
   