# -*- coding: utf-8 -*-
""" 
This module holds the Peltier class.

Attributes:
    MAX_LEN (int): maximum length of buffer
    READ_FORMAT (str): read format
    TempData (NamedTuple): temperature data

## Classes:
    `Peltier`: Peltier class
    
<i>Documentation last updated: 2025-02-22</i>
"""
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
from ...core import datalogger
from .. import Maker
from .heater_mixin import HeaterMixin

MAX_LEN = 100
READ_FORMAT = "{target};{temperature};{cold};{power}\n"
TempData = NamedTuple('TempData', [('target',float),('temperature',float),('cold',float),('power',float)])

class Peltier(HeaterMixin, Maker):
    """
    Peltier class
    
    ### Constructor:
        `port` (str): port
        `power_threshold` (float, optional): power threshold. Defaults to 20.
        `stabilize_timeout` (float, optional): stabilize timeout. Defaults to 10.
        `tolerance` (float, optional): tolerance. Defaults to 1.5.
        `baudrate` (int, optional): baudrate. Defaults to 115200.
        `verbose` (bool, optional): verbosity. Defaults to False.
        
    ### Attributes and properties:
        `buffer` (deque[tuple[NamedTuple, datetime]]): buffer data
        `records` (deque[tuple[NamedTuple, datetime]]): records data
        `record_event` (threading.Event): record event
        `tolerance` (float): tolerance
        `power_threshold` (float): power threshold
        `stabilize_timeout` (float): stabilize timeout
        `buffer_df` (pd.DataFrame): buffer data as DataFrame
        `records_df` (pd.DataFrame): records data as DataFrame
        
    ### Methods:
        `clearCache`: clear data cache
        `getData`: get data from device
        `record`: record data
        `stream`: stream data
        `connect`: connect to device
        `reset`: reset device
        `atTemperature`: check if at temperature
        `getTemperature`: get temperature
        `setTemperature`: set temperature
        `disconnect`: disconnect from the device
        `execute`: execute task
        `resetFlags`: reset all flags to class attribute `_default_flags`
        `run`: alias for `execute()`
        `shutdown`: shutdown procedure for tool
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
        """
        Initialize the class
        
        Args:
            port (str): port
            power_threshold (float, optional): power threshold. Defaults to 20.
            stabilize_timeout (float, optional): stabilize timeout. Defaults to 10.
            tolerance (float, optional): tolerance. Defaults to 1.5.
            baudrate (int, optional): baudrate. Defaults to 115200.
            verbose (bool, optional): verbosity. Defaults to False.
        """
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
        """Buffer data as DataFrame"""
        return datalogger.get_dataframe(data_store=self.buffer, fields=self.device.data_type._fields)
    
    @property
    def records_df(self) -> pd.DataFrame:
        """Records data as DataFrame"""
        return datalogger.get_dataframe(data_store=self.records, fields=self.device.data_type._fields)
        
    def connect(self):
        super().connect()
        self._logger.info(f"Current temperature: {self.getTemperature()}°C")
        return
    
    def reset(self):
        """Reset device"""
        self.clearCache()
        self.setTemperature(25, blocking=False)
        return
    
    # Data logging methods
    def clearCache(self):
        """Clear data cache"""
        self.buffer.clear()
        self.records.clear()
        return
    
    def getData(self, *args, **kwargs) -> TempData|None:
        """
        Get data from device
        
        Returns:
            TempData: data from device
        """
        if not self.device.stream_event.is_set():
            return self.device.query(None, multi_out=False)
        
        data_store = self.records if self.record_event.is_set() else self.buffer
        out = data_store[-1] if len(data_store) else None
        data,_ = out if out is not None else (None,None)
        return data
    
    def record(self, on: bool, show: bool = False, clear_cache: bool = False):
        """ 
        Record data
        
        Args:
            on (bool): record data
            show (bool, optional): print data. Defaults to False.
            clear_cache (bool, optional): clear cache. Defaults to False.
        """
        return datalogger.record(
            on=on, show=show, clear_cache=clear_cache, data_store=self.records, 
            device=self.device, event=self.record_event
        )
    
    def stream(self, on: bool, show: bool = False):
        """ 
        Stream data
        
        Args:
            on (bool): stream data
            show (bool, optional): print data. Defaults to False.
        """
        return datalogger.stream(
            on=on, show=show, data_store=self.buffer, 
            device=self.device, event=self.record_event
        )
    
    # Temperature control methods
    def atTemperature(self, 
        temperature: float|None = None, 
        *, 
        tolerance: float|None = None,
        power_threshold: float|None = None,
        stabilize_timeout: float|None = None
    ) -> bool:
        """
        Check if at temperature
        
        Args:
            temperature (float, optional): target temperature. Defaults to None.
            tolerance (float, optional): tolerance. Defaults to None.
            power_threshold (float, optional): power threshold. Defaults to None.
            stabilize_timeout (float, optional): stabilize timeout. Defaults to None.
            
        Returns:
            bool: at temperature
        """
        data = self.getData()
        if data is None:
            return False
        temperature = temperature if temperature is not None else data.target
        tolerance = tolerance or self.tolerance
        power_threshold = power_threshold or self.power_threshold
        stabilize_timeout = stabilize_timeout if stabilize_timeout is not None else self.stabilize_timeout
        if abs(data.temperature - temperature) > tolerance:
            self._stabilize_start_time = None
            return False
        self._stabilize_start_time = self._stabilize_start_time or time.perf_counter()
        if ((time.perf_counter()-self._stabilize_start_time) < stabilize_timeout):
            return False
        if data.power > power_threshold:
            return False
        return True
    
    def getTemperature(self) -> float|None:
        """
        Get temperature
        
        Returns:
            float: temperature
        """
        data = self.getData()
        if data is None:
            return None
        return data.temperature
    
    def _set_temperature(self, temperature: float):
        """ 
        Set temperature
        
        Args:
            temperature (float): target temperature
        """
        self.device.write(self.device.processInput(temperature))
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
        return
    