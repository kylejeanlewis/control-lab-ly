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
    Spinner class contains methods to control the spin coater unit

    Args:
        port (str): com port address
        channel (int, optional): channel. Defaults to 0.
        position (tuple, optional): x,y,z position of spinner. Defaults to (0,0,0).
        verbose (bool, optional): whether to print outputs. Defaults to False.
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
        super().__init__(**kwargs)
        self.channel = channel
        self.position = tuple(position)
        self.speed = 0
        
        self._connect(port)
        return
    
    def execute(self, soak_time:int = 0, spin_speed:int = 2000, spin_time:int = 1, **kwargs):
        """
        Executes the soak and spin steps

        Args:
            soak_time (int, optional): soak time. Defaults to 0.
            spin_speed (int, optional): spin speed. Defaults to 2000.
            spin_time (int, optional): spin time. Defaults to 1.
            channel (int, optional): channel index. Defaults to None.
        """
        self.setFlag(busy=True)
        self.soak(soak_time)
        self.spin(spin_speed, spin_time)
        self.setFlag(busy=False)
        return
    
    def shutdown(self):
        return super().shutdown()

    def soak(self, seconds:int, **kwargs):
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

    def spin(self, speed:int, seconds:int, **kwargs):
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
            time.sleep(2)   # Wait for grbl to initialize
            device.flushInput()
            print(f"Connection opened to {port}")
            self.setFlag(connected=True)
        self.device = device
        return
    
    def _diagnostic(self):
        """
        Run diagnostic on tool
        """
        thread = Thread(target=self.execute, name=f'maker_diag_{self.channel}')
        thread.start()
        time.sleep(1)
        return
    
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


class SpinnerAssembly(Maker):
    """
    Spinner assembly with multiple spinners

    Args:
        ports (list, optional): list of com port strings. Defaults to [].
        channels (list, optional): list of int channel indices. Defaults to [].
        positions (list, optional): list of tuples of x,y,z spinner positions. Defaults to [].
    """
    
    _default_flags = {
        'busy': False,
        'connected': False
    }
    
    def __init__(self, 
        ports:list[str], 
        channels:list[int], 
        positions:list[tuple[float]], 
        **kwargs
    ):
        super().__init__(**kwargs)
        self.channels = {}
        self._threads = {}
        
        self._connect(port=ports, channel=channels, position=positions)
        return

    def disconnect(self):
        for channel in self.channels.values():
            channel.disconnect()
        return super().disconnect() 
        
    def execute(self, soak_time:int, spin_speed:int, spin_time:int, channel:int):
        """
        Executes the soak and spin steps

        Args:
            soak_time (int): soak time
            spin_speed (int): spin speed
            spin_time (int): spin time
            channel (int): channel index
        """
        thread = Thread(target=self.channels[channel].execute, args=(soak_time, spin_speed, spin_time))
        thread.start()
        self._threads[f'channel_{channel}_execute'] = thread
        return
    
    def isBusy(self) -> bool:
        """
        Check whether any of the spinners are still busy

        Returns:
            bool: whether any of the spinners are busy
        """
        return any([channel.isBusy() for channel in self.channels.values()])
    
    def isConnected(self) -> bool:
        """
        Check whether all spinners are connected

        Returns:
            bool: whether all spinners are connected
        """
        return all([channel.isConnected() for channel in self.channels.values()])
    
    def shutdown(self):
        for thread in self._threads.values():
            thread.join()
        return super().shutdown()
    
    def soak(self, seconds:int, channel:int):
        """
        Executes the soak step

        Args:
            seconds (int): soak time
            channel (int): channel index
        """
        thread = Thread(target=self.channels[channel].soak, args=(seconds,))
        thread.start()
        self._threads[f'channel_{channel}_soak'] = thread
        return
    
    def spin(self, speed:int, seconds:int, channel:int):
        """
        Executes the spin step

        Args:
            speed (int): spin speed
            seconds (int): spin time
            channel (int): channel index
        """
        thread = Thread(target=self.channels[channel].spin, args=(speed, seconds))
        thread.start()
        self._threads[f'channel_{channel}_spin'] = thread
        return

    # Protected method(s)
    def _connect(self, **kwargs):
        properties = Helper.zip_inputs('channel', **kwargs)
        self.channels = {key: Spinner(**value) for key,value in properties.items()}
        return
    
    def _diagnostic(self):
        """
        Run diagnostic on tool
        """
        for channel in self.channels.values():
            channel._diagnostic()
        return
    