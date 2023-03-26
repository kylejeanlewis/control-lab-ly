# %% -*- coding: utf-8 -*-
"""
Created: Tue 2022/11/01 17:13:35
@author: Chang Jie

Notes / actionables:
-
"""
# Standard library imports
from __future__ import annotations
from threading import Thread
import time
from typing import Optional

# Third party imports
import serial   # pip install pyserial

# Local application imports
from ..make_utils import Maker
print(f"Import: OK <{__name__}>")

class LED:
    """
    LED class represents a LED unit

    Args:
        channel (int): channel index
    """
    def __init__(self, channel:int):
        self.channel = channel
        self._duration = 0
        self._end_time = time.time()
        self._power = 0
        self.flags = {'power_update': False}
        pass
    
    # Properties
    @property
    def power(self) -> int:
        return self._power
    @power.setter
    def power(self, value:int):
        if type(value) == int and (0 <= value <= 255):
            self._power = value
            self.setFlag(power_update=True)
        else:
            print('Please input an integer between 0 and 255.')
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
    
    def setPower(self, value:int, time_s:int = 0):
        """
        Set power and duration for illumination

        Args:
            value (int): power level between 0 and 255
            time_s (int, optional): time duration in seconds. Defaults to 0.
        """
        self.power = value
        if time_s:
            self._duration = time_s
        return
    

class LEDArray(Maker):
    """
    UVLed class contains methods to control an LED array

    Args:
        port (str): com port address
        channels (list, optional): list of channels. Defaults to [0].
        verbose (bool, optional): whether to print outputs. Defaults to False.
    """
    
    _default_flags = {
        'busy': False,
        'connected': False,
        'execute_now': False,
        'timing_loop': False
    }
    
    def __init__(self, port:str, channels:list[int] = [0], **kwargs):
        super().__init__(**kwargs)
        self.channels = {chn: LED(chn) for chn in channels}
        self._threads = {}
        self._timed_channels = []
        self._connect(port)
        return
    
    # Properties
    @property
    def port(self) -> str:
        return self.connection_details.get('port', '')
    
    def getPower(self, channel:Optional[int] = None) -> list[int]:
        """
        Get power levels of channels

        Args:
            channel (int, optional): channel index. Defaults to None.

        Returns:
            list: list of power levels
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
            list: list of channels that are still timed
        """
        now = time.time()
        self._timed_channels = [chn.channel for chn in self.channels.values() if chn._end_time>now]
        return self._timed_channels
    
    def isBusy(self) -> bool:
        """
        Check whether LED array is still busy

        Returns:
            bool: whether LED array is still busy
        """
        busy = bool(len(self.getTimedChannels()))
        busy = busy | any([chn._duration for chn in self.channels.values()])
        return busy
    
    def setPower(self, value:int, time_s:int = 0, channel:Optional[int] = None):
        """
        Set the power value(s) for channel(s)

        Args:
            value (int): 8-bit integer for LED power
            time_s (int, optional): time duration in seconds. Defaults to 0.
            channel (int/iterable, optional): channel(s) for which to set power. Defaults to None.
        """
        if channel is None:
            for chn in self.channels.values():
                chn.setPower(value, time_s)
        elif type(channel) == int and channel in self.channels:
            self.channels[channel].setPower(value, time_s)
        self.startTiming()
        return
    
    def shutdown(self):
        for thread in self._threads.values():
            thread.join()
        return super().shutdown()
    
    def startTiming(self):
        """
        Start timing the illumination steps
        """
        if not self.flags['timing_loop']:
            thread = Thread(target=self._loop_timer)
            thread.start()
            self._threads['timing_loop'] = thread
            print("Timing...")
        return
    
    def turnOff(self, channel:Optional[int] = None):
        """
        Turn off the LED corresponding to the channel(s)

        Args:
            channel (int, optional): channel index to turn off. Defaults to None.
        """
        print(f"Turning off LED {channel}")
        self.setPower(0, channel=channel)
        return

    # Protected method(s)
    def _connect(self, port:str, baudrate:int = 9600, timeout:int = 1):
        """
        Connect to machine control unit

        Args:
            `port` (str): com port address
            `baudrate` (int, optional): baudrate. Defaults to 115200.
            `timeout` (int, optional): timeout in seconds. Defaults to 1.
            
        Returns:
            `serial.Serial`: serial connection to machine control unit if connection is successful, else `None`
        """
        self.connection_details = {
            'port': port,
            'baudrate': baudrate,
            'timeout': timeout
        }
        device = None
        try:
            device = serial.Serial(port, baudrate, timeout=timeout)
        except Exception as e:
            print(f"Could not connect to {port}")
            if self.verbose:
                print(e)
        else:
            time.sleep(5)   # Wait for grbl to initialize
            device.flushInput()
            self.turnOff()
            print(f"Connection opened to {port}")
            self.setFlag(connected=True)
        self.device = device
        return
        
    def _loop_timer(self):
        """
        Loop for counting time and flagging channels
        """
        self.setFlag(timing_loop=True)
        busy = self.isBusy()
        timed_channels = self._timed_channels
        last_round = False
        while busy:
            finished_channels = list(set(timed_channels) - set(self._timed_channels))
            timed_channels = self._timed_channels
            if len(finished_channels):
                for c in finished_channels:
                    self.turnOff(c)
            self._update_power()
            time.sleep(0.01)
            if last_round:
                break
            if not self.isBusy():
                last_round = True
        self.setFlag(timing_loop=False)
        self._timed_channels = []
        return
    
    def _update_power(self) -> str:
        """
        Update power levels by sending message to device

        Returns:
            str: message string
        """
        if not any([chn.flags['power_update'] for chn in self.channels.values()]):
            return ''
        message = f"{';'.join([str(v) for v in self.getPower()])}\n"
        try:
            self.device.write(bytes(message, 'utf-8'))
        except AttributeError:
            pass
        now = time.time()
        for chn in self.channels.values():
            if chn.flags['power_update']:
                chn._end_time = now + chn._duration
                chn._duration = 0
                chn.setFlag(power_update=False)
        if self.verbose:
            print(message)
        return message
    