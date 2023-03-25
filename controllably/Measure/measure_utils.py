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
from typing import Callable
# Local application imports
print(f"Import: OK <{__name__}>")

class Measurer(ABC):
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
    def clearCache(self):
        ...
    
    @abstractmethod
    def disconnect(self):
        ...
    
    @abstractmethod
    def reset(self):
        ...
    
    @abstractmethod
    def shutdown(self):
        ...
    
    @abstractmethod
    def _connect(self, *args, **kwargs):
        """Connect to machine control unit"""
        self.connection_details = {}
        self.device = None
        self.setFlag(connected=True)
        return
    
    # Properties
    @property
    def instrument(self) -> Callable:
        return self.device
    @instrument.setter
    def instrument(self, device:Callable):
        self.device = device
    
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
