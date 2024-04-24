# %% -*- coding: utf-8 -*-
"""
This module holds the references for tools from Keithley.

Classes:
    SenseDetails (dataclass)
    SourceDetails (dataclass)

Functions:
    set_function_type
    set_limit

Other constants and variables:
    COUNT_UPPER_LIMIT (int)
    CURRENT_LIMITS (tuple)
    VOLTAGE_LIMITS (tuple)
"""
# Standard library imports
from __future__ import annotations
from dataclasses import dataclass, field
import numpy as np
from typing import Optional, Union
print(f"Import: OK <{__name__}>")

COUNT_UPPER_LIMIT = 300000
"""Maximum number of rows in buffer"""
CURRENT_LIMITS = (10e-9, 100e-9, 1e-6, 10e-6, 100e-6, 1e-3, 10e-3, 100e-3, 1)
"""Available current limit settings"""
VOLTAGE_LIMITS = (20e-3, 200e-3, 2, 20, 200)
"""Available voltage limit settings"""

def set_function_type(value:str, choices:tuple[str]) -> str:
    """
    Set the function type for either source or sense

    Args:
        value (str): function type
        choices (tuple[str]): options for function type

    Raises:
        ValueError: Select a valid function type

    Returns:
        str: name of function
    """
    if value is None:
        return None
    value = value.lower()
    for choice in choices:
        if value in choice.lower():
            return choice
    raise ValueError(f"Select a valid function from: {', '.join([c.lower() for c in choices])}")

def set_limit(limit:Union[str, float, None], is_current:bool) -> Union[str, float]:
    """
    Set the operating limits of Keithley

    Args:
        limit (Union[str, float, None]): limit option
        is_current (bool): whether setting limit for current function

    Raises:
        ValueError: Select a valid option

    Returns:
        Union[str, float]: limit option
    """
    if limit is None:
        return 'AUTO ON'
    if type(limit) is str:
        limit = limit.lower()
        choices = ('DEFault', 'MAXimum', 'MINimum')
        for choice in choices:
            if limit in choice.lower():
                return choice
        raise ValueError(f"Select a valid option from: {', '.join([c.lower() for c in choices])}")
    unit = 'A' if is_current else 'V'
    options = np.array(CURRENT_LIMITS) if is_current else np.array(VOLTAGE_LIMITS)
    shortlist = options[options >= abs(limit)]
    if len(shortlist):
        return shortlist[0]
    print(f'Input limit beyond -{limit} and {limit} {unit}')
    print(f'Defaulting to {options[-1]} {unit}')
    return options[-1]
    

@dataclass
class SenseDetails:
    """
    SenseDetails represents a set of parameters for Keithley's sense terminal

    ### Constructor
    Args:
        `function_type` (Optional[str]): name of function, choice from current, resistance, and voltage. Defaults to None.
        `range_limit` (Union[str, float, None]): sensing range. Defaults to 'DEFault'.
        `four_point` (bool): whether to use four-point probe measurement. Defaults to True.
        `count` (int): number of readings to measure for each condition. Defaults to 1.
    
    ### Attributes
    - `count` (int): number of readings to measure for each condition
    - `four_point` (bool): whether to use four-point probe measurement
    - `function_type` (Optional[str]): name of function
    - `range_limit` (Union[str, float, None]): sensing range
    
    ### Properties
    - `unit` (str): units of measurement
    
    ### Methods
    - `get_commands`: generate commands from details
    """
    
    function_type: Optional[str] = None
    range_limit: Union[str, float, None] = 'DEFault'
    four_point: bool = True
    count: int = 1
    _choices: tuple[str] = field(default=('CURRent', 'RESistance', 'VOLTage'), init=False)
    _name: str = field(default='SENSe', init=False)
    
    def __post_init__(self):
        self.function_type = set_function_type(self.function_type, self._choices)
        self.range_limit = set_limit(self.range_limit, (self.function_type=='CURRent'))
        self.four_point = 'ON' if self.four_point else 'OFF'
        self.count = max(1, min(self.count, COUNT_UPPER_LIMIT))
        return
    
    # Properties
    @property
    def unit(self) -> str:
        if self.function_type == 'CURRent':
            return 'AMP'
        elif self.function_type == 'VOLTage':
            return 'VOLT'
        return ''
    
    def get_commands(self) -> list[str]:
        """
        Generate commands from details
        
        Returns:
            list[str]: list of command strings
        """
        commands = {
            'RANGe': self.range_limit,
            'RSENse': self.four_point,
            'UNIT': self.unit
        }
        commands = [f'{self._name}:{self.function_type}:{k} {v}' for k,v in commands.items()]
        for i,command in enumerate(commands):
            if 'AUTO' in command:
                new_command = ':AUTO'.join((command.split(' AUTO')))
                commands[i] = new_command
        commands = commands + [f'SENSe:COUNt {self.count}']
        return commands
    
@dataclass
class SourceDetails:
    """
    SourceDetails represents a set of parameters for Keithley's source terminal

    ### Constructor
    Args:
        `function_type` (Optional[str]): name of function, choice from current and voltage. Defaults to None.
        `range_limit` (Union[str, float, None]): sourcing range. Defaults to None.
        `measure_limit` (Union[str, float, None]): limit imposed on the measurement range. Defaults to 'DEFault'.
    
    ### Attributes
    - `function_type` (Optional[str]): name of function
    - `measure_limit` (Union[str, float, None]): limit imposed on the measurement range
    - `range_limit` (Union[str, float, None]): sourcing range
    
    ### Properties
    - `measure_type` (str): type of measurement limit
    
    ### Methods
    - `get_commands`: generate commands from details
    """
    
    function_type: str = ''
    range_limit: Union[str, float, None] = None
    measure_limit: Union[str, float, None] = 'DEFault'
    _choices: tuple[str] = field(default=('CURRent', 'VOLTage'), init=False)
    _count: int = field(default=0, init=False)
    _name: str = field(default='SOURce', init=False)
    
    def __post_init__(self):
        self.function_type = set_function_type(self.function_type, self._choices)
        self.range_limit = set_limit(self.range_limit, (self.function_type=='CURRent'))
        self.measure_limit = set_limit(self.measure_limit, (self.function_type!='CURRent'))
        return
    
    # Properties
    @property
    def measure_type(self) -> str:
        value = 'VLIMit' if self.function_type == 'CURRent' else 'ILIMit'
        return value
    
    def get_commands(self) -> list[str]:
        """
        Generate commands from details
        
        Returns:
            list[str]: list of command strings
        """
        commands = {
            'RANGe': self.range_limit,
            self.measure_type: self.measure_limit
        }
        commands = [f'{self._name}:{self.function_type}:{k} {v}' for k,v in commands.items()]
        for i,command in enumerate(commands):
            if 'AUTO' in command:
                new_command = ':AUTO'.join((command.split(' AUTO')))
                commands[i] = new_command
        return commands
    