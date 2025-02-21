# -*- coding: utf-8 -*-
# Standard library imports
from __future__ import annotations
from datetime import datetime
import logging
import time
from typing import NamedTuple, Iterable

# Third party imports
import pandas as pd

# Local application imports
from ...core import datalogger
from ..measure import Measurer

logger = logging.getLogger(__name__)
logger.debug(f"Import: OK <{__name__}>")

READ_FORMAT = "{value}\n"
ValueData = NamedTuple('ValueData', [('value', int)])

class LoadCell(Measurer):
    
    def __init__(self,
        port: str,
        stabilize_timeout: float = 1, 
        force_tolerance: float = 0.01, 
        *, 
        calibration_factor: float = 1.0,
        correction_parameters: tuple[float] = (1.0,0.0),
        baudrate: int = 9600,
        verbose: bool = False, 
        **kwargs
    ):
        defaults = dict(
            init_timeout=3, 
            data_type=ValueData, 
            read_format=READ_FORMAT, 
        )
        defaults.update(kwargs)
        kwargs = defaults
        super().__init__(
            port=port, baudrate=baudrate, 
            verbose=verbose, **kwargs
        )
        
        self.force_tolerance = force_tolerance
        self.stabilize_timeout = stabilize_timeout
        self._stabilize_start_time = None
        
        self.baseline = 0
        self.calibration_factor = calibration_factor        # counts per unit force
        self.correction_parameters = correction_parameters  # polynomial correction parameters, starting with highest order
        return
    
    def connect(self):
        super().connect()
        if not self.is_connected:
            return
        self.device.clear()
        while True:
            time.sleep(0.1)
            out = self.device.query(None,multi_out=False)
            if out is not None:
                break
        return
    
    def getAttributes(self) -> dict:
        relevant = ['correction_parameters', 'baseline', 'calibration_factor', 'force_tolerance', 'stabilize_timeout']
        return {key: getattr(self, key) for key in relevant}
    
    def getData(self, *args, **kwargs) -> ValueData|None:
        """
        Get data from device
        """
        return super().getData(*args, **kwargs)
    
    def getDataframe(self, data_store: Iterable[NamedTuple, datetime]) -> pd.DataFrame:
        df = datalogger.get_dataframe(data_store=data_store, fields=self.device.data_type._fields)
        df['corrected_value'] = df['value'].apply(self._correct_value)
        df['force'] = df['corrected_value'].apply(self._calculate_force)
        return df
    
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
    
    def reset(self):
        super().reset()
        self.baseline = 0
        return
    
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
        self.baseline = sum([d[0] for d,_ in self.buffer])/len(self.buffer)
        self.device.stopStream()
        self.buffer.clear()
        return
    
    def _calculate_force(self, value: float) -> float:
        return (value-self.baseline)/self.calibration_factor
    
    def _correct_value(self, value: float) -> float:
        return sum([param * (value**i) for i,param in enumerate(self.correction_parameters[::-1])])
    