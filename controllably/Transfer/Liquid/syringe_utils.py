# %% -*- coding: utf-8 -*-
"""
Adapted from @jaycecheng spinutils

Created: Tue 2022/11/01 17:13:35
@author: Chang Jie

Notes / actionables:
-
"""
# Standard library imports
import time

# Third party imports
import serial # pip install pyserial

# Local application imports
from ...misc import Helper
from .liquid_utils import LiquidHandler
from .Pumps import Peristaltic, C3000
print(f"Import: OK <{__name__}>")

CALIBRATION_ASPIRATE = 27
CALIBRATION_DISPENSE = 23.5
DEFAULT_SPEED = 3000 # speed of pump
PULLBACK_TIME = 2 # amount of time to pullback [s]

class Syringe(LiquidHandler):
    """
    Syringe class

    Args:
        capacity (int, or float): capacity of syringe
        channel (int): channel index
        offset (tuple, optional): coordinates offset. Defaults to None.
        pullback_time (int, optional): duration of pullback. Defaults to 2.
        
    Kwargs:
        verbose (bool, optional): whether to print output. Defaults to False.
    """
    def __init__(
        self, 
        capacity, 
        channel, 
        offset=None, 
        pullback_time=PULLBACK_TIME, 
        default_speed=DEFAULT_SPEED,
        calibration_aspirate=CALIBRATION_ASPIRATE,
        calibration_dispense=CALIBRATION_DISPENSE, 
        **kwargs
    ):
        super().__init__(**kwargs)
        self.capacity = capacity
        self.channel = channel
        if offset is None:
            offset = (0,0,0)
        self.offset = tuple(offset)
        
        self.pump = None
        
        self.calibration_aspirate = calibration_aspirate
        self.calibration_dispense = calibration_dispense
        self._previous_action = 'first'
        self._pullback_time = pullback_time
        self._speed_in = default_speed
        self._speed_out = default_speed
        pass
    
    def aspirate(self, volume, speed=None, wait=0, reagent='', pause=False, channel=None):
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
        if speed is None:
            speed = self.speed['in']
        self.pump.setFlag('busy', True)
        volume = min(volume, self.capacity - self.volume)

        if volume != 0:
            speed = -abs(speed)
            t_aspirate = (volume / speed) * self.calibration_aspirate
            if self._previous_action == 'first':
                t_aspirate *= 1.3
            elif self._previous_action == 'aspirate':
                t_aspirate *= 1
            elif self._previous_action == 'dispense':
                t_aspirate *= 1.6
            print(t_aspirate)
            t_pullback = (50 / speed) * self.calibration_aspirate
            print(f'Aspirate {volume} uL')
            self.pump.push(speed=speed, push_time=t_aspirate, pullback_time=t_pullback, channel=self.channel)
            
            # Update values
            self._previous_action = 'aspirate'
            self.volume += volume
            if len(reagent) and len(self.reagent) == 0:
                self.reagent = reagent
        
        time.sleep(wait)
        self.pump.setFlag('busy', False)
        if pause:
            input("Press 'Enter to proceed.")
        return
    
    def dispense(self, volume, speed=None, wait=0, force_dispense=False, pause=False, channel=None):
        """
        Aspirate desired volume of reagent into channel

        Args:
            volume (int, or float): volume to be dispensed
            speed (int, optional): speed to dispense. Defaults to None.
            wait (int, optional): wait time between steps in seconds. Defaults to 0.
            force_dispense (bool, optional): whether to continue dispensing even if insufficient volume in channel. Defaults to False.
            pause (bool, optional): whether to pause for intervention / operator input. Defaults to False.
            pump (Pump, optional): pump object. Defaults to None.
            channel (int, optional): channel to dispense. Defaults to None.
            
        Raises:
            Exception: Required dispense volume is greater than volume in tip
        """
        if speed is None:
            speed = self.speed['out']
        self.pump.setFlag('busy', True)
        if force_dispense:
            volume = min(volume, self.volume)
        elif volume > self.volume:
            raise Exception('Required dispense volume is greater than volume in tip')
        
        if force_dispense or volume <= self.volume:
            speed = abs(speed)
            t_dispense = (volume / speed) * self.calibration_dispense
            if self._previous_action == 'first':
                t_dispense *= 1
            elif self._previous_action == 'aspirate':
                t_dispense *= 1.55
            elif self._previous_action == 'dispense':
                t_dispense *= 1
            print(t_dispense)
            t_pullback = (50 / speed) * self.calibration_dispense
            self.pump.push(speed=speed, push_time=t_dispense, pullback_time=t_pullback, channel=self.channel)
            
            # Update values
            self._previous_action = 'dispense'
            self.volume = max(self.volume - volume, 0)
        
        time.sleep(wait)
        self.pump.setFlag('busy', False)
        if pause:
            input("Press 'Enter to proceed.")
        return
    
    def pullback(self, channel=None):
        """
        Pullback liquid from tip

        Args:
            channel (int, optional): channel to pullback. Defaults to None.
        """
        self.pump.setFlag('busy', True)
        self.pump.push(speed=-300, push_time=0, pullback_time=self._pullback_time, channel=self.channel)
        self.pump.setFlag('busy', False)
        return
    
    def update(self, field:str, value):
        """
        Update the desired attribute

        Args:
            field (str): name of attribute
            value (any): new value of attribute
        """
        attrs = ['reagent', 'volume', '_previous_action']
        if field not in attrs:
            print(f"Select a field from: {', '.join(attrs)}")
        else:
            setattr(self, field, value)
        return


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
    def __init__(self, port:str, capacities=[], channels=[], offsets=[], **kwargs):
        super().__init__(**kwargs)
        self.pump = Peristaltic(port)
        properties = Helper.zip_inputs('channel', capacity=capacities, channel=channels, offset=offsets)
        self.channels = {key: Syringe(**value) for key,value in properties.items()}
        for syringe in self.channels.values():
            syringe.pump = self.pump
        return
    
    def aspirate(self, volume, speed=None, wait=0, reagent='', pause=False, channel=None):
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
        if channel not in self.channels.keys():
            raise Exception(f"Select a valid key from: {', '.join(self.channels.keys())}")
        return self.channels[channel].aspirate(volume=volume, speed=speed, wait=wait, reagent=reagent, pause=pause)

    def connect(self):
        """
        Reconnect to device using existing port and baudrate
        
        Returns:
            serial.Serial: serial connection to machine control unit if connection is successful, else None
        """
        return self.pump.connect()
    
    def dispense(self, volume, speed=None, wait=0, force_dispense=False, pause=False, channel=None):
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
        if channel not in self.channels.keys():
            raise Exception(f"Select a valid key from: {', '.join(self.channels.keys())}")
        return self.channels[channel].dispense(volume=volume, speed=speed, wait=wait, force_dispense=force_dispense, pause=pause)
 
    def empty(self, speed=None, wait=0, pause=False, channel:list=[]):
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
        if len(channel) == 0: # all channels instead
            channel = list(self.channels.keys())
        
        return_values = {}
        for chn in channel:
            if chn not in self.channels.keys():
                raise Exception(f"Select a valid key from: {', '.join(self.channels.keys())}")
            return_values[chn] = self.channels[channel].empty(speed=speed, wait=wait, pause=pause)
        return return_values

    def fill(self, speed=None, wait=0, reagents='', pause=False, pre_wet=True, channel:list=[]):
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
        if len(channel) == 0: # all channels instead
            channel = list(self.channels.keys())
        
        return_values = {}
        for chn in channel:
            if chn not in self.channels.keys():
                raise Exception(f"Select a valid key from: {', '.join(self.channels.keys())}")
            return_values[chn] = self.channels[channel].fill(speed=speed, wait=wait, reagent=reagents, pause=pause, pre_wet=pre_wet)
        return return_values

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

    def pullback(self, channel:list=[]):
        """
        Pullback liquid from tip for multiple channels

        Raises:
            Exception: Select a valid key
        
        Args:
            channel (int, optional): channel to pullback
        """
        if len(channel) == 0: # all channels instead
            channel = list(self.channels.keys())
        for chn in channel:
            if chn not in self.channels.keys():
                raise Exception(f"Select a valid key from: {', '.join(self.channels.keys())}")
            self.channels[chn].pullback()
        return
    
    def rinseMany(self, volume, speed=None, wait=0, reagents='', cycles=3, channel:list=[]):
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
        if len(channel) == 0: # all channels instead
            channel = list(self.channels.keys())
        
        return_values = {}
        for chn in channel:
            if chn not in self.channels.keys():
                raise Exception(f"Select a valid key from: {', '.join(self.channels.keys())}")
            return_values[chn] = self.channels[channel].rinse(volume=volume, speed=speed, wait=wait, reagent=reagents, cycles=cycles)
        return return_values
    
    def update(self, field, value, channel):
        """
        Update the desired channel attribute

        Args:
            field (str): name of attribute
            value (any): new value of attribute
            channel (int): channel to update
        """
        return self.channels[channel].update(field, value)
