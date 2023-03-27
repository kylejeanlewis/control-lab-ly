# %% -*- coding: utf-8 -*-
"""
Adapted from @jaycecheng spinutils

Created: Tue 2022/11/01 17:13:35
@author: Chang Jie

Notes / actionables:
-
"""
# Standard library imports
from __future__ import annotations
from functools import wraps
import time
from typing import Callable, Optional, Protocol, Union

# Third party imports

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
    SyringeAssembly consisting of a pump and syringe(s)

    Args:
        port (str): com port address
        capacities (list, optional): list of syringe capacities. Defaults to [].
        channels (list, optional): list of syringe channels. Defaults to [].
        offsets (list, optional): list of syringe offsets. Defaults to [].
    
    Kwargs:
        verbose (bool, optional): whether to print output. Defaults to False.
    """
    def __init__(
        self, 
        pump: Pump, 
        capacities: tuple[float], 
        channels: tuple[int],
        offsets: tuple[tuple[float]],
        speed: Speed = Speed(3000,3000),
        **kwargs
    ):
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
    def _multi_channel(func:Callable):
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
        Aspirate desired volume of reagent into channel

        Args:
            volume (int, or float): volume to be aspirated
            speed (int, optional): speed to aspirate. Defaults to None.
            wait (int, optional): wait time between steps in seconds. Defaults to 0.
            reagent (str, optional): name of reagent. Defaults to ''.
            pause (bool, optional): whether to pause for intervention / operator input. Defaults to False.
            channel (int, optional): channel to aspirate. Defaults to None.
        
        Raises:
            Exception: Select a valid key
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
            channel (int, optional): channel to blowout. Defaults to None.
        """
        return self.pump.blowout(channel=channel)
    
    def connect(self):
        """
        Reconnect to device using existing port and baudrate
        
        Returns:
            serial.Serial: serial connection to machine control unit if connection is successful, else None
        """
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
        Aspirate desired volume of reagent into channel

        Args:
            volume (int, or float): volume to be dispensed
            speed (int, optional): speed to dispense. Defaults to None.
            wait (int, optional): wait time between steps in seconds. Defaults to 0.
            force_dispense (bool, optional): whether to continue dispensing even if insufficient volume in channel. Defaults to False.
            pause (bool, optional): whether to pause for intervention / operator input. Defaults to False.
            channel (int, optional): channel to dispense. Defaults to None.
        
        Raises:
            Exception: Select a valid key
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
        Empty multiple channels

        Args:
            speed (int, optional): speed to empty. Defaults to None.
            wait (int, optional): wait time between steps in seconds. Defaults to 0.
            pause (bool, optional): whether to pause for intervention / operator input. Defaults to False.
            channel (list, optional): channel to empty. Defaults to None.
        
        Raises:
            Exception: Select a valid key
        
        Returns:
            dict: dictionary of (channel, return value)
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
        cycles: int = 3,
        reagent: Optional[str] = None, 
        channel: Optional[Union[int, tuple[int]]] = None,
        **kwargs
    ) -> bool:
        """
        Fill multiple channels

        Args:
            speed (int, optional): speed to fill. Defaults to None.
            wait (int, optional): wait time between steps in seconds. Defaults to 0.
            reagents (list, optional): name of reagent. Defaults to [''].
            pause (bool, optional): whether to pause for intervention / operator input. Defaults to False.
            pre_wet (bool, optional): whether to pre-wet the channel. Defaults to True.
            channel (list, optional): channel to fill. Defaults to [].
        
        Raises:
            Exception: Select a valid key
        
        Returns:
            dict: dictionary of (channel, return value)
        """
        syringe = self.syringes[channel]
        _capacity = self.capacity
        self.capacity = syringe.capacity
        success = super().fill(speed=speed, wait=wait, pause=pause, cycles=cycles, reagent=reagent, channel=channel)
        self.capacity = _capacity
        return success

    def isBusy(self):
        """
        Checks whether the pump is busy
        
        Returns:
            bool: whether the pump is busy
        """
        return self.pump.isBusy()
    
    def isConnected(self):
        """
        Check whether pump is connected

        Returns:
            bool: whether pump is connected
        """
        return self.pump.isConnected()

    @_multi_channel
    def pullback(self, channel:Optional[Union[int, tuple[int]]] = None,): # FIXME
        """
        Pullback liquid from tip for multiple channels

        Raises:
            Exception: Select a valid key
        
        Args:
            channel (int, optional): channel to pullback
        """
        syringe = self.syringes[channel]
        return self.pump.pullback(speed=300, pump_time=syringe.pullback_time, channel=channel)
    
    @_multi_channel
    def rinse(self, 
        speed: Optional[float] = None, 
        wait: int = 0, 
        cycles: int = 3, 
        channel: Optional[Union[int, tuple[int]]] = None,
        **kwargs
    ) -> bool:
        """
        Rinse multiple channels

        Args:
            volume (int, or float): volume to be rinsed
            speed (int, optional): speed to cycle. Defaults to None.
            wait (int, optional): wait time between steps in seconds. Defaults to 0.
            reagent (list, optional): name of reagent. Defaults to [''].
            cycles (int, optional): number of cycles to perform. Defaults to 3.
            channel (list, optional): channel to cycle. Defaults to [].

        Raises:
            Exception: Select a valid key

        Returns:
            dict: dictionary of (channel, return value)
        """
        syringe = self.syringes[channel]
        _capacity = self.capacity
        self.capacity = syringe.capacity
        success = super().rinse(speed=speed, wait=wait, cycles=cycles, channel=channel)
        self.capacity = _capacity
        return success
    
    def updateChannel(self, channel:int, **kwargs):
        """
        Update the desired channel attribute

        Args:
            field (str): name of attribute
            value (any): new value of attribute
            channel (int): channel to update
        """
        return self.syringes[channel].update(**kwargs)

    # Protected method(s)
    def _connect(self, *args, **kwargs):
        return self.pump.connect()
    
    @staticmethod
    def _get_syringes(**kwargs) -> dict[int, Syringe]:
        properties = Helper.zip_inputs(primary_keyword='channel', **kwargs)
        return {key: Syringe(**value) for key,value in properties.items()}
