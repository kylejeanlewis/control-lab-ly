# -*- coding: utf-8 -*-
# Standard Library imports
from __future__ import annotations
import threading
import time

# Local application imports
from ...core.compound import Ensemble
from ...core.device import TimedDeviceMixin
from .. import Maker

class Spinner(Maker, TimedDeviceMixin):
    def __init__(self, port: str, *, baudrate: int = 9600, verbose = False, **kwargs):
        super().__init__(port=port, baudrate=baudrate, verbose=verbose, **kwargs)
        
        self.target_rpm = 0
        self.timer_event = threading.Event()
        self.threads = dict()
        return
    
    def soak(self, duration: int|float, blocking: bool = True):
        return self.spin(0, duration, blocking)
    
    def spin(self, rpm: int, duration: int|float, blocking: bool = True):
        """
        Spin the spinner at a given speed
        
        Args:
            `rpm` (int): spin speed in rpm
        """
        timer = self.onState(rpm, duration, blocking, event=self.timer_event)
        if isinstance(timer, threading.Timer):
            self.threads['timer'] = timer
        # assert rpm >= 0, "Ensure the spin speed is a non-negative number"
        # assert duration >= 0, "Ensure the spin time is a non-negative number"
        # success = self.setSpinSpeed(rpm)
        # if not success:
        #     return
        # self.timer_event.set()
        # if blocking:
        #     time.sleep(duration)
        #     self.stop()
        #     return
        # timer = threading.Timer(duration, self.setSpinSpeed, args=(0,self.timer_event))
        # timer.start()
        # self.threads['timer'] = timer
        return
    
    def stop(self):
        """
        Stop the spinner
        """
        self.stopTimer(self.threads.get('timer', None), event=self.timer_event)
        # self.setSpinSpeed(0)
        # if 'timer' in self.threads and isinstance(self.threads['timer'] , threading.Timer):
        #     self.threads['timer'].cancel()
        # self.timer_event.clear()
        return
    
    def setSpinSpeed(self, rpm: int, event: threading.Event|None = None) -> bool:
        """
        Set the spin speed in rpm
        
        Args:
            `rpm` (int): spin speed in rpm
        """
        assert rpm >= 0, "Ensure the spin speed is a non-negative number"
        if self.timer_event.is_set() and rpm != 0:
            self._logger.info("[BUSY] Spinner is currently in use")
            return False
        self._logger.info(f"[SPIN] {rpm}")
        self.device.query(rpm)
        self.target_rpm = rpm
        if isinstance(event, threading.Event):
            _ = event.clear() if event.is_set() else event.set()
        return True
    
    def setValue(self, value: int, event: threading.Event|None = None) -> bool:
        return self.setSpinSpeed(value, event)
    
    # Overwritten method(s)
    def execute(self, soak_time:int|float = 0, spin_speed:int = 2000, spin_time:int|float = 1, blocking:bool = True, *args, **kwargs):
        """
        Execute the soak and spin steps

        Args:
            soak_time (int, optional): soak time. Defaults to 0.
            spin_speed (int, optional): spin speed. Defaults to 2000.
            spin_time (int, optional): spin time. Defaults to 1.
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
