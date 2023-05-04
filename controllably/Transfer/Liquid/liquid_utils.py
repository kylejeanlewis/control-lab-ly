# %% -*- coding: utf-8 -*-
"""
This module holds the base class for liquid handler tools.

Classes:
    LiquidHandler (ABC)
    Speed (dataclass)
"""
# Standard library imports
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
import numpy as np
from typing import Optional, Union
print(f"Import: OK <{__name__}>")

@dataclass
class Speed:
    """
    Speed dataclass represents a single aspirate-dispense speed pair
    
    ### Constructor
    Args:
        up (float): speed of upwards movement
        down (float): speed of downwards movement
    """
    
    up: float
    down: float

class LiquidHandler(ABC):
    """
    Abstract Base Class (ABC) for Liquid Handler objects (i.e. tools that transfer liquids).
    ABC cannot be instantiated, and must be subclassed with abstract methods implemented before use.
    
    ### Constructor
    Args:
        `verbose` (bool, optional): verbosity of class. Defaults to False.
    
    ### Attributes
    - `capacity` (float): maximum amount of liquid that can be held
    - `channel` (int): channel id
    - `connection_details` (dict): dictionary of connection details (e.g. COM port / IP address)
    - `device` (Callable): device object that communicates with physical tool
    - `flags` (dict[str, bool]): keywords paired with boolean flags
    - `reagent` (str): name of reagent held in liquid handler
    - `speed` (Speed): up and down speeds of liquid handler
    - `verbose` (bool): verbosity of class
    
    ### Properties
    - `offset` (np.ndarray): liquid handler offset
    - `volume` (float): volume held in liquid handler
    
    ### Methods
    #### Abstract
    - `aspirate`: aspirate desired volume of reagent
    - `blowout`: blowout liquid from tip
    - `dispense`: dispense desired volume of reagent
    - `pullback`: pullback liquid from tip
    - `_connect`: connection procedure for tool
    #### Public
    - `connect`: establish connection with device
    - `cycle`: cycle between aspirate and dispense
    - `disconnect`: disconnect from device
    - `empty`: empty the channel
    - `fill`: fill the channel
    - `isBusy`: checks and returns whether the device is busy
    - `isConnected`: checks and returns whether the device is connected
    - `resetFlags`: reset all flags to class attribute `_default_flags`
    - `rinse`: rinse the channel with aspirate and dispense cycles
    - `setFlag`: set flags by using keyword arguments
    - `shutdown`: shutdown procedure for tool
    """
    
    _default_flags: dict[str, bool] = {'busy': False, 'connected': False}
    def __init__(self, verbose:bool = False, **kwargs):
        """
        Instantiate the class

        Args:
            verbose (bool, optional): verbosity of class. Defaults to False.
        """
        self.capacity = 0
        self.channel = 0
        self.reagent = ''
        self.speed = Speed(0,0)
        self._volume = 0
        self._offset = (0,0,0)
        
        self.connection_details = {}
        self.device = None
        self.flags = self._default_flags.copy()
        self.verbose = verbose
        return

    def __del__(self):
        self.shutdown()
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
        Aspirate desired volume of reagent

        Args:
            volume (float): target volume
            speed (Optional[float], optional): speed to aspirate at. Defaults to None.
            wait (int, optional): time delay after aspirate. Defaults to 0.
            pause (bool, optional): whether to pause for user intervention. Defaults to False.
            reagent (Optional[str], optional): name of reagent. Defaults to None.
            channel (Optional[Union[int, tuple[int]]], optional): channel id. Defaults to None.

        Returns:
            bool: whether the action is successful
        """
    
    @abstractmethod
    def blowout(self, channel: Optional[Union[int, tuple[int]]] = None, **kwargs) -> bool:
        """
        Blowout liquid from tip

        Args:
            channel (Optional[Union[int, tuple[int]], optional): channel id. Defaults to None.
            
        Returns:
            bool: whether the action is successful
        """
        return False
    
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
        Dispense desired volume of reagent

        Args:
            volume (float): target volume
            speed (Optional[float], optional): speed to dispense at. Defaults to None.
            wait (int, optional): time delay after dispense. Defaults to 0.
            pause (bool, optional): whether to pause for user intervention. Defaults to False.
            blowout (bool, optional): whether perform blowout. Defaults to False.
            force_dispense (bool, optional): whether to dispense reagent regardless. Defaults to False.
            channel (Optional[Union[int, tuple[int]]], optional): channel id. Defaults to None.

        Returns:
            bool: whether the action is successful
        """

    @abstractmethod
    def pullback(self, channel: Optional[Union[int, tuple[int]]] = None, **kwargs) -> bool:
        """
        Pullback liquid from tip

        Args:
            channel (Optional[Union[int, tuple[int]]], optional): channel id. Defaults to None.
            
        Returns:
            bool: whether the action is successful
        """
        return False

    @abstractmethod
    def _connect(self):
        """Connection procedure for tool"""
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
    
    @property
    def volume(self) -> float:
        return self._volume
    @volume.setter
    def volume(self, value:float):
        self._volume = value
        return
    
    def connect(self):
        """Establish connection with device"""
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
        Cycle between aspirate and dispense

        Args:
            volume (float): target volume
            speed (Optional[float], optional): speed to aspirate and dispense at. Defaults to None.
            wait (int, optional): time delay after each action. Defaults to 0.
            cycles (int, optional): number of cycles. Defaults to 1.
            reagent (Optional[str], optional): name of reagent. Defaults to None.
            channel (Optional[Union[int, tuple[int]]], optional): channel id. Defaults to None.

        Returns:
            bool: whether the action is successful
        """
        success = []
        for _ in range(int(cycles)):
            ret1 = self.aspirate(volume=volume, speed=speed, wait=wait, pause=False, reagent=reagent, channel=channel)
            ret2 = self.dispense(volume=volume, speed=speed, wait=wait, pause=False, force_dispense=True, channel=channel)
            success.extend([ret1,ret2])
        return all(success)
    
    def disconnect(self):
        """Disconnect from device"""
        try:
            self.device.close()
        except Exception as e:
            if self.verbose:
                print(e)
        self.setFlag(connected=False)
        return
    
    def empty(self, 
        speed: Optional[float] = None, 
        wait: int = 0, 
        pause: bool = False, 
        channel: Optional[Union[int, tuple[int]]] = None,
        **kwargs
    ) -> bool:
        """
        Empty the channel

        Args:
            speed (Optional[float], optional): speed to empty. Defaults to None.
            wait (int, optional): wait time between steps in seconds. Defaults to 0.
            pause (bool, optional): whether to pause for user intervention. Defaults to False.
            channel (Optional[Union[int, tuple[int]]], optional): channel id. Defaults to None.
            
        Returns:
            bool: whether the action is successful
        """
        ret1 = self.dispense(volume=self.capacity, speed=speed, wait=wait, pause=pause, force_dispense=True, channel=channel)
        ret2 = self.blowout(channel=channel)
        return all([ret1,ret2])
    
    def fill(self, 
        speed: Optional[float] = None, 
        wait: int = 0, 
        pause: bool = False, 
        cycles: int = 0,
        reagent: Optional[str] = None, 
        channel: Optional[Union[int, tuple[int]]] = None,
        **kwargs
    ) -> bool:
        """
        Fill the channel

        Args:
            speed (Optional[float], optional): speed to aspirate and dispense at. Defaults to None.
            wait (int, optional): time delay after each action. Defaults to 0.
            pause (bool, optional): whether to pause for user intervention. Defaults to False.
            cycles (int, optional): number of cycles. Defaults to 0.
            reagent (Optional[str], optional): name of reagent. Defaults to None.
            channel (Optional[Union[int, tuple[int]]], optional): channel id. Defaults to None.
        
        Returns:
            bool: whether the action is successful
        """
        ret1 = self.cycle(volume=self.capacity, speed=speed, wait=wait, cycles=cycles, reagent=reagent, channel=channel)
        ret2 = self.aspirate(volume=self.capacity, speed=speed, wait=wait, pause=pause, reagent=reagent, channel=channel)
        ret3 = self.pullback(channel=channel)
        return all([ret1,ret2,ret3])
    
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
            if self.verbose:
                print(f"{self.__class__} is not connected. Details: {self.connection_details}")
        return self.flags.get('connected', False)

    def resetFlags(self):
        """Reset all flags to class attribute `_default_flags`"""
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
            speed (Optional[float], optional): speed to aspirate and dispense at. Defaults to None.
            wait (int, optional): time delay after each action. Defaults to 0.
            cycles (int, optional): number of cycles. Defaults to 1.
            channel (Optional[Union[int, tuple[int]]], optional): channel id. Defaults to None.

        Returns:
            bool: whether the action is successful
        """
        return self.cycle(volume=self.capacity, speed=speed, wait=wait, cycles=cycles, channel=channel)
    
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
        self.disconnect()
        self.resetFlags()
        return

    # Protected method(s)
    def _diagnostic(self):
        """Run diagnostic test"""
        self.pullback()
        return
