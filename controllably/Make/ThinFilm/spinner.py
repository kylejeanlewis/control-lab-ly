# -*- coding: utf-8 -*-
"""
This module holds the spinner class.

## Classes:
    `Spinner`: Spinner class
    `Multi_Spinner`: Ensemble of spinner tools
    
<i>Documentation last updated: 2025-02-22</i>
"""
# Standard Library imports
from __future__ import annotations
import threading

# Local application imports
from ...core.compound import Ensemble
from ...core.device import TimedDeviceMixin
from .. import Maker

class Spinner(TimedDeviceMixin, Maker):
    """ 
    Spinner class
    
    ### Constructor:
        `port` (str): port to connect to
        `baudrate` (int, optional): baudrate of the connection. Defaults to 9600.
        `verbose` (bool, optional): verbosity of the class. Defaults to False.
        
    ### Attributes and properties:
        `target_rpm` (int): target rpm of the spinner
        `timer_event` (threading.Event): event for timer
        `threads` (dict): threads for the spinner
        
    ### Methods:
        `soak`: soak the spinner
        `spin`: spin the spinner
        `stop`: stop the spinner
        `setSpinSpeed`: set the spin speed
        `setValue`: set the spin speed
        `execute`: execute the soak and spin steps
        `shutdown`: shutdown procedure for the spinner
    """
    
    def __init__(self, port: str, *, baudrate: int = 9600, verbose = False, **kwargs):
        """
        Initialize the spinner
        
        Args:
            port (str): port to connect to
            baudrate (int, optional): baudrate of the connection. Defaults to 9600.
            verbose (bool, optional): verbosity of the class. Defaults to False.
        """
        super().__init__(port=port, baudrate=baudrate, verbose=verbose, **kwargs)
        
        self.target_rpm = 0
        self.timer_event = threading.Event()
        self.threads = dict()
        return
    
    def soak(self, duration: int|float, blocking: bool = True):
        """
        Soak the spinner for a given duration
        
        Args:
            duration (int): soak time in seconds
            blocking (bool, optional): whether to block the thread. Defaults to True.
        """
        return self.spin(0, duration, blocking)
    
    def spin(self, rpm: int, duration: int|float, blocking: bool = True):
        """
        Spin the spinner at a given speed
        
        Args:
            rpm (int): spin speed in rpm
            duration (int): spin time in seconds
            blocking (bool, optional): whether to block the thread. Defaults to True.
        """
        timer = self.setValueDelayed(duration, rpm, 0, blocking, event=self.timer_event)
        if isinstance(timer, threading.Timer):
            self.threads['timer'] = timer
        return
    
    def stop(self):
        """Stop the spinner"""
        self.stopTimer(self.threads.get('timer', None), event=self.timer_event)
        return
    
    def setSpinSpeed(self, rpm: int, event: threading.Event|None = None) -> bool:
        """
        Set the spin speed in rpm
        
        Args:
            rpm (int): spin speed in rpm
            event (threading.Event, optional): event to set. Defaults to None.
            
        Returns:
            bool: whether the command was successful
        """
        assert rpm >= 0, "Ensure the spin speed is a non-negative number"
        if self.timer_event.is_set() and rpm != 0:
            self._logger.info("[BUSY] Spinner is currently in use")
            return False
        self._logger.info(f"[SPIN] {rpm}")
        self.device.write(self.device.processInput(rpm))
        self.target_rpm = rpm
        if isinstance(event, threading.Event):
            _ = event.clear() if event.is_set() else event.set()
        return True
    
    def setValue(self, value: int, event: threading.Event|None = None) -> bool:
        """ 
        Set the spin speed in rpm
        
        Args:
            value (int): spin speed in rpm
            event (threading.Event, optional): event to set. Defaults to None.
            
        Returns:
            bool: whether the command was successful
        """
        return self.setSpinSpeed(value, event)
    
    # Overwritten method(s)
    def execute(self, soak_time:int|float = 0, spin_speed:int = 2000, spin_time:int|float = 1, blocking:bool = True, *args, **kwargs):
        """
        Execute the soak and spin steps

        Args:
            soak_time (int, optional): soak time. Defaults to 0.
            spin_speed (int, optional): spin speed. Defaults to 2000.
            spin_time (int, optional): spin time. Defaults to 1.
            blocking (bool, optional): whether to block the thread. Defaults to True.
        """
        def inner(soak_time:int|float, spin_speed:int, spin_time:int|float):
            if self.timer_event.is_set():
                self._logger.info("[BUSY] Spinner is currently in use")
            self.soak(soak_time)
            self.spin(spin_speed, spin_time)
            return
        if blocking:
            inner(soak_time, spin_speed, spin_time)
            return
        thread = threading.Thread(target=inner, args=(soak_time, spin_speed, spin_time))
        thread.start()
        self.threads['execute'] = thread
        return
    
    def shutdown(self):
        if 'timer' in self.threads and isinstance(self.threads['timer'], threading.Timer):
            self.threads['timer'].cancel()
        for thread in self.threads.values():
            if isinstance(thread, threading.Thread):
                thread.join()
        self.disconnect()
        self.resetFlags()
        return super().shutdown()

Multi_Spinner = Ensemble.factory(Spinner)
