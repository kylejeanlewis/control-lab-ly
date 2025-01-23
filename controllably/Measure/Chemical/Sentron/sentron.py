# -*- coding: utf-8 -*-
# Standard library imports
from __future__ import annotations
import logging
import time
from typing import NamedTuple

# Local application imports
from ....core import datalogger
from ...measure import Measurer

logger = logging.getLogger(__name__)
logger.debug(f"Import: OK <{__name__}>")

MAX_LEN = 100
READ_FORMAT = "{yymmdd} {hhmmss} {sample}  {pH}  {temperature}\n"
pHData = NamedTuple('pHData', [('yymmdd',str),('hhmmss',str),('pH',float),('temperature',float), ('sample',str)])

class SI600(Measurer):
    
    def __init__(self,
        port: str,
        stabilize_timeout: float = 10, 
        pH_tolerance: float = 1.5, 
        temp_tolerance: float = 1.5, 
        *, 
        baudrate: int = 9600,
        verbose: bool = False, 
        **kwargs
    ):
        super().__init__(
            port=port, baudrate=baudrate, verbose=verbose, 
            read_format=READ_FORMAT, data_type=pHData, **kwargs
        )
        
        self.pH_tolerance = pH_tolerance
        self.temp_tolerance = temp_tolerance
        self.stabilize_timeout = stabilize_timeout
        self._stabilize_start_time = None
        return
    
    def getData(self, *args, **kwargs) -> pHData|None:
        """
        Get data from device
        """
        return super().getData(query='ACT', *args, **kwargs)
    
    def atPH(self, 
        pH: float, 
        *, 
        tolerance: float|None = None,
        stabilize_timeout: float = 0
    ) -> bool:
        """
        Check if the device is at the target pH
        """
        data = self.getData()
        if data is None:
            return False
        
        tolerance = tolerance or self.pH_tolerance
        stabilize_timeout = stabilize_timeout or self.stabilize_timeout
        if abs(data.pH - pH) > tolerance:
            self._stabilize_start_time = None
            return False
        self._stabilize_start_time = self._stabilize_start_time or time.perf_counter()
        if ((time.perf_counter()-self._stabilize_start_time) < stabilize_timeout):
            return False
        return True
    
    def atTemperature(self, 
        temperature: float, 
        *, 
        tolerance: float|None = None,
        stabilize_timeout: float = 0
    ) -> bool:
        """
        Check if the device is at the target temperature
        """
        data = self.getData()
        if data is None:
            return False
        
        tolerance = tolerance or self.temp_tolerance
        stabilize_timeout = stabilize_timeout or self.stabilize_timeout
        if abs(data.temperature - temperature) > tolerance:
            self._stabilize_start_time = None
            return False
        self._stabilize_start_time = self._stabilize_start_time or time.perf_counter()
        if ((time.perf_counter()-self._stabilize_start_time) < stabilize_timeout):
            return False
        return True
    
    def getPH(self) -> float|None:
        """
        Get temperature
        """
        data = self.getData()
        if data is None:
            return None
        return data.pH
    
    def getTemperature(self) -> float|None:
        """
        Get temperature
        """
        data = self.getData()
        if data is None:
            return None
        return data.temperature
    
    def record(self, on: bool, show: bool = False, clear_cache: bool = False):
        return datalogger.record(
            on=on, show=show, clear_cache=clear_cache, 
            query='ACT', data_store=self.records, 
            device=self.device, event=self.record_event
        )
    
    def stream(self, on: bool, show: bool = False):
        return datalogger.stream(
            on=on, show=show, data_store=self.buffer, query='ACT',
            device=self.device, event=self.record_event
        )
        