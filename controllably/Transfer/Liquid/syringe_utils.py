# %% -*- coding: utf-8 -*-
"""
This module holds the class for syringe assemblies.

Classes:
    SyringeAssembly (LiquidHandler)
"""
# Standard library imports
from __future__ import annotations
from functools import wraps
import time
from typing import Callable, Optional, Protocol, Union

# Local application imports
from ...misc import Helper
from .liquid_utils import LiquidHandler, Speed
from .syringe_lib import Syringe
print(f"Import: OK <{__name__}>")

class Pump(Protocol):
    def aspirate(self, *args, **kwargs):
        ...
    def blowout(self, *args, **kwargs):
        ...
    def connect(self, *args, **kwargs):
        ...
    def dispense(self, *args, **kwargs):
        ...
    def pullback(self, *args, **kwargs):
        ...

class SyringeAssembly(LiquidHandler):
    """
    SyringeAssembly provides methods for interfacing a pump with multiple syringes

    ### Constructor
    Args:
        `pump` (Pump): Pump object
        `capacities` (tuple[float]): capacities of syringes
        `channels` (tuple[int]): channel ids of syringes
        `offsets` (tuple[tuple[float]]): coordinate offsets of syringes
        `speed` (Speed, optional): default speeds of pump. Defaults to Speed(3000,3000).
    
    ### Attributes
    - `channels` (dict[int, Syringe]): 
    - `device` (Pump): Pump object
    - `speed` (Speed): default speeds of pump
    
    ### Properties
    - `last_action` (str): last performed action, either aspirate or dispense
    - `pump` (Pump): alias for `device`
    - `syringes` (dict[int, Syringe]): alias for `channels`
    
    ### Methods
    - `aspirate`: aspirate desired volume of reagent
    - `blowout`: blowout liquid from tip
    - `connect`: establish connection with device
    - `disconnect`: disconnect from device
    - `dispense`: dispense desired volume of reagent
    - `empty`: empty the channel
    - `fill`: fill the channel
    - `isBusy`: checks and returns whether the device is busy
    - `isConnected`: checks and returns whether the device is connected
    - `pullback`: pullback liquid from tip
    - `rinse`: rinse the channel with aspirate and dispense cycles
    - `updateChannel`: update data stored in Syringe dataclass
    """
    
    def __init__(self, 
        pump: Pump, 
        capacities: tuple[float], 
        channels: tuple[int],
        offsets: tuple[tuple[float]],
        speed: Speed = Speed(3000,3000),
        **kwargs
    ):
        """
        Instantiate the class

        Args:
            pump (Pump): Pump object
            capacities (tuple[float]): capacities of syringes
            channels (tuple[int]): channel ids of syringes
            offsets (tuple[tuple[float]]): coordinate offsets of syringes
            speed (Speed, optional): default speed of pump. Defaults to Speed(3000,3000).
        """
        super().__init__(**kwargs)
        self.device = pump
        self.channels = self._get_syringes(capacity=capacities, channel=channels, offset=offsets)
        self.speed = speed
        self._last_action = 'first'
        return
    
    # Properties
    @property
    def last_action(self) -> str:
        return self._last_action
    @last_action.setter
    def last_action(self, value:str):
        if value not in ('first', 'aspirate', 'dispense'):
            raise ValueError("Select one of: first, aspirate, dispense.")
        self._last_action = value
        return
    
    @property
    def pump(self) -> Pump:
        return self.device
    
    @property
    def syringes(self) -> dict[int, Syringe]:
        return self.channels
    
    # Decorators
    def _multi_channel(func:Callable) -> Callable:
        """
        Decorator to make function work with multiple channels

        Args:
            func (Callable): target method

        Returns:
            Callable: multi-channel method
        """
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            success = []
            channels = []
            
            channel = kwargs.pop('channel', None)
            if channel is None:
                channels = tuple(self.syringes.keys())
            elif type(channel) is int:
                channels = (channel,)
            else:
                channels = tuple(channel)
            
            for channel in channels:
                if channel not in self.syringes:
                    print(f"Channel {channel} not found.")
                    continue
                ret = func(self, channel=channel, *args, **kwargs)
                success.append(ret)
            return all(success)
        return wrapper
    
    # Public methods
    @_multi_channel
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
        syringe = self.syringes[channel]
        volume = min(volume, syringe.capacity - syringe.volume)
        if not volume:
            return False
        
        print(f"Syringe {channel}")
        print(f'Aspirating {volume} uL...')
        speed = abs(self.speed.up) if speed is None else abs(speed) # NOTE: used to be -ve
        t_aspirate = (volume / speed)
        try:
            t_aspirate *= eval(f"syringe.calibration.{self._last_action}.aspirate")
        except AttributeError:
            pass
        print(t_aspirate)
        self.pump.aspirate(volume=volume, speed=speed, pump_time=t_aspirate, channel=channel)
        self.pullback(channel=channel)
        self.last_action = 'aspirate'
        
        time.sleep(wait)
        syringe.volume += volume
        if reagent is not None:
            syringe.reagent = reagent
        if pause:
            input("Press 'Enter' to proceed.")
        return True

    def blowout(self, channel: Optional[Union[int, tuple[int]]] = None, **kwargs) -> bool:
        """
        Blowout liquid from tip

        Args:
            channel (Optional[Union[int, tuple[int]], optional): channel id. Defaults to None.
            
        Returns:
            bool: whether the action is successful
        """
        return self.pump.blowout(channel=channel)
    
    def connect(self):
        """Establish connection with device"""
        return self.pump.connect()
    
    def disconnect(self):
        return self.pump.disconnect()
    
    @_multi_channel
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
        syringe = self.syringes[channel]
        if not force_dispense and volume > syringe.volume:
            print('Required dispense volume is greater than volume in tip')
            return False
        volume = min(volume, syringe.volume)
        
        print(f"Syringe {channel}")
        print(f'Dispensing {volume} uL...')
        speed = abs(self.speed.down) if speed is None else abs(speed)
        t_dispense = (volume / speed)
        try:
            t_dispense *= eval(f"syringe.calibration.{self._last_action}.dispense")
        except AttributeError:
            pass
        print(t_dispense)
        self.pump.dispense(volume=volume, speed=speed, pump_time=t_dispense, channel=channel)
        self.pullback(channel=channel)
        self.last_action = 'dispense'
        
        time.sleep(wait)
        syringe.volume = max(syringe.volume - volume, 0)
        if syringe.volume == 0 and blowout:
            self.blowout(channel=channel)
        if pause:
            input("Press 'Enter' to proceed.")
        return True
 
    @_multi_channel
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
        syringe = self.syringes[channel]
        _capacity = self.capacity
        self.capacity = syringe.capacity
        success = super().empty(speed=speed, wait=wait, pause=pause, channel=channel)
        self.capacity = _capacity
        return success

    @_multi_channel
    def fill(self, 
        speed: Optional[float] = None, 
        wait: int = 0, 
        pause: bool = False, 
        cycles: int = 1,
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
            cycles (int, optional): number of cycles. Defaults to 1.
            reagent (Optional[str], optional): name of reagent. Defaults to None.
            channel (Optional[Union[int, tuple[int]]], optional): channel id. Defaults to None.
        
        Returns:
            bool: whether the action is successful
        """
        syringe = self.syringes[channel]
        _capacity = self.capacity
        self.capacity = syringe.capacity
        success = super().fill(speed=speed, wait=wait, pause=pause, cycles=cycles, reagent=reagent, channel=channel)
        self.capacity = _capacity
        return success

    def isBusy(self):
        """
        Checks and returns whether the pump is busy
        
        Returns:
            bool: whether the device is busy
        """
        return self.pump.isBusy()
    
    def isConnected(self):
        """
        Checks and returns whether the pump is connected

        Returns:
            bool: whether the device is connected
        """
        return self.pump.isConnected()

    @_multi_channel
    def pullback(self, channel:Optional[Union[int, tuple[int]]] = None,):
        """
        Pullback liquid from tip

        Args:
            channel (Optional[Union[int, tuple[int]]], optional): channel id. Defaults to None.
            
        Returns:
            bool: whether the action is successful
        """
        syringe = self.syringes[channel]
        return self.pump.pullback(pump_time=syringe.pullback_time, channel=channel)
    
    @_multi_channel
    def rinse(self, 
        speed: Optional[float] = None, 
        wait: int = 0, 
        cycles: int = 1, 
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
        syringe = self.syringes[channel]
        _capacity = self.capacity
        self.capacity = syringe.capacity
        success = super().rinse(speed=speed, wait=wait, cycles=cycles, channel=channel)
        self.capacity = _capacity
        return success
    
    def updateChannel(self, channel:int, **kwargs):
        """
        Update data stored in Syringe dataclass

        Args:
            channel (int): channel to update
        
        Kwargs:
            key, value: (attribute name, value) pairs
        """
        return self.syringes[channel].update(**kwargs)

    # Protected method(s)
    def _connect(self, *args, **kwargs):
        """Connection procedure for pump"""
        return self.pump.connect()
    
    @staticmethod
    def _get_syringes(**kwargs) -> dict[int, Syringe]:
        """
        Generate Syringe dataclass objects from parameters

        Returns:
            dict[int, Syringe]: dictionary of {channel id, `Syringe` object}
        """
        properties = Helper.zip_inputs(primary_keyword='channel', **kwargs)
        print(properties)
        return {key: Syringe(**value) for key,value in properties.items()}
