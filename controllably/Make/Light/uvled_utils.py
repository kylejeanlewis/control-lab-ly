# %% -*- coding: utf-8 -*-
"""
Created: Tue 2022/11/01 17:13:35
@author: Chang Jie

Notes / actionables:
-
"""
# Standard library imports
from threading import Thread
import time

# Third party imports
import serial # pip install pyserial

# Local application imports
print(f"Import: OK <{__name__}>")

class LED(object):
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
        
        self._flags = {
            'power_update': False
        }
        pass
    
    @property
    def power(self):
        return self._power
    @power.setter
    def power(self, value:int):
        if type(value) == int and (0 <= value <= 255):
            self._power = value
            self.setFlag('power_update', True)
        else:
            print('Please input an integer between 0 and 255.')
        return
    
    def setFlag(self, name:str, value:bool):
        """
        Set a flag truth value

        Args:
            name (str): label
            value (bool): flag value
        """
        self._flags[name] = value
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
    

class LEDArray(object):
    """
    UVLed class contains methods to control an LED array

    Args:
        port (str): com port address
        channels (list, optional): list of channels. Defaults to [0].
        verbose (bool, optional): whether to print outputs. Defaults to False.
    """
    def __init__(self, port:str, channels:list = [0], verbose:bool = False):
        self.channels = {chn: LED(chn) for chn in channels}
        
        self.device = None
        self._flags = {
            'execute_now': False,
            'timing_loop': False
        }
        self._threads = {}
        self._timed_channels = []
        
        self.verbose = verbose
        self.port = None
        self._baudrate = None
        self._timeout = None
        self._connect(port)
        return
    
    def _connect(self, port:str, baudrate=9600, timeout=1):
        """
        Connect to serial port

        Args:
            port (str): com port address
            baudrate (int): baudrate
            timeout (int, optional): timeout in seconds. Defaults to None.
            
        Returns:
            serial.Serial: serial connection to machine control unit if connection is successful, else None
        """
        self.port = port
        self._baudrate = baudrate
        self._timeout = timeout
        device = None
        try:
            device = serial.Serial(port, baudrate, timeout=timeout)
            time.sleep(5)   # Wait for grbl to initialize
            device.flushInput()
            self.turnOff()
            print(f"Connection opened to {port}")
        except Exception as e:
            if self.verbose:
                print(f"Could not connect to {port}")
                print(e)
        self.device = device
        return self.device
    
    def _loop_count_time(self):
        """
        Loop for counting time and flagging channels
        """
        self.setFlag('timing_loop', True)
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
        self.setFlag('timing_loop', False)
        self._timed_channels = []
        return
    
    def _update_power(self):
        """
        Update power levels by sending message to device

        Returns:
            str: message string
        """
        if not any([chn._flags['power_update'] for chn in self.channels.values()]):
            return ''
        message = f"{';'.join([str(v) for v in self.getPower()])}\n"
        try:
            self.device.write(bytes(message, 'utf-8'))
        except AttributeError:
            pass
        now = time.time()
        for chn in self.channels.values():
            if chn._flags['power_update']:
                chn._end_time = now + chn._duration
                chn._duration = 0
                chn.setFlag('power_update', False)
        if self.verbose:
            print(message)
        return message
    
    def getPower(self, channel:int = None):
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
    
    def getTimedChannels(self):
        """
        Get channels that are still timed

        Returns:
            list: list of channels that are still timed
        """
        now = time.time()
        self._timed_channels = [chn.channel for chn in self.channels.values() if chn._end_time>now]
        return self._timed_channels
    
    def isBusy(self):
        """
        Check whether LED array is still busy

        Returns:
            bool: whether LED array is still busy
        """
        busy = bool(len(self.getTimedChannels()))
        busy = busy | any([chn._duration for chn in self.channels.values()])
        return busy
    
    def isConnected(self):
        """
        Checks whether the LED array is connected

        Returns:
            bool: whether the spinner is connected
        """
        if self.device is None:
            print(f"{self.__class__} ({self.port}) not connected.")
            return False
        return True
    
    def setFlag(self, name:str, value:bool):
        """
        Set a flag truth value

        Args:
            name (str): label
            value (bool): flag value
        """
        self._flags[name] = value
        return
    
    def setPower(self, value:int, time_s:int = 0, channel:int =None):
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
    
    def startTiming(self):
        """
        Start timing the illumination steps
        """
        if not self._flags['timing_loop']:
            thread = Thread(target=self._loop_count_time)
            thread.start()
            self._threads['timing_loop'] = thread
            print("Timing...")
        return
    
    def turnOff(self, channel:int = None):
        """
        Turn off the LED corresponding to the channel(s)

        Args:
            channel (int, optional): channel index to turn off. Defaults to None.
        """
        print(f"Turning off LED {channel}")
        self.setPower(0, channel=channel)
        return
