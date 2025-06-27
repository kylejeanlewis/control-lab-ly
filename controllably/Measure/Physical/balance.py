# -*- coding: utf-8 -*-
""" 
This module provides a class for the balance.

Attributes:
    G (float): Acceleration due to gravity
    
## Classes:
    `Balance`: Balance class
    
<i>Documentation last updated: 2025-02-22</i>
"""

# Standard library imports
from __future__ import annotations
from datetime import datetime
from typing import NamedTuple, Iterable

# Third party imports
import pandas as pd

# Local application 
from ...core import datalogger
from ..Mechanical.load_cell import LoadCell

G = 9.81

class Balance(LoadCell):
    """ 
    Balance class for interfacing with a balance.
    
    ### Constructor:
        `port` (str): The port to connect to.
        `stabilize_timeout` (float): The time to wait for the balance to stabilize.
        `force_tolerance` (float): The tolerance for the force measurement.
        `mass_tolerance` (float): The tolerance for the mass measurement
        `calibration_factor` (float): The calibration factor for the balance.
        `correction_parameters` (tuple[float]): The correction parameters for the balance.
        `baudrate` (int): The baudrate for the balance.
        `verbose` (bool): The verbosity of the balance.
        
    ### Attributes and properties:
        `mass_tolerance` (float): The tolerance for the mass measurement.
        `force_tolerance` (float): Tolerance for force
        `stabilize_timeout` (float): Time to wait for the device to stabilize
        `baseline` (int): Baseline value
        `calibration_factor` (float): counts per unit force
        `correction_parameters` (tuple[float]): polynomial correction parameters, starting with highest order
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
        
    ### Methods:
        `connect`: Connect to the device
        `getDataframe`: Get a DataFrame from the data store
        `atMass`: Check if the balance is at a specific mass
        `getMass`: Get the mass measured by the balance
        `tare`: Tare the balance
        `getAttributes`: Get attributes
        `getData`: Get data from device
        `atForce`: Check if the device is at the target force
        `getForce`: Get force
        `getValue`: Get value
        `reset`: Reset the device
        `zero`: Set current reading as baseline
        `disconnect`: disconnect from the device
        `execute`: execute task
        `resetFlags`: reset all flags to class attribute `_default_flags`
        `run`: alias for `execute()`
        `shutdown`: shutdown procedure for tool
    """
    
    def __init__(self,
        port: str,
        stabilize_timeout: float = 10, 
        force_tolerance: float = 1.5, 
        mass_tolerance: float = 0.15,
        *, 
        calibration_factor: float = 1.0,
        correction_parameters: tuple[float] = (1.0,0.0),
        baudrate: int = 115200,
        verbose: bool = False, 
        **kwargs
    ):
        """
        Initialize the balance.
        
        Args:
            port (str): The port to connect to.
            stabilize_timeout (float): The time to wait for the balance to stabilize.
            force_tolerance (float): The tolerance for the force measurement.
            mass_tolerance (float): The tolerance for the mass measurement
            calibration_factor (float): The calibration factor for the balance.
            correction_parameters (tuple[float]): The correction parameters for the balance.
            baudrate (int): The baudrate for the balance.
            verbose (bool): The verbosity of the balance.
        """
        super().__init__(
            port=port, baudrate=baudrate, verbose=verbose, 
            stabilize_timeout=stabilize_timeout, force_tolerance=force_tolerance,
            calibration_factor=calibration_factor, 
            correction_parameters=correction_parameters,
            **kwargs
        )
        self.mass_tolerance = mass_tolerance
        return
    
    def getDataframe(self, data_store: Iterable[NamedTuple, datetime]) -> pd.DataFrame:
        df = datalogger.get_dataframe(data_store=data_store, fields=self.device.data_type._fields)
        df['corrected_value'] = df['value'].apply(self._correct_value)
        df['force'] = df['corrected_value'].apply(self._calculate_force)
        df['mass'] = df['corrected_value'].apply(self._calculate_mass)
        return df
    
    def atMass(self, mass: float) -> float:
        """ 
        Check if the balance is at a specific mass.
        
        Args:
            mass (float): The mass to check for.
            
        Returns:
            float: The force measured by the balance.
        """
        return self.atForce(mass*G, tolerance=self.mass_tolerance*G)
    
    def getMass(self) -> float:
        """
        Get the mass measured by the balance.
        
        Returns:
            float: The mass measured by the balance.
        """
        data = self.getForce()
        if data is None:
            return None
        return self._calculate_mass(data)
    
    def tare(self, wait: float = 5.0):
        """
        Tare the balance.
        
        Args:
            wait (float): The time to wait after taring.
        """
        return self.zero(wait=wait)
    
    def _calculate_force(self, value: float) -> float:
        """ 
        Calculate the force from the value.
        """
        return (value-self.baseline)/self.calibration_factor
    
    def _calculate_mass(self, value: float) -> float:
        """
        Calculate the mass from the value.
        
        Args:
            value (float): The value to calculate the mass from.
            
        Returns:
            float: The mass calculated from the value.
        """
        return self._calculate_force(value) / G
    
    def _correct_value(self, value: float) -> float:
        """
        Correct the value using the correction parameters.
        
        Args:
            value (float): The value to correct.
            
        Returns:
            float: The corrected value.
        """
        return sum([param * (value**i) for i,param in enumerate(self.correction_parameters[::-1])])
    