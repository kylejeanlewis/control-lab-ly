# %% -*- coding: utf-8 -*-
"""
This module holds the references for syringe pumps from TriContinent.

## Classes:
    `ErrorCode`: Enum for error codes returned by the pump
    `StatusCode`: Enum for status codes returned by the pump
"""
# Standard library imports
from enum import Enum

class ErrorCode(Enum):
    er0     = 'No error'
    er1     = 'Initialization failure'
    er2     = 'Invalid command'
    er3     = 'Invalid operand'
    er4     = 'Invalid checksum'
    er5     = 'Unused'
    er6     = 'EEPROM failure'
    er7     = 'Device not initialized'
    er8     = 'CAN bus failure'
    er9     = 'Plunger overload'
    er10    = 'Valve overload'
    er11    = 'Plunger move not allowed'
    er15    = 'Command overflow'

class StatusCode(Enum):
    Busy    = ('@','A','B','C','D','E','F','G','H','I','J','K','_L','_M','_N','O')
    Idle    = ('`','a','b','c','d','e','f','g','h','i','j','k','_l','_m','_n','o')
