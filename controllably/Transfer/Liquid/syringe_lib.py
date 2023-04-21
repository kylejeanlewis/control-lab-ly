# %% -*- coding: utf-8 -*-
"""
This module holds the references for syringe tools.

Classes:
    Syringe (dataclass)
    SyringeCalibration (dataclass)

Other types:
    Calibration (namedtuple)

Other constants and variables:
    CALIBRATION (SyringeCalibration)
"""
# Standard library imports
from __future__ import annotations
from collections import namedtuple
from dataclasses import dataclass, field
import numpy as np
print(f"Import: OK <{__name__}>")

Calibration = namedtuple('Calibration', ['aspirate','dispense'])
"""Calibration is a named tuple for an aspirate-dispense pair calibration value"""

@dataclass
class SyringeCalibration:
    """
    SyringeCalibration dataclass represent a single set of calibration parameter for syringes
    
    ### Constructor
    Args:
        first (Calibration): aspirate-dispense calibration value for first action
        aspirate (Calibration): aspirate-dispense calibration value for action following an aspiration
        dispense (Calibration): aspirate-dispense calibration value for action following a dispense
    """
    first: Calibration
    aspirate: Calibration
    dispense: Calibration

CALIBRATION = SyringeCalibration(
    Calibration(35.1,23.5),
    Calibration(27,36.425),
    Calibration(43.2,23.5)
)
"""Calibration parameters for setup that has been empirically determined"""

@dataclass
class Syringe:
    """
    Syringe dataclass represents a single syringe

    ### Constructor
    Args:
        `capacity` (float): capacity of syringe
        `channel` (int): channel id
        `offset` (tuple[float], optional): coordinates offset. Defaults to (0,0,0).
        `volume` (float): volume of reagent in syringe. Defaults to 0.
        `reagent` (str): name of reagent. Defaults to ''.
        `pullback_time` (float, optional): duration of pullback. Defaults to 2.
        `_calibration` (SyringeCalibration): calibration parameters. Defaults to CALIBRATION.
    
    ### Attributes
    - `capacity` (float): capacity of syringe
    - `channel` (int): channel id
    - `offset` (np.ndarray): coordinates offset
    - `pullback_time` (float): duration of pullback
    - `reagent` (str): name of reagent
    - `volume` (float): volume of reagent in syringe
    
    ### Properties
    - `calibration` (SyringeCalibration): calibration parameters
    
    ### Methods
    - `update`: update values of attributes and properties
    """
    
    capacity: float
    channel: int
    offset: tuple[float] = (0,0,0)
    volume: float = 0
    reagent: str = ''
    pullback_time: float = 2
    _calibration: SyringeCalibration = field(default_factory=lambda: CALIBRATION)
    
    def __post_init__(self):
        self.offset = np.array(self.offset)
        return
    
    def __repr__(self) -> str:
        return f"Syringe {self.channel} (capacity={self.capacity}, volume={self.volume}, reagent={self.reagent}, offset={self.offset})"
    
    # Properties
    @property
    def calibration(self) -> SyringeCalibration:
        return self._calibration
    
    def update(self, **kwargs):
        """
        Update values of attributes and properties
        
        Kwargs:
            key, value: (attribute, value) pairs
        """
        for key, value in kwargs.items():
            if key in self.__dict__:
                setattr(self, key, value)
        return
