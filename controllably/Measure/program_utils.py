# %% -*- coding: utf-8 -*-
"""
Created: Tue 2023/01/05 17:13:35
@author: Chang Jie

Notes / actionables:
-
"""
# Standard library imports
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import inspect
import pandas as pd
from typing import Callable, Optional, Protocol, Any
print(f"Import: OK <{__name__}>")

class Device(Protocol):
    ...

@dataclass
class ProgramDetails:
    inputs: list[str] = field(default_factory=lambda: [])
    defaults: dict[str, Any] = field(default_factory=lambda: {})
    short_doc: str = ''
    tooltip: str = ''

class Program(ABC):
    """
    Base Program template

    Args:
        device (PiezoRoboticsDevice): PiezoRobotics Device object
        parameters (dict, optional): dictionary of measurement parameters. Defaults to {}.
    
    ==========
    Parameters:
        None
    """
    details: ProgramDetails = ProgramDetails()
    def __init__(self, 
        device: Device, 
        parameters: Optional[dict] = None,
        verbose: bool = False, 
        **kwargs
    ):
        self.device = device
        self.data_df = pd.DataFrame()
        self.parameters = parameters
        self.verbose = verbose
        return
    
    @abstractmethod
    def run(self, *args, **kwargs):
        """
        Run the measurement program
        """
def get_program_details(program_class: Callable, verbose:bool = False) -> ProgramDetails:
    """
    Get the input fields and defaults
    
    Args:
        program_class (Callable): program class of interest
        verbose: whether to print out truncated docstring. Defaults to False.

    Returns:
        ProgramDetails: details of program class
    """
    doc = inspect.getdoc(program_class)
    
    # Extract truncated docstring and parameter listing
    lines = doc.split('\n')
    start, end = 0,0
    for i,line in enumerate(lines):
        # line = line.strip()
        if line.startswith('### Constructor'):
            start = i
        if line.startswith('===') and start:
            end = i
            break
    short_lines = [''] + lines[:start-1] + lines[end:]
    short_doc = '\n'.join(short_lines).replace("### ", "")
    parameter_list = [l.strip() for l in lines[end+3:] if len(l.strip())]
    tooltip = '\n'.join(['Parameters:'] + [f'- {p}' for p in parameter_list])
    
    # Extract input fields and defaults
    inputs = []
    defaults = {}
    for parameter in parameter_list:
        if len(parameter) == 0:
            continue
        inputs.append(parameter.split(' ')[0])
        if 'Defaults' in parameter:
            defaults[inputs[-1]] = parameter.split(' ')[-1][:-1]

    details = ProgramDetails(
        inputs=inputs,
        defaults=defaults,
        short_doc=short_doc,
        tooltip=tooltip
    )
    if verbose:
        print(short_doc)
    return details
