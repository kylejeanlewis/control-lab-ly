# -*- coding: utf-8 -*-
"""
This module contains the LED class.

## Classes:
    `LED`: LED class
    `Multi_LED`: Multi-channel LED class
    
<i>Documentation last updated: 2025-02-22</i>
"""
# Standard Library imports
from __future__ import annotations
import threading
import time

# Local application imports
from ...core.compound import Multichannel
from ...core.device import TimedDeviceMixin
from .. import Maker

class LED(Maker, TimedDeviceMixin):
    """ 
    LED class
    
    ### Constructor:
        `port` (str, optional): port to connect to. Defaults to 'COM0'.
        `channel` (int, optional): channel number. Defaults to 0.
        `baudrate` (int, optional): baudrate for connection. Defaults to 9600.
        `verbose` (bool, optional): verbosity of class. Defaults to False.
        
    ### Attributes and properties:
        `channel` (int): channel number
        `target_power` (int): target power level
        `timer_event` (threading.Event): timer event
        `threads` (dict): threads
        
    ### Methods:
        `dark`: Darken the LED
        `light`: Light up the LED
        `stop`: Stop the LED
        `getPower`: Get the power level of the LED
        `setPower`: Set the power level of the LED
        `setValue`: Set the power level of the LED
        `updatePower`: Update the power level of the LED
        `execute`: Execute the dark and spin steps
        `shutdown`: Shutdown procedure for the LED
    """
    
    def __init__(self, 
        port: str = 'COM0', 
        channel: int = 0,
        *, 
        baudrate: int = 9600, 
        verbose = False, 
        **kwargs
    ):
        """
        Initialize the LED class
        
        Args:
            port (str, optional): port to connect to. Defaults to 'COM0'.
            channel (int, optional): channel number. Defaults to 0.
            baudrate (int, optional): baudrate for connection. Defaults to 9600.
            verbose (bool, optional): verbosity of class. Defaults to False.
        """
        super().__init__(port=port, baudrate=baudrate, verbose=verbose, **kwargs)
        
        self.channel = channel
        self.target_power = 0
        self.timer_event = threading.Event()
        self.threads = dict()
        return
    
    def getAttributes(self) -> dict:
        """
        Get relevant attributes of the class
        
        Returns:
            dict: relevant attributes
        """
        relevant = ['targer_power', 'timer_event', 'threads']
        return {key: getattr(self, key) for key in relevant}
    
    def dark(self, duration: int|float, blocking: bool = True):
        """
        Darken the LED for a given duration
        
        Args:
            duration (int|float): duration to darken the LED
            blocking (bool, optional): whether to block the thread. Defaults to True.
        """
        return self.light(0, duration, blocking)
    
    def light(self, power: int, duration: int|float, blocking: bool = True):
        """
        Light up the LED at a given power level for a given duration
        
        Args:
            power (int): power level
            duration (int|float): duration to light up the LED
            blocking (bool, optional): whether to block the thread. Defaults to
        """
        timer = self.setValueDelayed(duration, power, 0, blocking, event=self.timer_event)
        if isinstance(timer, threading.Timer):
            self.threads['timer'] = timer
        return
    
    def stop(self):
        """Stop the LED from emitting light"""
        self.stopTimer(self.threads.get('timer', None), event=self.timer_event)
        return
    
    def getPower(self) -> int:
        """
        Get the current power level of the LED
        
        Returns:
            int: power level
        """
        return self.target_power
    
    def setPower(self, power: int, event: threading.Event|None = None) -> bool:
        """
        Set power level of LED
        
        Args:
            power (int): power level
            event (threading.Event, optional): event to set. Defaults to None.
            
        Returns:
            bool: whether the power level was set
        """
        assert power >= 0, "Ensure the power level is a non-negative number"
        if self.timer_event.is_set() and power != 0:
            self._logger.info(f"[BUSY] LED {self.channel} is currently in use")
            return False
        self._logger.info(f"[LED {self.channel}] {power}")
        self.target_power = power
        self.updatePower()
        if isinstance(event, threading.Event):
            _ = event.clear() if event.is_set() else event.set()
        return True
    
    def setValue(self, value: int, event: threading.Event|None = None) -> bool:
        """ 
        Set the power level of the LED
        
        Args:
            value (int): power level
            event (threading.Event, optional): event to set. Defaults to None.
            
        Returns:
            bool: whether the power level was set
        """
        return self.setPower(value, event)
    
    def updatePower(self):
        """Update the power level of the LED"""
        all_power = self.getPower()
        all_power = all_power if isinstance(all_power, list) else [all_power]
        data = ';'.join([str(v) for v in all_power])
        self.device.write(self.device.processInput(data))
        return
    
    # Overwritten method(s)
    def execute(self, dark_time:int|float = 0, power:int = 255, light_time:int|float = 1, blocking:bool = True, *args, **kwargs):
        """
        Execute the dark and spin steps

        Args:
            dark_time (int, optional): dark time. Defaults to 0.
            power (int, optional): power level. Defaults to 255.
            light_time (int, optional): spin time. Defaults to 1.
            blocking (bool, optional): whether to block the thread. Defaults to True.
        """
        def inner(dark_time:int|float, power:int, light_time:int|float):
            if self.timer_event.is_set():
                self._logger.info("[BUSY] LED is currently in use")
                return
            self.dark(dark_time)
            self.light(power, light_time)
            return
        if blocking:
            inner(dark_time, power, light_time)
            return
        thread = threading.Thread(target=inner, args=(dark_time, power, light_time))
        thread.start()
        self.threads['execute'] = thread
        return
    
    def shutdown(self):
        """Shutdown procedure for the LED"""
        if 'timer' in self.threads and isinstance(self.threads['timer'], threading.Timer):
            self.threads['timer'].cancel()
        for thread in self.threads.values():
            if isinstance(thread, threading.Thread):
                thread.join()
        self.disconnect()
        self.resetFlags()
        return super().shutdown()

Multi_LED = Multichannel.factory(LED)
# Couple the getPower method to the Multi_LED class
Multi_LED.getPower = lambda self: [led.target_power for led in self.channels]
Multi_LED._channel_class.getPower = Multi_LED.getPower
