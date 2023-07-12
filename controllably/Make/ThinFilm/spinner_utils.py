# %% -*- coding: utf-8 -*-
"""
This module holds the class for spin-coaters.

Classes:
    Spinner (Maker)
    SpinnerAssembly (Maker)
"""
# Standard library imports
from __future__ import annotations
import numpy as np
from threading import Thread
import time

# Third party imports
import serial   # pip install pyserial

# Local application imports
from ...misc import Helper
from ..make_utils import Maker
print(f"Import: OK <{__name__}>")

class Spinner(Maker):
    """
    Spinner provides methods to control a single spin coater controller unit
    
    ### Constructor
    Args:
        `port` (str): COM port address
        `channel` (int, optional): channel id. Defaults to 0.
        `position` (tuple[float], optional): x,y,z position of spinner. Defaults to (0,0,0).

    ### Attributes
    - `channel` (int): channel id
    - `speed` (int): spin speed in rpm
    
    ### Properties
    - `port` (str): COM port address
    - `position` (np.ndarray): x,y,z position of spinner
    
    ### Methods
    - `execute`: alias for `run()`
    - `run`: executes the soak and spin steps
    - `shutdown`: shutdown procedure for tool
    - `soak`: executes a soak step
    - `spin`: execute a spin step
    """
    
    _default_flags = {
        'busy': False,
        'connected': False
    }
    
    def __init__(self, 
        port: str, 
        channel: int = 0, 
        position: tuple[float] = (0,0,0), 
        **kwargs
    ):
        """
        Instantiate the class

        Args:
            port (str): COM port address
            channel (int, optional): channel id. Defaults to 0.
            position (tuple[float], optional): x,y,z position of spinner. Defaults to (0,0,0).
        """
        super().__init__(**kwargs)
        self.channel = channel
        self._position = tuple(position)
        self.speed = 0
        self._connect(port)
        return
    
    # Properties
    @property
    def port(self) -> str:
        return self.connection_details.get('port', '')
    
    @property
    def position(self) -> np.ndarray:
        return np.array(self._position)
    
    def execute(self, soak_time:int = 0, spin_speed:int = 2000, spin_time:int = 1, *args, **kwargs):
        """
        Alias for `run()`
        
        Execute the soak and spin steps

        Args:
            soak_time (int, optional): soak time. Defaults to 0.
            spin_speed (int, optional): spin speed. Defaults to 2000.
            spin_time (int, optional): spin time. Defaults to 1.
        """
        return self.run(soak_time=soak_time, spin_speed=spin_speed, spin_time=spin_time)
    
    def run(self, soak_time:int = 0, spin_speed:int = 2000, spin_time:int = 1, **kwargs):
        """
        Execute the soak and spin steps

        Args:
            soak_time (int, optional): soak time. Defaults to 0.
            spin_speed (int, optional): spin speed. Defaults to 2000.
            spin_time (int, optional): spin time. Defaults to 1.
        """
        self.setFlag(busy=True)
        self.soak(soak_time)
        self.spin(spin_speed, spin_time)
        self.setFlag(busy=False)
        return
    
    def shutdown(self):
        """Shutdown procedure for tool"""
        return super().shutdown()

    def soak(self, time_s:int, **kwargs):
        """
        Executes a soak step

        Args:
            time_s (int): soak time in seconds
        """
        self.speed = 0
        print(f"Soaking    (channel {self.channel}): {time_s}s")
        if time_s:
            time.sleep(time_s)
        return

    def spin(self, speed:int, time_s:int, **kwargs):
        """
        Executes a spin step

        Args:
            speed (int): spin speed in rpm
            time_s (int): spin time in seconds
        """
        self._query(speed)
        self.speed = speed
        print(f"Duration   (channel {self.channel}): {time_s}s")
        interval = 1
        start_time = time.perf_counter()
        while(True):
            time.sleep(0.1)
            if (interval <= time.perf_counter() - start_time):
                interval += 1
            if (time_s <= time.perf_counter() - start_time):
                break
        self._query(0)
        self.speed = 0
        return

    # Protected method(s)
    def _connect(self, port:str, baudrate:int = 9600, timeout:int = 1):
        """
        Connection procedure for tool

        Args:
            port (str): COM port address
            baudrate (int, optional): baudrate. Defaults to 9600.
            timeout (int, optional): timeout in seconds. Defaults to 1.
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
            time.sleep(2)   # Wait for grbl to initialize
            device.reset_input_buffer()
            print(f"Connection opened to {port}")
            self.setFlag(connected=True)
        self.device = device
        return
    
    def _diagnostic(self):
        """Run diagnostic test"""
        thread = Thread(target=self.run, name=f'maker_diag_{self.channel}')
        thread.start()
        time.sleep(1)
        return
    
    def _query(self, command:str) ->list[str]:
        """
        Write command to and read response from device

        Args:
            command (str): command string to send to device

        Returns:
            list[str]: list of response string(s) from device
        """
        responses = [b'']
        self._write(command)
        try:
            responses = self.device.readline()
        except Exception as e:
            if self.verbose:
                print(e)
        else:
            if self.verbose:
                print(responses)
        return
    
    def _write(self, speed:int):
        """
        Relay spin speed to spinner

        Args:
            speed (int): spin speed in rpm
        """
        fstring = f"{speed}\n"
        if self.verbose:
            print(fstring)
        try:
            self.device.write(fstring.encode('utf-8'))
        except AttributeError:
            pass
        print(f"Spin speed (channel {self.channel}): {speed}")
        return


class SpinnerAssembly(Maker):
    """
    SpinnerAssembly provides methods to control multiple spin coater controller units
    
    ### Constructor
    Args:
        `ports` (list[str]): COM port addresses
        `channels` (list[int]): channel ids
        `positions` (list[tuple[float]]): x,y,z positions of spinners
    
    ### Attributes
    - `channels` (dict[int, Spinner]): dictionary of {channel id, `Spinner` objects}
    
    ### Methods
    - `disconnect`: disconnect from device
    - `execute`: alias for `run()`
    - `isBusy`: checks and returns whether any of the spinners are still busy
    - `isConnected`: checks and returns whether all spinners are connected
    - `run`: executes the soak and spin steps
    - `shutdown`: shutdown procedure for tool
    - `soak`: executes a soak step
    - `spin`: execute a spin step
    """
    
    _default_flags = {
        'busy': False,
        'connected': False
    }
    
    def __init__(self, 
        ports: list[str], 
        channels: list[int], 
        positions: list[tuple[float]],
        **kwargs
    ):
        """
        Instantiate the class

        Args:
            ports (list[str]): COM port addresses
            channels (list[int]): channel ids
            positions (list[tuple[float]]): x,y,z positions of spinners
        """
        super().__init__(**kwargs)
        self.channels = {}
        self._threads = {}
        
        self._connect(port=ports, channel=channels, position=positions, verbose=self.verbose)
        return

    def disconnect(self):
        """Disconnect from device"""
        for channel in self.channels.values():
            channel.disconnect()
        return super().disconnect() 
    
    def execute(self, soak_time:int, spin_speed:int, spin_time:int, channel:int, *args, **kwargs):
        """
        Alias for `run()`
        
        Execute the soak and spin steps

        Args:
            soak_time (int): soak time
            spin_speed (int): spin speed
            spin_time (int): spin time
            channel (int): channel id
        """
        return self.run(soak_time=soak_time, spin_speed=spin_speed, spin_time=spin_time, channel=channel)
        
    def isBusy(self) -> bool:
        """
        Checks and returns whether any of the spinners are still busy

        Returns:
            bool: whether any of the spinners are still busy
        """
        return any([channel.isBusy() for channel in self.channels.values()])
    
    def isConnected(self) -> bool:
        """
        Checks and returns whether all spinners are connected

        Returns:
            bool: whether all spinners are connected
        """
        return all([channel.isConnected() for channel in self.channels.values()])
    
    def run(self, soak_time:int, spin_speed:int, spin_time:int, channel:int):
        """
        Execute the soak and spin steps

        Args:
            soak_time (int): soak time
            spin_speed (int): spin speed
            spin_time (int): spin time
            channel (int): channel id
        """
        thread = Thread(target=self.channels[channel].run, args=(soak_time, spin_speed, spin_time))
        thread.start()
        self._threads[f'channel_{channel}_run'] = thread
        return
    
    def shutdown(self):
        """Shutdown procedure for tool"""
        for thread in self._threads.values():
            thread.join()
        return super().shutdown()
    
    def soak(self, seconds:int, channel:int):
        """
        Executes a soak step

        Args:
            time_s (int): soak time in seconds
            channel (int): channel id
        """
        thread = Thread(target=self.channels[channel].soak, args=(seconds,))
        thread.start()
        self._threads[f'channel_{channel}_soak'] = thread
        return
    
    def spin(self, speed:int, seconds:int, channel:int):
        """
        Executes a spin step

        Args:
            speed (int): spin speed in rpm
            time_s (int): spin time in seconds
            channel (int): channel id
        """
        thread = Thread(target=self.channels[channel].spin, args=(speed, seconds))
        thread.start()
        self._threads[f'channel_{channel}_spin'] = thread
        return

    # Protected method(s)
    def _connect(self, **kwargs):
        """Connection procedure for tool"""
        properties = Helper.zip_inputs('channel', **kwargs)
        self.channels = {key: Spinner(**value) for key,value in properties.items()}
        return
    
    def _diagnostic(self):
        """Run diagnostic test"""
        for channel in self.channels.values():
            channel._diagnostic()
        return
    