# -*- coding: utf-8 -*-
"""
This module holds the class for controlling LED arrays on serial devices.

## Classes:
    `LED`: Dataclass to represent a single LED unit
    `LEDArray`: Class to control an array of LEDs connected to a controller

<i>Documentation last updated: 2024-11-13</i>
"""
# Standard library imports
from __future__ import annotations
from dataclasses import dataclass, field
import logging
from threading import Thread
import time
from types import SimpleNamespace
from typing import final

# Local application imports
from .. import Maker

logger = logging.getLogger("controllably.Make")
logger.debug(f"Import: OK <{__name__}>")

@dataclass
class LED:
    """
    LED dataclass represents a single LED unit.
    Do not use this class directly.
    Use `LEDArray` instead, which provides serial connection to device.

    ### Constructor
        `channel` (int): channel id
    
    ### Attributes and properties
        `channel` (int): channel id
        `duration` (int): duration in seconds
        `end_time` (float): end time of illumination
        `power` (int): power level of LED (0~255)
        `update_power` (bool): whether to update the LED's power
    
    ### Methods
        `setPower`: set power and duration for illumination
    """
    
    channel: int
    
    update_power: bool = field(default=False, init=False)
    _duration: int = field(default=0, init=False)
    _end_time: float = field(default=time.perf_counter(), init=False)
    _power: int = field(default=0, init=False)
    
    # Properties
    @property
    def duration(self) -> int:
        """Duration in seconds"""
        return self._duration
    
    @property
    def end_time(self) -> float:
        """End time of illumination"""
        return self._end_time
    @end_time.setter
    def end_time(self, value:float):
        assert isinstance(value, float), 'Please input a float value.'
        assert value >= time.perf_counter(), 'End time must be greater than current time.'
        self._end_time = value
        return
    
    @property
    def power(self) -> int:
        """Power level of LED (0~255)"""
        return self._power
    @power.setter
    def power(self, value:int):
        assert isinstance(value,int) and (0 <= value <= 255), 'Please input an integer between 0 and 255.'
        self._power = value
        self.update_power = True
        return
    
    def setPower(self, value:int, duration:int = 0):
        """
        Set power and duration for illumination

        Args:
            value (int): power level between 0 and 255
            duration (int, optional): duration in seconds. Defaults to 0.
        """
        self.power = value
        if duration:
            logger.info(f"{duration} seconds for LED {self.channel}")
        self._duration = duration
        return
    

