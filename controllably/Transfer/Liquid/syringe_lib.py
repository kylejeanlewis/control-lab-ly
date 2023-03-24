# %% -*- coding: utf-8 -*-
"""
Adapted from @jaycecheng spinutils

Created: Tue 2022/11/01 17:13:35
@author: Chang Jie

Notes / actionables:
-
"""
# Standard library imports
from __future__ import annotations
from collections import namedtuple
from dataclasses import dataclass
import numpy as np

# Third party imports

# Local application imports
print(f"Import: OK <{__name__}>")

Calibration = namedtuple('Calibration', ['aspirate','dispense'])

@dataclass
class SyringeCalibration:
    first: Calibration
    aspirate: Calibration
    dispense: Calibration

CALIBRATION = SyringeCalibration(
    Calibration(35.1,23.5),
    Calibration(27,36.425),
    Calibration(43.2,23.5)
)

@dataclass
class Syringe:
    """
    Syringe class

    Args:
        capacity (int, or float): capacity of syringe
        channel (int): channel index
        offset (tuple, optional): coordinates offset. Defaults to None.
        pullback_time (int, optional): duration of pullback. Defaults to 2.
        
    Kwargs:
        verbose (bool, optional): whether to print output. Defaults to False.
    """
    capacity: float
    channel: int
    _offset: tuple[float] = (0,0,0)
    volume: float = 0
    reagent: str = ''
    pullback_time: float = 2
    _calibration: SyringeCalibration = CALIBRATION
    
    # Properties
    @property
    def calibration(self):
        return self._calibration
    
    @property
    def offset(self):
        return np.array(self._offset)
    
    def update(self, **kwargs):
        for key, value in kwargs.items():
            if key in self.__dict__:
                setattr(self, key, value)
        return
