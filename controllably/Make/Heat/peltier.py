# -*- coding: utf-8 -*-
# Standard Library imports
from __future__ import annotations
from collections import deque
from datetime import datetime
import threading
import time
from typing import NamedTuple

# Third party imports
import pandas as pd

# Local application imports
from ...core.device import DataLoggerUtils
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
        super().__init__(
            port=port, baudrate=baudrate, verbose=verbose, 
            read_format=READ_FORMAT, data_type=TempData, **kwargs
        )
        
        # Data logging attributes
        self.buffer: deque[tuple[NamedTuple, datetime]] = deque(maxlen=MAX_LEN)
        self.records: deque[tuple[NamedTuple, datetime]] = deque()
        self.record_event = threading.Event()
        
        # Temperature control attributes
        self.tolerance = tolerance
        self.power_threshold = power_threshold
        self.stabilize_timeout = stabilize_timeout
        self._stabilize_start_time = None
        
        self.connect()
        return
    
    # Data logging properties
    @property
    def buffer_df(self) -> pd.DataFrame:
        return DataLoggerUtils.getDataframe(data_store=self.buffer, fields=self.device.data_type._fields)
    
    @property
    def records_df(self) -> pd.DataFrame:
        return DataLoggerUtils.getDataframe(data_store=self.records, fields=self.device.data_type._fields)
    
    # Temperature control properties
    @property
    def at_temperature(self) -> bool:
        ret = self.atTemperature(None)
        if ret is None:
            return False
        return ret
    
    def connect(self):
        super().connect()
        self._logger.info(f"Current temperature: {self.getTemperature()}°C")
        return
    
    def reset(self):
        self.clearCache()
        self.setTemperature(25, blocking=False)
        return
    
    # Data logging methods
    def clearCache(self):
        self.buffer = deque(maxlen=MAX_LEN)
        self.records = deque()
        return
    
    def getData(self) -> TempData|None:
        """
        Get data from device
        """
        data_store = self.records if self.record_event.is_set() else self.buffer
        return DataLoggerUtils.getData(data_store=data_store, device=self.device)
    
    def record(self, on: bool, show: bool = False, clear_cache: bool = False):
        return DataLoggerUtils.record(
            on=on, show=show, clear_cache=clear_cache, data_store=self.records, 
            device=self.device, event=self.record_event
        )
    
    def stream(self, on: bool, show: bool = False):
        return DataLoggerUtils.stream(
            on=on, show=show, data_store=self.buffer, 
            device=self.device, event=self.record_event
        )
    
    # Temperature control methods
    def atTemperature(self, 
        temperature: float|None, 
        *, 
        tolerance: float|None = None,
        power_threshold: float|None = None,
        stabilize_timeout: float|None = None
    ) -> bool:
        data = self.getData()
        if data is None:
            return False
        temperature = temperature if temperature is not None else data.target
        tolerance = tolerance or self.tolerance
        power_threshold = power_threshold or self.power_threshold
        stabilize_timeout = stabilize_timeout if stabilize_timeout is not None else self.stabilize_timeout
        if abs(data.temperature - temperature) > tolerance:
            return False
        if (time.perf_counter()-self._stabilize_start_time) < stabilize_timeout:
            return False
        if data.power > power_threshold:
            return False
        return True
    
    def getTemperature(self) -> float|None:
        """
        Get temperature
        """
        data = self.getData()
        if data is None:
            return None
        return data.temperature
    
    def _set_temperature(self, temperature: float):
        buffer = self.records if self.record_event.is_set() else self.buffer
        if not self.device.stream_event.is_set():
            self.device.startStream(buffer=buffer)
            time.sleep(0.1)
        while True:
            data = self.getData()
            if data is None:
                time.sleep(0.01)
                continue
            if data.target == temperature:
                break
            time.sleep(0.01)
        self._stabilize_start_time = time.perf_counter()
        return
    