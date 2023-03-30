# %% -*- coding: utf-8 -*-
"""
Created: Tue 2022/12/09 11:11:00
@author: Chang Jie

Notes / actionables:
-
"""
# Standard library imports
from dataclasses import dataclass, field
from enum import Enum
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
    Busy    = ('@','A','B','C','D','E','F','G','H','I','J','K','O')
    Idle    = ('`','a','b','c','d','e','f','g','h','i','j','k','o')

@dataclass
class TriContinentPump:
    channel: int
    model: str
    capacity: int
    output_right: bool
    name: str = ''
    reagent: str = ''
    resolution: float = field(init=False)
    step_limit: int = field(init=False)
    
    busy: bool = field(default=False, init=False)
    init_status: bool = field(default=False, init=False)
    
    command: str = field(default='', init=False)
    position: int = field(default=0, init=False)
    _status_code: str = field(default='', init=False)
    
    def __post_init__(self):
        self.step_limit = int(''.join(filter(str.isdigit, self.model)))
        self.resolution = self.capacity / self.step_limit
        if len(self.name) == 0:
            self.name = f"Pump {self.channel}"
        return
    
    # Properties
    @property
    def status(self) -> str:
        return ErrorCode[self._status_code].value
    @status.setter
    def status(self, value:str):
        if value not in ErrorCode._member_names_:
            raise ValueError("Please provide a valid error code.")
        self._status_code = value
        return
    
    @property
    def volume(self) -> float:
        return self.position/self.step_limit * self.capacity
