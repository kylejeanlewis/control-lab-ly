# %% -*- coding: utf-8 -*-
"""
This module holds the references for tools from PiezoRobotics.

Classes:
    CommandCode (Enum)
    ErrorCode (Enum)
    FrequencyCode (Enum)
    Frequency (dataclass)
"""
# Standard library imports
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
print(f"Import: OK <{__name__}>")

class CommandCode(Enum):
    INIT    = 'To initialize after every power-up, make sure there is no sample placed on the pr.DMA'
    CLAMP   = 'To control the automatic clamping system'
    RUN     = 'To run the test and apply a compressive sinusoidal force on the material sample'
    GET     = 'To export the measurement results of the previously run test - complex modulus of the material sample as a function of frequency'
    CLR     = 'To clear previously acquired data stored in the pr.DMA'

class ErrorCode(Enum):
    ERROR1  = 'Invalid syntax (the specified forma is incorrect or parameters are missing).'
    ERROR2  = 'Serial number not matching the device.'
    ERROR3  = 'Wrong parameters.'
    ERROR4  = 'Invalid function specified.'
    ERROR5  = 'No sample detected while clamping.'
    
class FrequencyCode(Enum):
    FREQ_01 = 1.1
    FREQ_02 = 1.2
    FREQ_03 = 1.3
    FREQ_04 = 1.4
    FREQ_05 = 1.5
    FREQ_06 = 1.7
    FREQ_07 = 1.8
    FREQ_08 = 2.0
    FREQ_09 = 2.2
    FREQ_10 = 2.4
    FREQ_11 = 2.6
    FREQ_12 = 2.9
    FREQ_13 = 3.1
    FREQ_14 = 3.4
    FREQ_15 = 3.7
    FREQ_16 = 4.1
    FREQ_17 = 4.5
    FREQ_18 = 4.9
    FREQ_19 = 5.4
    FREQ_20 = 5.9
    FREQ_21 = 6.5
    FREQ_22 = 7.0
    FREQ_23 = 7.7
    FREQ_24 = 8.4
    FREQ_25 = 9.2
    FREQ_26 = 10.1
    FREQ_27 = 11.0
    FREQ_28 = 12.0
    FREQ_29 = 13.2
    FREQ_30 = 14.5
    FREQ_31 = 15.6
    FREQ_32 = 17.2
    FREQ_33 = 18.9
    FREQ_34 = 20.4
    FREQ_35 = 22.2
    FREQ_36 = 24.4
    FREQ_37 = 27.0
    FREQ_38 = 29.4
    FREQ_39 = 32.2
    FREQ_40 = 34.5
    FREQ_41 = 38.4
    FREQ_42 = 41.6
    FREQ_43 = 45.4
    FREQ_44 = 47.6
    FREQ_45 = 52.6
    FREQ_46 = 58.8
    FREQ_47 = 62.4
    FREQ_48 = 66.6
    FREQ_49 = 71.3
    FREQ_50 = 76.8
    FREQ_51 = 83.2
    FREQ_52 = 90.8
    FREQ_53 = 99.8
    FREQ_54 = 110.9

@dataclass
class Frequency:
    """
    Frequency dataclass represents a low and high frequency range limit

    ### Constructor
    Args:
        `low` (float): frequency lower bound. Defaults to FrequencyCode.FREQ_01
        `high` (float): frequency upper bound. Defaults to FrequencyCode.FREQ_54
    
    ### Attributes
    - `low` (float): frequency lower bound. Defaults to FrequencyCode.FREQ_01
    - `high` (float): frequency upper bound. Defaults to FrequencyCode.FREQ_54
    
    ### Properties
    - `code` (tuple[str]): tuple of (lower frequency code, upper frequency code)
    """
    
    low: float = FrequencyCode.FREQ_01
    high: float = FrequencyCode.FREQ_54
    
    @property
    def code(self):
        low = str(int(FrequencyCode(self.low).name[-2:]))
        high = str(int(FrequencyCode(self.high).name[-2:]))
        return low,high
