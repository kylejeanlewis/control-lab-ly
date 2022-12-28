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
from ...misc import HELPER
print(f"Import: OK <{__name__}>")

class Spinner(object):
    """
    Spinner class contains methods to control the spin coater unit

    Args:
        port (str): com port address
        order (int, optional): channel order. Defaults to 0.
        position (tuple, optional): x,y,z position of spinner. Defaults to (0,0,0).
        verbose (bool, optional): whether to print outputs. Defaults to False.
    """
    def __init__(self, port:str, order=0, position=(0,0,0), verbose=False, **kwargs):
        self.order = order
        self.position = tuple(position)
        self.speed = 0
        
        self.device = None
        self._flags = {
            'busy': False
        }
        
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
            device = serial.Serial(port, 9600, timeout=1)
            time.sleep(2)   # Wait for grbl to initialize
            device.flushInput()
            print(f"Connection opened to {port}")
        except Exception as e:
            if self.verbose:
                print(f"Could not connect to {port}")
                print(e)
        self.device = device
        return self.device
    
    def _run_speed(self, speed:int):
        """
        Relay spin speed to spinner

        Args:
            speed (int): spin speed
        """
        try:
            self.device.write(bytes(f"{speed}\n", 'utf-8'))
        except AttributeError:
            pass
        print("Spin speed: {}".format(speed))
        return
    
    def _run_spin_step(self, speed:int, run_time:int):
        """
        Perform timed spin step

        Args:
            speed (int): spin speed
            run_time (int): spin time
        """
        interval = 1
        start_time = time.time()
        self._run_speed(speed)
        
        while(True):
            time.sleep(0.1)
            if (interval <= time.time() - start_time):
                interval += 1
            if (run_time <= time.time() - start_time):
                self._run_speed(0)
                break
        return

    def execute(self, soak_time=0, spin_speed=2000, spin_time=1, channel=None):
        """
        Executes the soak and spin steps

        Args:
            soak_time (int, optional): soak time. Defaults to 0.
            spin_speed (int, optional): spin speed. Defaults to 2000.
            spin_time (int, optional): spin time. Defaults to 1.
            channel (int, optional): channel index. Defaults to None.
        """
        self._flags['busy'] = True
        self.soak(soak_time)
        self.spin(spin_speed, spin_time)
        self._flags['busy'] = False
        return
    
    def isBusy(self):
        """
        Checks whether the spinner is busy

        Returns:
            bool: whether the spinner is busy
        """
        return self._flags['busy']
    
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

    def soak(self, seconds:int, channel=None):
        """
        Executes the soak step

        Args:
            seconds (int): soak time
            channel (int, optional): channel index. Defaults to None.
        """
        self.speed = 0
        if seconds:
            time.sleep(seconds)
        return

    def spin(self, speed:int, seconds:int, channel=None):
        """
        Executes the spin step

        Args:
            speed (int): spin speed
            seconds (int): spin time
            channel (int, optional): channel index. Defaults to None.
        """
        self.speed = speed
        self._run_spin_step(speed, seconds)
        self.speed = 0
        return


class SpinnerAssembly(object):
    """
    Spinner assembly with multiple spinners

    Args:
        ports (list, optional): list of com port strings. Defaults to [].
        channels (list, optional): list of int channel indices. Defaults to [].
        positions (list, optional): list of tuples of x,y,z spinner positions. Defaults to [].
    """
    def __init__(self, ports=[], channels=[], positions=[]):
        properties = HELPER.zip_inputs('channel', port=ports, channel=channels, position=positions)
        self.channels = {chn: Spinner(port, chn, pos) for port,chn,pos in properties}
        return
        
    def execute(self, soak_time:int, spin_speed:int, spin_time:int, channel:int):
        """
        Executes the soak and spin steps

        Args:
            soak_time (int): soak time
            spin_speed (int): spin speed
            spin_time (int): spin time
            channel (int): channel index
        """
        return self.channels[channel].execute(soak_time, spin_speed, spin_time)
    
    def isBusy(self):
        """
        Check whether any of the spinners are still busy

        Returns:
            bool: whether any of the spinners are busy
        """
        return any([spinner.isBusy() for spinner in self.channels.values()])
    
    def isConnected(self):
        """
        Check whether all spinners are connected

        Returns:
            bool: whether all spinners are connected
        """
        return all([spinner.isConnected() for spinner in self.channels.values()])
    
    def soak(self, seconds:int, channel:int):
        """
        Executes the soak step

        Args:
            seconds (int): soak time
            channel (int): channel index
        """
        return self.channels[channel].soak(seconds)
    
    def spin(self, speed:int, seconds:int, channel:int):
        """
        Executes the spin step

        Args:
            speed (int): spin speed
            seconds (int): spin time
            channel (int): channel index
        """
        return self.channels[channel].spin(speed, seconds)
