# %% -*- coding: utf-8 -*-
"""
Created: Tue 2022/12/09 11:11:00
@author: Chang Jie

Notes / actionables:
-
"""
# Standard library imports
from enum import Enum

# Local application imports
print(f"Import: OK <{__name__}>")

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
    Busy    = ['@','A','B','C','D','E','F','G','H','I','J','K','O']
    Idle    = ['`','a','b','c','d','e','f','g','h','i','j','k','o']
