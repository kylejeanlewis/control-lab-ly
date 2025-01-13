# Standard Library imports
from __future__ import annotations
from collections import deque
from datetime import datetime
import time
from typing import NamedTuple

# Third party imports
import pandas as pd

# Local application imports
from .. import Maker
from .heater_mixin import HeaterMixin

MAX_LEN = 100
READ_FORMAT = "{target};{temperature};{cold};{power}\n"
TempData = NamedTuple('TempData', [('target',float),('temperature',float),('cold',float),('power',float)])

class Peltier(Maker, HeaterMixin):
    """
    Class for Peltier control
    """
    
    def __init__(self, 
        port: str, 
        power_threshold: float = 20,
        stabilize_timeout: float = 10, 
        tolerance: float = 1.5, 
        *,
        baudrate: int = 115200,
        verbose: bool = False,
        **kwargs
    ):
        super().__init__(port=port, baudrate=baudrate, verbose=verbose, **kwargs)
        self.buffer: deque[tuple[TempData, datetime]] = deque(maxlen=MAX_LEN)
        
        self.tolerance = tolerance
        self.power_threshold = power_threshold
        self.stabilize_timeout = stabilize_timeout
        self._stabilize_start_time = None
        
        self.connect()
        return
    
    @property
    def at_temperature(self) -> bool:
        out: tuple[TempData, datetime] = self.buffer[-1] if self.device.stream_event.is_set() else self.device.query(None)
        data, _ = out
        return self.atTemperature(data.target)
    
    @property
    def buffer_df(self) -> pd.DataFrame:
        data,timestamps = list([x for x in zip(*self.buffer)])
        return pd.DataFrame(data, index=timestamps).reset_index(names='timestamp')
    
    def __del__(self):
        return
    
    def connect(self):
        super().connect()
        self._logger.info(f"Current temperature: {self.getTemperature()}°C")
        return
    
    def clearCache(self):
        self.buffer = deque(maxlen=MAX_LEN)
        return
    
    def reset(self):
        self.clearCache()
        self.setTemperature(25, blocking=False)
        return
    
    def record(self, on: bool):
        self.device.stopStream()
        time.sleep(0.1)
        if on:
            if self.buffer.maxlen is not None:
                self.buffer = deque(self.buffer)
            self.device.startStream(buffer=self.buffer)
        return
    
    def stream(self, on: bool, show: bool = False):
        _ = self.device.startStream(buffer=self.buffer) if on else self.device.stopStream()
        self.device.showStream(show)
        return
    
    def atTemperature(self, temperature: float, *, tolerance: float|None = None) -> bool:
        out: tuple[TempData, datetime] = self.buffer[-1] if self.device.stream_event.is_set() else self.device.query(None)
        data, _ = out
        
        tolerance = tolerance or self.tolerance
        if abs(data.temperature - temperature) <= tolerance:
            return True
        if data.power <= self.power_threshold:
            return True
        if time.perf_counter()-self._stabilize_start_time >= self.stabilize_timeout:
            return True
        return False
    
    def getTemperature(self) -> float:
        """
        Get temperature
        """
        out: tuple[TempData, datetime] = self.buffer[-1] if self.device.stream_event.is_set() else self.device.query(None)
        data, _ = out
        return data.temperature
    
    def _set_temperature(self, temperature: float):
        self.device.query(temperature)
        if not self.device.stream_event.is_set():
            self.device.startStream(buffer=self.buffer)
        while True:
            out: tuple[TempData, datetime] = self.buffer[-1] if self.device.stream_event.is_set() else self.device.query(None)
            data, _ = out
            if data.target == temperature:
                break
            time.sleep(0.01)
        return
    