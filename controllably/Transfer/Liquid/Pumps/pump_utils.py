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
print(f"Import: OK <{__name__}>")

class Pump(object):
    def __init__(self, port:str, verbose=False):
        self.device = None
        self._flags = {
            'busy': False
        }
        
        self.verbose = verbose
        self.port = ''
        self._baudrate = None
        self._timeout = None
        self._connect(port)
        return
    
    def _connect(self, port:str, baudrate=9600, timeout=1):
        """
        Connect to machine control unit

        Args:
            port (str): com port address
            baudrate (int): baudrate. Defaults to 9600.
            timeout (int, optional): timeout in seconds. Defaults to None.
            
        Returns:
            serial.Serial: serial connection to machine control unit if connection is successful, else None
        """
        self.port = port
        self._baudrate = baudrate
        self._timeout = timeout
        device = None
        try:
            device = serial.Serial(port, self._baudrate, timeout=self._timeout)
            time.sleep(2)   # Wait for grbl to initialize
            device.flushInput()
            print(f"Connection opened to {port}")
        except Exception as e:
            if self.verbose:
                print(f"Could not connect to {port}")
                print(e)
        self.device = device
        return self.device
    
    def connect(self):
        """
        Reconnect to device using existing port and baudrate
        
        Returns:
            serial.Serial: serial connection to machine control unit if connection is successful, else None
        """
        return self._connect(self.port, self._baudrate, self._timeout)
    
    def isBusy(self):
        """
        Checks whether the pump is busy
        
        Returns:
            bool: whether the pump is busy
        """
        return self._flags['busy']
    
    def isConnected(self):
        """
        Check whether machine control unit is connected

        Returns:
            bool: whether machine control unit is connected
        """
        if self.device == None:
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
    

class Peristaltic(Pump):
    """
    Peristaltic pump object

    Args:
        port (str): com port address
        verbose (bool, optional): whether to print output. Defaults to False.
    """
    def __init__(self, port:str, verbose=False):
        self.device = None
        self._flags = {
            'busy': False
        }
        
        self.verbose = verbose
        self.port = ''
        self._baudrate = None
        self._timeout = None
        self._connect(port)
        return
    
    def _connect(self, port:str, baudrate=9600, timeout=1):
        """
        Connect to machine control unit

        Args:
            port (str): com port address
            baudrate (int): baudrate. Defaults to 9600.
            timeout (int, optional): timeout in seconds. Defaults to None.
            
        Returns:
            serial.Serial: serial connection to machine control unit if connection is successful, else None
        """
        self.port = port
        self._baudrate = baudrate
        self._timeout = timeout
        device = None
        try:
            device = serial.Serial(port, self._baudrate, timeout=self._timeout)
            time.sleep(2)   # Wait for grbl to initialize
            device.flushInput()
            print(f"Connection opened to {port}")
        except Exception as e:
            if self.verbose:
                print(f"Could not connect to {port}")
                print(e)
        self.device = device
        return self.device
    
    def _run_pump(self, speed:int):
        """
        Relay instructions to pump
        
        Args:
            speed (int): speed of pump of rotation
        """
        try:
            self.device.write(bytes(f"{speed}\n", 'utf-8'))
        except AttributeError:
            pass
        return
        
    def _run_solenoid(self, state:int):
        """
        Relay instructions to valve.
        
        Args:
            state (int): open or close valve channel (-1~-8 open valve; 1~8 close valve; 9 close all valves)
        """
        try:
            self.device.write(bytes(f"{state}\n", 'utf-8'))
        except AttributeError:
            pass
        return
    
    def connect(self):
        """
        Reconnect to device using existing port and baudrate
        
        Returns:
            serial.Serial: serial connection to machine control unit if connection is successful, else None
        """
        return self._connect(self.port, self._baudrate, self._timeout)
    
    def isBusy(self):
        """
        Checks whether the pump is busy
        
        Returns:
            bool: whether the pump is busy
        """
        return self._flags['busy']
    
    def isConnected(self):
        """
        Check whether machine control unit is connected

        Returns:
            bool: whether machine control unit is connected
        """
        if self.device == None:
            print(f"{self.__class__} ({self.port}) not connected.")
            return False
        return True

    def push(self, speed:int, push_time, pullback_time, channel:int):
        """
        Dispense (aspirate) liquid from (into) syringe
        
        Args:
            speed (int): speed of pump of rotation (<0 aspirate; >0 dispense)
            push_time (int, or float): time to achieve desired volume
            pullback_time (int, or float): time to pullback the peristaltic pump
            channel (int): valve channel
        """
        run_time = pullback_time + push_time
        interval = 0.1
        
        start_time = time.time()
        self._run_solenoid(-channel) # open channel
        self._run_pump(speed)
        
        while(True):
            time.sleep(0.001)
            if (interval <= time.time() - start_time):
                interval += 0.1
            if (run_time <= time.time() - start_time):
                break
        
        start_time = time.time()
        self._run_solenoid(-channel) # open channel
        self._run_pump(-abs(speed))

        while(True):
            time.sleep(0.001)
            if (interval <= time.time() - start_time):
                interval += 0.1
            if (pullback_time <= time.time() - start_time):
                self._run_pump(10)
                self._run_solenoid(channel) # close channel
                break
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
