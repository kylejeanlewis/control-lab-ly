# %% -*- coding: utf-8 -*-
"""
This module holds the references for syringe pumps from TriContinent.

Classes:
    ErrorCode (Enum)
    StatusCode (Enum)
    TriContinentPump (dataclass)
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
    """
    TriContinentPump dataclass represents a single syringe pump channel when pumps are daisy-chained

    ### Constructor
    Args:
        `channel` (int): channel id
        `model` (str): TriContinent pump model name
        `capacity` (int): syringe capacity
        `output_right` (bool): whether liquid is pumped out to the right for channel
        `name` (str): name of the pump. Defaults to ''.
        `reagent` (str): name of reagent in pump. Defaults to ''.
    
    ### Attributes
    - `busy` (bool): whether the pump is busy
    - `capacity` (int): syringe capacity
    - `channel` (int): channel id
    - `command` (str): command string
    - `init_status` (bool): whether the pump has been initialised
    - `limits` (int): maximum allowable position
    - `model` (str): TriContinent pump model name
    - `name` (str): name of the pump
    - `output_right` (bool): whether liquid is pumped out to the right
    - `position` (int): position of plunger
    - `reagent` (str): name of reagent in pump
    - `resolution` (float): volume resolution of pump (i.e. uL per step)
    
    ### Properties
    - `status` (str): pump device status
    - `volume` (float): volume of reagent in pump
    """
    
    channel: int
    model: str
    capacity: int
    output_right: bool
    name: str = ''
    reagent: str = ''
    limits: int = field(init=False)
    resolution: float = field(init=False)
    
    busy: bool = field(default=False, init=False)
    init_status: bool = field(default=False, init=False)
    
    command: str = field(default='', init=False)
    position: int = field(default=0, init=False)
    _status_code: str = field(default='', init=False)
    
    def __post_init__(self):
        self.limits = int(''.join(filter(str.isdigit, self.model)))
        self.resolution = self.capacity / self.limits
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
        return self.position/self.limits * self.capacity
