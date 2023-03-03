# %% -*- coding: utf-8 -*-
"""
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
print(f"Import: OK <{__name__}>")

class LED(object):
    def __init__(self, channel, position):
        self.channel = channel
        self.position = position
        self._power = 0
        pass
    
    @property
    def power(self):
        return self._power
    
    @power.setter
    def power(self, value:int):
        if type(value) == int and (0 <= value <= 255):
            self._power = value
        else:
            print('Please input an integer between 0 and 255.')
        return


class LEDArray(object):
    """
    UVLed class contains methods to control an LED array

    Args:
        port (str): com port address
        order (int, optional): channel order. Defaults to 0.
        position (tuple, optional): x,y,z position of spinner. Defaults to (0,0,0).
        verbose (bool, optional): whether to print outputs. Defaults to False.
    """
    def __init__(self, port:str, channels=[], positions=[], verbose:bool = False):
        properties = Helper.zip_inputs('channel', channel=channels, position=positions)
        self.channels = {key: LED(**kwargs) for key,kwargs in properties.items()}
        self.channels = channels
        self.positions = positions
        
        self.device = None
        self._flags = {}
        
        self.verbose = verbose
        self.port = None
        self._baudrate = None
        self._timeout = None
        self._connect(port)
        return
    
    def _connect(self, port:str, baudrate=115200, timeout=1):
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
            device = serial.Serial(port, 9600, timeout=1)
            time.sleep(2)   # Wait for grbl to initialize
            device.flushInput()
            self.turnOff()
            print(f"Connection opened to {port}")
        except Exception as e:
            if self.verbose:
                print(f"Could not connect to {port}")
                print(e)
        self.device = device
        return self.device
    
    def _update_power(self):
        message = f"{';'.join([c.power for c in self.channels.values()])}\n"
        try:
            self.device.write(bytes(message, 'utf-8'))
        except AttributeError:
            pass
        return
    
    def isConnected(self):
        """
        Checks whether the spinner is connected

        Returns:
            bool: whether the spinner is connected
        """
        if self.device is None:
            print(f"{self.__class__} ({self.port}) not connected.")
            return False
        return True
    
    def setPower(self, value:int, channel=None):
        """
        Set the power value(s) for channel(s)

        Args:
            value (int): 8-bit integer for LED power
            channel (int/iterable, optional): channel(s) for which to set power. Defaults to None.
        """
        if channel is None:
            for c in self.channels.values():
                c.power = value
        elif type(channel) == int and channel in self.channels:
            self.channels[channel].power = value
        self._update_power()
        return
    
    def turnOff(self, channel=None):
        """
        Turn off the LED corresponding to the channel(s)

        Args:
            channel (int/iterable, optional): channel(s) to turn off. Defaults to None.
        """
        self.setPower(0, channel=channel)
        return
