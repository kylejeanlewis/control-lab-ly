# -*- coding: utf-8 -*-
# Standard library imports
from __future__ import annotations
import logging
import time
from typing import NamedTuple

# Third party imports
import pandas as pd

# Local application imports
from ...core import datalogging
from ..measure import Measurer

logger = logging.getLogger(__name__)
logger.debug(f"Import: OK <{__name__}>")

MAX_LEN = 100
READ_FORMAT = "{value}\r\n"
ValueData = NamedTuple('ValueData', [('value', float)])

class LoadCell(Measurer):
    
    def __init__(self,
        port: str,
        stabilize_timeout: float = 10, 
        force_tolerance: float = 1.5, 
        *, 
        calibration_factor: float = 1.0,
        correction_parameters: tuple[float] = (1.0,0.0),
        baudrate: int = 9600,
        verbose: bool = False, 
        **kwargs
    ):
        super().__init__(port=port, baudrate=baudrate, verbose=verbose, **kwargs)
        
        self.force_tolerance = force_tolerance
        self.stabilize_timeout = stabilize_timeout
        self._stabilize_start_time = None
        
        self.baseline = 0
        self.calibration_factor = calibration_factor        # counts per unit force
        self.correction_parameters = correction_parameters  # polynomial correction parameters, starting with highest order
        return
    
    @property
    def buffer_df(self) -> pd.DataFrame:
        df = datalogging.getDataframe(data_store=self.buffer, fields=self.device.data_type._fields)
        df['corrected_value'] = df['value'].apply(self._correct_value)
        df['force'] = df['corrected_value'].apply(self._calculate_force)
        return df
    
    @property
    def records_df(self) -> pd.DataFrame:
        df = datalogging.getDataframe(data_store=self.records, fields=self.device.data_type._fields)
        df['corrected_value'] = df['value'].apply(self._correct_value)
        df['force'] = df['corrected_value'].apply(self._calculate_force)
        return df
    
    @property
    def _parameters(self) -> dict:
        return {
            'correction_parameters': self.correction_parameters,
            'baseline': self.baseline,
            'calibration_factor': self.calibration_factor,
            'tolerance': self.force_tolerance,
            'stabilize_timeout': self.stabilize_timeout
        }
    
    def getData(self, *args, **kwargs) -> ValueData|None:
        """
        Get data from device
        """
        return super().getData(*args, **kwargs)
    
    def atForce(self, 
        force: float, 
        *, 
        tolerance: float|None = None,
        stabilize_timeout: float = 0
    ) -> bool:
        """
        Check if the device is at the target temperature
        """
        force_actual = self.getForce()
        if force_actual is None:
            return False
        
        tolerance = tolerance or self.force_tolerance
        stabilize_timeout = stabilize_timeout or self.stabilize_timeout
        if abs(force_actual - force) > tolerance:
            self._stabilize_start_time = None
            return False
        self._stabilize_start_time = self._stabilize_start_time or time.perf_counter()
        if ((time.perf_counter()-self._stabilize_start_time) < stabilize_timeout):
            return False
        return True
    
    def getForce(self) -> float|None:
        """
        Get force
        """
        data = self.getValue()
        if data is None:
            return None
        return self._calculate_force(data)
    
    def getValue(self) -> float|None:
        """
        Get temperature
        """
        data = self.getData()
        if data is None:
            return None
        return self._correct_value(data.value)
    
    def zero(self, wait: float = 5.0):
        """
        Set current reading as baseline
        """
        self.record_event.clear()
        self.buffer.clear()
        if not self.device.stream_event.is_set():
           self.device.startStream(buffer=self.buffer)
        while not len(self.buffer) == 100:
            time.sleep(0.1)
        time.sleep(wait)
        self.baseline = sum([d[0] for d in self.buffer])/len(self.buffer)
        return
    
    def _calculate_force(self, value: float) -> float:
        return (value-self.baseline)/self.calibration_factor
    
    def _correct_value(self, value: float) -> float:
        return sum([param * (value**i) for i,param in enumerate(self.correction_parameters[::-1])])
    