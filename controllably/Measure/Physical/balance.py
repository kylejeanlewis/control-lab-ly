# -*- coding: utf-8 -*-
# Standard library imports
from __future__ import annotations
import logging

# Third party imports
import pandas as pd

# Local application 
from ...core import datalogger
from ..Mechanical.load_cell import LoadCell, ValueData

logger = logging.getLogger(__name__)
logger.debug(f"Import: OK <{__name__}>")

G = 9.81

class Balance(LoadCell):
    def __init__(self,
        port: str,
        stabilize_timeout: float = 10, 
        force_tolerance: float = 1.5, 
        mass_tolerance: float = 0.15,
        *, 
        calibration_factor: float = 1.0,
        correction_parameters: tuple[float] = (1.0,0.0),
        baudrate: int = 9600,
        verbose: bool = False, 
        **kwargs
    ):
        super().__init__(
            port=port, baudrate=baudrate, verbose=verbose, 
            stabilize_timeout=stabilize_timeout, force_tolerance=force_tolerance,
            calibration_factor=calibration_factor, 
            correction_parameters=correction_parameters,
            **kwargs
        )
        self.mass_tolerance = mass_tolerance
        return
    
    @property
    def buffer_df(self) -> pd.DataFrame:
        return self._get_dataframe(self.buffer)
    
    @property
    def records_df(self) -> pd.DataFrame:
        return self._get_dataframe(self.records)
    
    def atMass(self, mass: float) -> float:
        return self.atForce(mass*G, tolerance=self.mass_tolerance*G)
    
    def getMass(self) -> float:
        data = self.getForce()
        if data is None:
            return None
        return self._calculate_mass(data)
    
    def tare(self, wait: float = 5.0):
        return self.zero(wait=wait)
    
    def _calculate_force(self, value: float) -> float:
        return (value-self.baseline)/self.calibration_factor
    
    def _calculate_mass(self, value: float) -> float:
        return self._calculate_force(value) / G
    
    def _correct_value(self, value: float) -> float:
        return sum([param * (value**i) for i,param in enumerate(self.correction_parameters[::-1])])
    
    def _get_dataframe(self, data_store: list[ValueData]) -> pd.DataFrame:
        df = datalogger.get_dataframe(data_store=data_store, fields=self.device.data_type._fields)
        df['corrected_value'] = df['value'].apply(self._correct_value)
        df['force'] = df['corrected_value'].apply(self._calculate_force)
        df['mass'] = df['corrected_value'].apply(self._calculate_mass)
        return df
    