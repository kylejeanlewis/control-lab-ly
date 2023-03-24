# %% -*- coding: utf-8 -*-
"""
Created: Tue 2022/11/01 17:13:35
@author: Chang Jie

Notes / actionables:
- 
"""
# Standard library imports
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
import numpy as np
from typing import Optional, Union

# Local application imports
print(f"Import: OK <{__name__}>")

PRE_FILL_CYCLES = 1

@dataclass
class Speed:
    up: float
    down: float

class LiquidHandler(ABC):
    """
    Liquid handler class

    Args:
        **kwargs: catch-all for stray inputs
    """
    _default_flags: dict[str, bool] = {'busy': False, 'connected': False}
    def __init__(self, verbose:bool = False, **kwargs):
        self.capacity = 0
        self.channel = 0
        self.reagent = ''
        self.speed = Speed(0,0)
        self.volume = 0
        self._offset = (0,0,0)
        
        self.connection_details = {}
        self.device = None
        self.flags = self._default_flags.copy()
        self.verbose = verbose
        return

    @abstractmethod
    def aspirate(self, 
        volume: float, 
        speed: Optional[float] = None, 
        wait: int = 0, 
        pause: bool = False, 
        reagent: Optional[str] = None, 
        channel: Optional[Union[int, tuple[int]]] = None,
        **kwargs
    ) -> bool:
        """
        Aspirate desired volume of reagent into channel

        Args:
            volume (int, or float): volume to be aspirated
            speed (int, optional): speed to aspirate. Defaults to None.
            wait (int, optional): wait time between steps in seconds. Defaults to 0.
            reagent (str, optional): name of reagent. Defaults to ''.
            pause (bool, optional): whether to pause for intervention / operator input. Defaults to False.
            channel (int, optional): channel to aspirate. Defaults to None.
        """
    
    @abstractmethod
    def blowout(self, channel: Optional[Union[int, tuple[int]]] = None, **kwargs) -> bool:
        """
        Blowout liquid from tip

        Args:
            channel (int, optional): channel to pullback. Defaults to None.
        """

    @abstractmethod
    def disconnect(self):
        ...
    
    @abstractmethod
    def dispense(self, 
        volume: float, 
        speed: Optional[float] = None, 
        wait: int = 0, 
        pause: bool = False, 
        blowout: bool = False,
        force_dispense: bool = False, 
        channel: Optional[Union[int, tuple[int]]] = None,
        **kwargs
    ) -> bool:
        """
        Dispense desired volume of reagent from channel

        Args:
            volume (int, or float): volume to be dispensed
            speed (int, optional): speed to dispense. Defaults to None.
            wait (int, optional): wait time between steps in seconds. Defaults to 0.
            force_dispense (bool, optional): whether to continue dispensing even if insufficient volume in channel. Defaults to False.
            pause (bool, optional): whether to pause for intervention / operator input. Defaults to False.
            channel (int, optional): channel to dispense. Defaults to None.
        """

    @abstractmethod
    def pullback(self, channel: Optional[Union[int, tuple[int]]] = None, **kwargs) -> bool:
        """
        Pullback liquid from tip

        Args:
            channel (int, optional): channel to pullback. Defaults to None.
        """

    @abstractmethod
    def _connect(self):
        self.connection_details = {}
        self.device = None
        self.setFlag(connected=True)
        return

    # Properties
    @property
    def offset(self) -> np.ndarray:
        return np.array(self._offset)
    @offset.setter
    def offset(self, value:tuple[float]):
        if len(value) != 3:
            raise Exception('Please input x,y,z offset')
        self._offset = tuple(value)
        return
    
    def connect(self):
        """
        Reconnect to device using existing port and baudrate
        
        Returns:
            `serial.Serial`: serial connection to machine control unit if connection is successful, else `None`
        """
        return self._connect(**self.connection_details)
    
    def cycle(self, 
        volume: float, 
        speed: Optional[float] = None, 
        wait: int = 0,  
        cycles: int = 1,
        reagent: Optional[str] = None, 
        channel: Optional[Union[int, tuple[int]]] = None,
        **kwargs
    ) -> bool:
        """
        Cycle the channel with aspirate and dispense

        Args:
            volume (int, or float): volume to be cycled
            speed (int, optional): speed to cycle. Defaults to None.
            wait (int, optional): wait time between steps in seconds. Defaults to 0.
            reagent (str, optional): name of reagent. Defaults to ''.
            cycles (int, optional): number of cycles to perform. Defaults to 1.
            channel (int, optional): channel to cycle. Defaults to None.
        """
        success = []
        for _ in range(cycles):
            ret1 = self.aspirate(volume=volume, speed=speed, wait=wait, pause=False, reagent=reagent, channel=channel)
            ret2 = self.dispense(volume=volume, speed=speed, wait=wait, pause=False, force_dispense=True, channel=channel)
            success.extend([ret1,ret2])
        return all(success)

    def empty(self, 
        speed: Optional[float] = None, 
        wait: int = 0, 
        pause: bool = False, 
        channel: Optional[Union[int, tuple[int]]] = None,
        **kwargs
    ) -> bool:
        """
        Empty the channel of its contents

        Args:
            speed (int, optional): speed to empty. Defaults to None.
            wait (int, optional): wait time between steps in seconds. Defaults to 0.
            pause (bool, optional): whether to pause for intervention / operator input. Defaults to False.
            channel (int, optional): channel to empty. Defaults to None.
        """
        ret1 = self.dispense(volume=self.capacity, speed=speed, wait=wait, pause=pause, force_dispense=True, channel=channel)
        ret2 = self.blowout(channel=channel)
        return all([ret1,ret2])
    
    def fill(self, 
        speed: Optional[float] = None, 
        wait: int = 0, 
        pause: bool = False, 
        cycles: int = PRE_FILL_CYCLES,
        reagent: Optional[str] = None, 
        channel: Optional[Union[int, tuple[int]]] = None,
        **kwargs
    ) -> bool:
        """
        Fill the channel with reagent to its capacity

        Args:
            speed (int, optional): speed to fill. Defaults to None.
            wait (int, optional): wait time between steps in seconds. Defaults to 0.
            reagent (str, optional): name of reagent. Defaults to ''.
            pause (bool, optional): whether to pause for intervention / operator input. Defaults to False.
            cycles (bool, optional): whether to pre-wet the channel. Defaults to True.
            channel (int, optional): channel to fill. Defaults to None.
        """
        ret1 = self.cycle(volume=self.capacity, speed=speed, wait=wait, cycles=cycles, reagent=reagent, channel=channel)
        ret2 = self.aspirate(volume=self.capacity, speed=speed, wait=wait, pause=pause, reagent=reagent, channel=channel)
        ret3 = self.pullback(channel=channel)
        return all([ret1,ret2,ret3])
    
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
    
    def rinse(self, 
        speed: Optional[float] = None, 
        wait: int = 0, 
        cycles: int = 3, 
        channel: Optional[Union[int, tuple[int]]] = None,
        **kwargs
    ) -> bool:
        """
        Rinse the channel with aspirate and dispense cycles

        Args:
            volume (int, or float): volume to be rinsed
            speed (int, optional): speed to cycle. Defaults to None.
            wait (int, optional): wait time between steps in seconds. Defaults to 0.
            reagent (str, optional): name of reagent. Defaults to ''.
            cycles (int, optional): number of cycles to perform. Defaults to 3.
            channel (int, optional): channel to cycle. Defaults to None.
        """
        return self.cycle(volume=self.capacity, speed=speed, wait=wait, cycles=cycles, channel=channel)
    
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

    # Protected method(s)
    def _diagnostic(self):
        """
        Run diagnostic on tool
        """
        self.pullback()
        return
