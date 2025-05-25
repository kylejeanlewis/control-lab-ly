# -*- coding: utf-8 -*-
""" 
This module provides a class for the Sentron pH meter.

Attributes:
    MAX_LEN (int): Maximum length of the data buffer
    READ_FORMAT (str): Format for reading data
    pHData (NamedTuple): NamedTuple for pH data
    
## Classes:
    `SI600`: Sentron pH meter class
    
<i>Documentation last updated: 2025-02-22</i>
"""
# Standard library imports
from __future__ import annotations
import time
from typing import NamedTuple

# Local application imports
from ....core import datalogger
from ...measure import Measurer

MAX_LEN = 100
READ_FORMAT = "{yymmdd} {hhmmss} {sample}  {pH}  {temperature}\n"
pHData = NamedTuple('pHData', [('yymmdd',str),('hhmmss',str),('pH',float),('temperature',float), ('sample',str)])

class SI600(Measurer):
    """
    Sentron pH meter
    
    ### Constructor:
        `port` (str): Serial port
        `stabilize_timeout` (float): Time to wait for the device to stabilize
        `pH_tolerance` (float): Tolerance for pH
        `temp_tolerance` (float): Tolerance for temperature
        `baudrate` (int): Baudrate for serial communication
        `verbose` (bool): Print verbose output
        
    ### Attributes and properties:
        `pH_tolerance` (float): Tolerance for pH
        `temp_tolerance` (float): Tolerance for temperature
        `stabilize_timeout` (float): Time to wait for the device to stabilize
        `buffer` (deque): data buffer for the device
        `buffer_df` (pd.DataFrame): data buffer as a DataFrame
        `records` (deque): records for the device
        `records_df` (pd.DataFrame): records as a DataFrame
        `record_event` (threading.Event): event for recording data
        `program` (Program): program to run
        `runs` (dict): dictionary of runs
        `n_runs` (int): number of runs
        `connection_details` (dict): connection details for the device
        `device` (Device): device object that communicates with physical tool
        `flags` (SimpleNamespace[str, bool]): flags for the class
        `is_busy` (bool): whether the device is busy
        `is_connected` (bool): whether the device is connected
        `verbose` (bool): verbosity of class
        
    ### Methods:
        `getData`: Get pH and temperature data
        `atPH`: Check if the device is at the target pH
        `atTemperature`: Check if the device is at the target temperature
        `getPH`: Get pH
        `getTemperature`: Get temperature
        `record`: Record data
        `stream`: Stream data
        `connect`: connect to the device
        `disconnect`: disconnect from the device
        `execute`: execute task
        `resetFlags`: reset all flags to class attribute `_default_flags`
        `run`: alias for `execute()`
        `shutdown`: shutdown procedure for the device
    """
    
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
        """ 
        Initialize the Sentron pH meter
        
        Args:
            port (str): Serial port
            stabilize_timeout (float): Time to wait for the device to stabilize
            pH_tolerance (float): Tolerance for pH
            temp_tolerance (float): Tolerance for temperature
            baudrate (int): Baudrate for serial communication
            verbose (bool): Print verbose output
        """
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
        Get pH and temperature data
        
        Returns:
            pHData: pH and temperature data
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
        
        Args:
            pH (float): Target pH
            tolerance (float): Tolerance for pH
            stabilize_timeout (float): Time to wait for the device to stabilize
            
        Returns:
            bool: True if the device is at the target pH
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
        
        Args:
            temperature (float): Target temperature
            tolerance (float): Tolerance for temperature
            stabilize_timeout (float): Time to wait for the device to stabilize
            
        Returns:
            bool: True if the device is at the target temperature
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
        Get pH
        
        Returns:
            float: pH
        """
        data = self.getData()
        if data is None:
            return None
        return data.pH
    
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
        