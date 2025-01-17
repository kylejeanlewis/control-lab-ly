# -*- coding: utf-8 -*-
# Standard Library imports
from __future__ import annotations
import threading
import time

# Local application imports
from ...core.compound import Multichannel
from ...core.device import TimedDeviceMixin
from .. import Maker

class LED(Maker, TimedDeviceMixin):
    def __init__(self, port: str, *, baudrate: int = 9600, verbose = False, **kwargs):
        super().__init__(port=port, baudrate=baudrate, verbose=verbose, **kwargs)
        
        self.target_power = 0
        self.timer_event = threading.Event()
        self.threads = dict()
        return
    
    def getAttributes(self):
        relevant = ['targer_power', 'timer_event', 'threads']
        return {key: getattr(self, key) for key in relevant}
    
    def dark(self, duration: int|float, blocking: bool = True):
        return self.light(0, duration, blocking)
    
    def light(self, power: int, duration: int|float, blocking: bool = True):
        """
        Light up the LED at a given power level for a given duration
        
        Args:
            `power` (int): power level
        """
        timer = self.onState(power, duration, blocking, event=self.timer_event)
        if isinstance(timer, threading.Timer):
            self.threads['timer'] = timer
        return
    
    def stop(self):
        """
        Stop the LED from emitting light
        """
        self.stopTimer(self.threads.get('timer', None), event=self.timer_event)
        return
    
    def setPower(self, power: int, event: threading.Event|None = None) -> bool:
        """
        Set power level of LED
        
        Args:
            `power` (int): power level
        """
        assert power >= 0, "Ensure the power level is a non-negative number"
        if self.timer_event.is_set() and power != 0:
            self._logger.info("[BUSY] LED is currently in use")
            return False
        self._logger.info(f"[LED] {power}")
        self.device.query(power)
        self.target_power = power
        if isinstance(event, threading.Event):
            _ = event.clear() if event.is_set() else event.set()
        return True
    
    def setValue(self, value: int, event: threading.Event|None = None) -> bool:
        return self.setPower(value, event)
    
    # Overwritten method(s)
    def execute(self, dark_time:int|float = 0, power:int = 255, light_time:int|float = 1, blocking:bool = True, *args, **kwargs):
        """
        Execute the dark and spin steps

        Args:
            dark_time (int, optional): dark time. Defaults to 0.
            power (int, optional): power level. Defaults to 255.
            light_time (int, optional): spin time. Defaults to 1.
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
        if 'timer' in self.threads and isinstance(self.threads['timer'], threading.Timer):
            self.threads['timer'].cancel()
        for thread in self.threads.values():
            if isinstance(thread, threading.Thread):
                thread.join()
        self.disconnect()
        self.resetFlags()
        return super().shutdown()

Multi_LED = Multichannel.factory(LED)
