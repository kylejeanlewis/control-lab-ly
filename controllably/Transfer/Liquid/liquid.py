# -*- coding: utf-8 -*-
"""
This module contains the LiquidHandler class.

## Classes:
    `LiquidHandler`: Liquid handler base class
    
<i>Documentation last updated: 2025-02-22</i>
"""
# Standard library imports
from __future__ import annotations
from copy import deepcopy
import logging
import time
from types import SimpleNamespace

# Local application imports
from ...core import factory
from ...core.device import Device, StreamingDevice

# Configure logging
from controllably import CustomLevelFilter
logger = logging.getLogger(__name__)

class LiquidHandler:
    """ 
    Liquid handler base class
    
    ### Constructor:
        `verbose` (bool, optional): verbosity of class. Defaults to False
        
    ### Attributes and properties:
        `device`: Device object
        `flags`: Flags for the class
        `speed_in`: Speed for aspiration
        `speed_out`: Speed for dispense
        `reagent`: Name of reagent
        `offset`: Offset for liquid handling
        `connection_details`: Connection details for the device
        `is_busy`: Whether the device is busy
        `is_connected`: Whether the device is connected
        `verbose`: Verbosity of class
        `capacity`: Capacity of liquid handler
        `channel`: Current channel of liquid handler
        `volume`: Current volume of liquid in the channel
        `volume_resolution`: Volume resolution of liquid handler
        
    ### Methods:
        `connect`: Connect to the device
        `disconnect`: Disconnect from the device
        `resetFlags`: Reset all flags to to default
        `shutdown`: Shutdown procedure for tool
        `aspirate`: Aspirate desired volume of reagent
        `blowout`: Blowout liquid from tip
        `dispense`: Dispense desired volume of reagent
        `pullback`: Pullback liquid from tip
        `cycle`: Cycle between aspirate and dispense
        `empty`: Empty the channel
        `fill`: Fill the channel
        `rinse`: Rinse the channel with aspirate and dispense cycles
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
        self.speed_in = 0
        self.speed_out = 0
        self._capacity = 0
        self._volume = 0
        self.reagent = ''
        
        self._channel = 0
        self.offset = (0,0,0)
        
        self._volume_resolution = 1
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
    
    @property
    def capacity(self) -> float:
        """Capacity of liquid handler"""
        return self._capacity
    @capacity.setter
    def capacity(self, value:float):
        self._capacity = value
        return
    
    @property
    def channel(self) -> float:
        """Current channel of liquid handler"""
        return self._channel
    @channel.setter
    def channel(self, value:float):
        self._channel = value
        return
    
    @property
    def volume(self) -> float:
        """Current volume of liquid in the channel"""
        return self._volume
    @volume.setter
    def volume(self, value:float):
        self._volume = value
        return
    
    @property
    def volume_resolution(self) -> float:
        """Volume resolution of liquid handler"""
        return self._volume_resolution
    @volume_resolution.setter
    def volume_resolution(self, value:float):
        self._volume_resolution = value
        return
    
    def connect(self):
        """Connect to the device"""
        if not self.device.is_connected:
            self.device.connect()
        return
    
    def disconnect(self):
        """Disconnect from the device"""
        if self.device.is_connected:
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
    
    # Liquid handling methods
    def aspirate(self, 
        volume: float, 
        speed: float|None = None, 
        reagent: str|None = None,
        *,
        pullback: bool = False,
        delay: int = 0, 
        pause: bool = False, 
        ignore: bool = False,
        **kwargs
    ) -> bool:
        """
        Aspirate desired volume of reagent

        Args:
            volume (float): target volume
            speed (float|None, optional): speed to aspirate at. Defaults to None.
            reagent (str|None, optional): name of reagent. Defaults to None.
            pullback (bool, optional): whether to pullback after aspirate. Defaults to False.
            delay (int, optional): time delay after aspirate. Defaults to 0.
            pause (bool, optional): whether to pause for user intervention. Defaults to False.
            ignore (bool, optional): whether to aspirate reagent regardless. Defaults to False.

        Returns:
            bool: whether the action is successful
        """
        if (reagent and self.reagent) and reagent != self.reagent:
            self._logger.warning(f"Reagent {reagent} does not match current reagent {self.reagent}.")
            return False
        if volume > (self.capacity - self.volume) and ignore:
            volume = self.capacity - self.volume
            self._logger.warning("Volume exceeds capacity. Aspirating up to capacity.")
        elif volume > (self.capacity - self.volume):
            self._logger.warning("Volume exceeds capacity.")
            return False
        if volume < self.volume_resolution and not ignore:
            self._logger.warning("Volume is too small. Ensure volume is greater than resolution.")
            return False
        volume = round(volume/self.volume_resolution)*self.volume_resolution
        speed = speed or self.speed_in
        
        # Replace with actual aspirate implementation
        ...
        
        # Update values
        time.sleep(delay)
        self.volume = min(self.volume + volume, self.capacity)
        if pullback and self.volume < self.capacity:
            self.pullback(**kwargs)
        if pause:
            input("Press 'Enter' to proceed.")
        raise NotImplementedError
    
    def blowout(self, **kwargs) -> bool:
        """
        Blowout liquid from tip
            
        Returns:
            bool: whether the action is successful
        """
        self._logger.warning("Blowout not implemented.")
        return True
    
    def dispense(self, 
        volume: float, 
        speed: float|None = None, 
        *,
        blowout: bool = False,
        delay: int = 0, 
        pause: bool = False, 
        ignore: bool = False,
        **kwargs
    ) -> bool:
        """
        Dispense desired volume of reagent

        Args:
            volume (float): target volume
            speed (float|None, optional): speed to dispense at. Defaults to None.
            blowout (bool, optional): whether perform blowout. Defaults to False.
            delay (int, optional): time delay after dispense. Defaults to 0.
            pause (bool, optional): whether to pause for user intervention. Defaults to False.
            ignore (bool, optional): whether to dispense reagent regardless. Defaults to False.

        Returns:
            bool: whether the action is successful
        """
        if volume > self.volume and ignore:
            volume = self.volume
            self._logger.warning("Volume exceeds available volume. Dispensing up to available volume.")
        elif volume > self.volume:
            self._logger.warning("Volume exceeds available volume.")
            return False
        if volume < self.volume_resolution and not ignore:
            self._logger.warning("Volume is too small. Ensure volume is greater than resolution.")
            return False
        volume = round(volume/self.volume_resolution)*self.volume_resolution
        speed = speed or self.speed_out
        
        # Replace with actual dispense implementation
        ...
        
        # Update values
        time.sleep(delay)
        self.volume = max(self.volume - volume, 0)
        if blowout and self.volume == 0:
            self.blowout(**kwargs)
        if pause:
            input("Press 'Enter' to proceed.")
        raise NotImplementedError

    def pullback(self, **kwargs) -> bool:
        """
        Pullback liquid from tip
            
        Returns:
            bool: whether the action is successful
        """
        self._logger.warning("Pullback not implemented.")
        return True
    
    def cycle(self, 
        volume: float, 
        speed: float|None = None, 
        reagent: str|None = None,
        cycles: int = 1,
        *,
        delay: int = 0,
        **kwargs
    ) -> bool:
        """
        Cycle between aspirate and dispense

        Args:
            volume (float): target volume
            speed (float|None, optional): speed to aspirate and dispense at. Defaults to None.
            reagent (str|None, optional): name of reagent. Defaults to None.
            cycles (int, optional): number of cycles. Defaults to 1.
            delay (int, optional): time delay after each action. Defaults to 0.

        Returns:
            bool: whether the action is successful
        """
        assert cycles > 0, "Ensure cycles is a positive integer"
        success = []
        for _ in range(int(cycles)):
            ret1 = self.aspirate(volume, speed, reagent, delay=delay, pause=False, **kwargs)
            ret2 = self.dispense(volume, speed, delay=delay, pause=False, ignore=True, **kwargs)
            success.extend([ret1,ret2])
        return all(success)
    
    def empty(self, 
        speed: float|None = None, 
        *,
        blowout: bool = False,
        delay: int = 0, 
        pause: bool = False, 
        **kwargs
    ) -> bool:
        """
        Empty the channel

        Args:
            speed (float|None, optional): speed to empty. Defaults to None.
            blowout (bool, optional): whether to perform blowout. Defaults to False.
            delay (int, optional): delay time between steps in seconds. Defaults to 0.
            pause (bool, optional): whether to pause for user intervention. Defaults to False.
            
        Returns:
            bool: whether the action is successful
        """
        return self.dispense(self.capacity, speed, blowout=blowout, delay=delay, pause=pause, ignore=True, **kwargs)
    
    def fill(self, 
        speed: float|None = None, 
        reagent: str|None = None,
        *,
        pullback: bool = False,
        cycles: int = 0,
        delay: int = 0, 
        pause: bool = False, 
        **kwargs
    ) -> bool:
        """
        Fill the channel

        Args:
            speed (float|None, optional): speed to aspirate and dispense at. Defaults to None.
            reagent (str|None, optional): name of reagent. Defaults to None.
            pullback (bool, optional): whether to pullback after aspirate. Defaults to False.
            cycles (int, optional): number of cycles before filling. Defaults to 0.
            delay (int, optional): time delay after each action. Defaults to 0.
            pause (bool, optional): whether to pause for user intervention. Defaults to False.
        
        Returns:
            bool: whether the action is successful
        """
        ret1 = self.rinse(speed, reagent, cycles, delay=delay, **kwargs) if cycles > 0 else True
        ret2 = self.aspirate(self.capacity, speed, reagent, pullback=pullback, delay=delay, pause=pause, ignore=True, **kwargs)
        return all([ret1,ret2])

    def rinse(self, 
        speed: float|None = None,
        reagent: str|None = None,
        cycles: int = 3,
        *,
        delay: int = 0, 
        **kwargs
    ) -> bool:
        """
        Rinse the channel with aspirate and dispense cycles
        
        Args:
            speed (float|None, optional): speed to aspirate and dispense at. Defaults to None.
            reagent (str|None, optional): name of reagent. Defaults to None.
            cycles (int, optional): number of cycles. Defaults to 1.
            delay (int, optional): time delay after each action. Defaults to 0.

        Returns:
            bool: whether the action is successful
        """
        return self.cycle(volume=self.capacity, speed=speed, reagent=reagent, cycles=cycles, delay=delay, **kwargs)