@final
class LEDArray(Maker):
    """
    LEDArray provides an interface to control an array of LEDs connected together to a controller

    ### Constructor
        `port` (str): serial port address
        `channels` (list, optional): list of channels. Defaults to (0,).
        `baudrate` (int, optional): baudrate for the device. Defaults to 9600.
        `verbose` (bool, optional): verbosity of class. Defaults to False.
    
    ### Attributes
        `channels` (dict[int, LED]): dictionary of {channel id, `LED` objects}
    
    ### Methods
    - `execute`: alias for `setPower()`
    - `getPower`: get power level(s) of channel(s)
    - `getTimedChannels`: get channels that are still timed
    - `isBusy`: checks and returns whether the LED array is still busy
    - `setPower`: set the power value(s) for channel(s)
    - `shutdown`: shutdown procedure for tool
    - `startTiming`: start counting down time left with LEDs on
    - `turnOff`: turn of specified LED channels
    """
    
    _default_flags: SimpleNamespace[str,bool] = SimpleNamespace(busy=False, execute_now=False, timing_loop=False)
    def __init__(self, 
        port:str, 
        channels:tuple[int] = (0,), 
        *,
        baudrate: int = 9600,
        verbose: bool = False,
        **kwargs
    ):
        """
        Initialize LEDArary class

        Args:
            port (str): COM port address
            channels (list, optional): list of channels. Defaults to (0,).
            baudrate (int, optional): baudrate for the device. Defaults to 9600.
            verbose (bool, optional): verbosity of class. Defaults to False.
        """
        super().__init__(port=port, baudrate=baudrate, verbose=verbose, **kwargs)
        self.channels = {chn: LED(chn) for chn in channels}
        self._threads = {}
        self._timed_channels = []
        
        self.connect()
        return
    
    def getPower(self, channel:int|None = None) -> list[int]:
        """
        Get power level(s) of channel(s)

        Args:
            channel (int|None, optional): channel id. Defaults to None.

        Returns:
            list[int]: list of power level(s)
        """
        power = []
        if channel is None:
            power = [chn.power for chn in self.channels.values()]
        else:
            power = [self.channels[channel].power]
        return power
    
    def getTimedChannels(self) -> list[int]:
        """
        Get channels that are still timed

        Returns:
            list[int]: list of channels that are still timed
        """
        now = time.perf_counter()
        self._timed_channels = [chn.channel for chn in self.channels.values() if (chn.end_time>now and chn.duration)]
        return self._timed_channels
    
    def setPower(self, value:int, duration:int = 0, channel:int|None = None):
        """
        Set the power value(s) for channel(s)

        Args:
            value (int): 8-bit integer for LED power (i.e. 0~255)
            duration (int, optional): duration in seconds. Defaults to 0.
            channel (int|None, optional): channel id. Defaults to None.
        """
        if channel is None:
            for chn in self.channels.values():
                chn.setPower(value, duration)
        elif type(channel) is int and channel in self.channels:
            self.channels[channel].setPower(value, duration)
        _ = self.startTiming() if duration else self._update_power()
        return
    
    def startTiming(self):
        """Start counting down time left with LEDs on"""
        self._logger.info("Timing...")
        if not self.flags.timing_loop:
            if 'timing_loop'in self._threads and self._threads['timing_loop'].is_alive():
                return
            thread = Thread(target=self._loop_timer)
            thread.start()
            self._threads['timing_loop'] = thread
        return
    
    def turnOff(self, channel:int|None = None):
        """
        Turn off the LED corresponding to the channel(s)

        Args:
            channel (int|None, optional): channel id. Defaults to None.
        """
        self._logger.info(f"Turning off LED {channel}")
        self.setPower(0, channel=channel)
        return
    
    # Overwritten method(s)
    @property
    def is_busy(self) -> bool:
        """
        Checks and returns whether the LED array is still busy

        Returns:
            bool: whether the LED array is still busy
        """
        busy = bool(len(self.getTimedChannels()))
        busy = busy | any([chn.duration for chn in self.channels.values()])
        self.flags.busy = busy
        return busy
    
    def execute(self, value:int, duration:int = 0, channel:int|None = None, *args, **kwargs):
        """
        Alias for `setPower()`
        
        Set the power value(s) for channel(s)

        Args:
            value (int): 8-bit integer for LED power (i.e. 0~255)
            duration (int, optional): duration in seconds. Defaults to 0.
            channel (int|None, optional): channel id. Defaults to None.
        """
        return self.setPower(value=value, duration=duration, channel=channel)
    
    def shutdown(self):
        """Shutdown procedure for tool"""
        for thread in self._threads.values():
            thread.join()
        self.disconnect()
        self.resetFlags()
        return
    
    # Protected method(s)
    def _loop_timer(self):
        """Loop for counting time and flagging channels"""
        self.flags.timing_loop = True
        time.sleep(0.1)
        busy = self.is_busy
        timed_channels = self._timed_channels
        last_round = False
        while busy:
            finished_channels = list(set(timed_channels) - set(self._timed_channels))
            timed_channels = self._timed_channels
            if len(finished_channels):
                for c in finished_channels:
                    if self.channels[c].duration == 0:
                        continue
                    self.turnOff(c)
            self._update_power()
            time.sleep(0.01)
            if last_round:
                break
            if not self.is_busy:
                last_round = True
        self.flags.timing_loop = False
        self._threads.pop('timing_loop')
        self._timed_channels = []
        return
    
    def _update_power(self) -> str:
        """
        Update LED power levels by sending command to device

        Returns:
            str: command string
        """
        if not any([chn.update_power for chn in self.channels.values()]):
            return ''
        command = ';'.join([str(v) for v in self.getPower()])
        try:
            command = self.device.process_input(command)
        except:
            pass
        self.device.write(command)
        now = time.perf_counter()
        for chn in self.channels.values():
            if chn.update_power:
                chn.end_time = now + chn.duration
                chn.update_power = False
        return command
    