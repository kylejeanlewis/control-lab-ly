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
import logging
import threading

# Local application imports
from ...core.compound import Multichannel
from ...core.device import TimedDeviceMixin
from .. import Maker

# Configure logging
logger = logging.getLogger(__name__)

class LED(TimedDeviceMixin, Maker):
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
        self._parent = self
        return
    
    def getAttributes(self) -> dict:
        """
        Get relevant attributes of the class
        
        Returns:
            dict: relevant attributes
        """
        relevant = ['target_power', 'timer_event', 'threads']
        return {key: getattr(self, key) for key in relevant}
    
    def dark(self, duration: int|float, blocking: bool = True, **kwargs):
        """
        Darken the LED for a given duration
        
        Args:
            duration (int|float): duration to darken the LED
            blocking (bool, optional): whether to block the thread. Defaults to True.
        """
        if self.channel != self._parent.channel:
            return
        return self.light(0, duration, blocking, **kwargs)
    
    def light(self, power: int, duration: int|float, blocking: bool = True, **kwargs):
        """
        Light up the LED at a given power level for a given duration
        
        Args:
            power (int): power level
            duration (int|float): duration to light up the LED
            blocking (bool, optional): whether to block the thread. Defaults to
        """
        if self.channel != self._parent.channel:
            self._logger.debug(f'{self.channel=} != {self._parent.channel=}, not lighting')
            return
        timer = self.setValueDelayed(duration, power, 0, blocking, event=self.timer_event, **kwargs)
        if isinstance(timer, threading.Timer):
            self.threads['timer'] = timer
        return
    
    def stop(self, **kwargs):
        """Stop the LED from emitting light"""
        if self.channel != self._parent.channel:
            self._logger.debug(f'{self.channel=} != {self._parent.channel=}, not stopping')
            return False
        self.stopTimer(self.threads.get('timer', None), event=self.timer_event)
        self.setPower(0, **kwargs)
        return
    
    def getPower(self) -> int:
        """
        Get the current power level of the LED
        
        Returns:
            int: power level
        """
        return self.target_power
    
    def setPower(self, power: int, event: threading.Event|None = None, **kwargs) -> bool:
        """
        Set power level of LED
        
        Args:
            power (int): power level
            event (threading.Event, optional): event to set. Defaults to None.
            
        Returns:
            bool: whether the power level was set
        """
        channel = kwargs.get('channel', self.channel)
        if isinstance(channel,int):
            self._parent.channel = channel
        if self.channel != self._parent.channel:
            self._logger.debug(f'{self.channel=} != {self._parent.channel=}, not setting power')
            return False
        ret = self.setTargetPower(power)
        self.updatePower()
        if isinstance(event, threading.Event):
            _ = event.clear() if event.is_set() else event.set()
        return ret
    
    def setTargetPower(self, power: int) -> bool:
        """
        Set power level of LED
        
        Args:
            power (int): power level
            
        Returns:
            bool: whether the power level was set
        """
        if self.channel != self._parent.channel:
            self._logger.debug(f'{self.channel=} != {self._parent.channel=}, not setting target power')
            return False
        assert power >= 0, "Ensure the power level is a non-negative number"
        if self.timer_event.is_set() and power != 0:
            self._logger.info(f"[BUSY] LED {self.channel} is currently in use")
            return False
        self._logger.info(f"[LED {self.channel}] {power}")
        self.target_power = power
        return True
    
    def setValue(self, value: int, event: threading.Event|None = None, **kwargs) -> bool:
        """ 
        Set the power level of the LED
        
        Args:
            value (int): power level
            event (threading.Event, optional): event to set. Defaults to None.
            
        Returns:
            bool: whether the power level was set
        """
        return self.setPower(value, event, **kwargs)
    
    def updatePower(self):
        """Update the power level of the LED"""
        channel = self._parent.channel
        all_power = self._parent.getPower()
        self._parent.channel = channel
        if isinstance(all_power, dict):
            all_power = list(all_power.values())
        all_power = all_power if isinstance(all_power, list) else [all_power]
        data = ';'.join([str(v) for v in all_power])
        self.device.clearDeviceBuffer()
        self.device.query(data, multi_out=False)
        return
    
    # Overwritten method(s)
    def execute(self, dark_time:int|float = 0, power:int = 255, light_time:int|float = 1, blocking:bool = True, *args, **kwargs):
        """
        Execute the dark and light steps

        Args:
            dark_time (int, optional): dark time. Defaults to 0.
            power (int, optional): power level. Defaults to 255.
            light_time (int, optional): light time. Defaults to 1.
            blocking (bool, optional): whether to block the thread. Defaults to True.
        """
        if self.channel != self._parent.channel:
            return False
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
Multi_LED.updatePower = LED.updatePower
