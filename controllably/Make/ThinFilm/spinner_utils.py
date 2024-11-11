# -*- coding: utf-8 -*-
"""
This module holds the class for spin-coaters.

Classes:
    Spinner (Maker)
    SpinnerAssembly (Maker)
"""
# Standard library imports
from __future__ import annotations
import logging
from threading import Thread
import time

# Local application imports
from ...core.compound import Ensemble
from ..make_utils import Maker

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.debug(f"Import: OK <{__name__}>")

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
    
    def __init__(self, 
        port: str,
        *,
        baudrate: int = 9600,
        verbose: bool = False,
        **kwargs
    ):
        """
        Instantiate the class

        Args:
            port (str): COM port address
            channel (int, optional): channel id. Defaults to 0.
            position (tuple[float], optional): x,y,z position of spinner. Defaults to (0,0,0).
        """
        super().__init__(port=port, baudrate=baudrate, verbose=verbose, **kwargs)
        self._speed = 0
        self._threads = {}
        
        self.connect()
        return
    
    # Properties
    @property
    def port(self) -> str:
        return self.device.connection_details.get('port', '')
    
    @property
    def speed(self) -> int:
        return self._speed
    
    def setSpeed(self, speed:int):
        """
        Set the spin speed of the spinner

        Args:
            speed (int): spin speed in rpm
        """
        self.device.query(speed)
        self._speed = speed
        return
    
    def soak(self, time_s:int, blocking:bool = True):
        """
        Executes a soak step

        Args:
            time_s (int): soak time in seconds
        """
        assert time_s >= 0, "Ensure the soak time is a non-negative integer"
        def inner():
            self.flags.busy = True
            logger.info(f"Soaking   : {time_s}s")
            self.setSpeed(0)
            time.sleep(time_s)
            self.flags.busy = False
            return
        if blocking:
            inner()
        else:
            thread = Thread(target=inner)
            thread.start()
            self._threads['soak'] = thread
        return

    def spin(self, speed:int, time_s:int, blocking:bool = True):
        """
        Executes a spin step

        Args:
            speed (int): spin speed in rpm
            time_s (int): spin time in seconds
        """
        assert speed >= 0, "Ensure the spin speed is a non-negative integer"
        assert time_s >= 0, "Ensure the spin time is a non-negative integer"
        def inner():
            self.flags.busy = True
            logger.info(f"Spin speed: {speed}")
            logger.info(f"Duration  : {time_s}s")
            self.setSpeed(speed)
            start_time = time.perf_counter()
            while (time_s >= (time.perf_counter() - start_time)):
                time.sleep(0.1)
            self.setSpeed(0)
            self.flags.busy = False
            return
        if blocking:
            inner()
        else:
            thread = Thread(target=inner)
            thread.start()
            self._threads['spin'] = thread
        return
    
    # Overwritten method(s)
    def execute(self, soak_time:int = 0, spin_speed:int = 2000, spin_time:int = 1, blocking:bool = True, *args, **kwargs):
        """
        Execute the soak and spin steps

        Args:
            soak_time (int, optional): soak time. Defaults to 0.
            spin_speed (int, optional): spin speed. Defaults to 2000.
            spin_time (int, optional): spin time. Defaults to 1.
        """
        def inner():
            self.flags.busy = True
            self.soak(soak_time)
            self.spin(spin_speed, spin_time)
            self.flags.busy = False
            return
        if blocking:
            inner()
        else:
            thread = Thread(target=inner)
            thread.start()
            self._threads['execute'] = thread
        return
    
    def shutdown(self):
        for thread in self._threads.values():
            thread.join()
        self.disconnect()
        self.resetFlags()
        return

Multi_Spinner = Ensemble.factory(Spinner)
