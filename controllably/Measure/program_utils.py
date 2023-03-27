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
from typing import Optional, Protocol, Any

# Local application imports
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
    
    @classmethod
    def getDetails(cls, verbose:bool = False) -> ProgramDetails:
        """
        Get the input fields and defaults
        
        Args:
            verbose: whether to print out truncated docstring. Defaults to False.

        Returns:
            dict: dictionary of program details
        """
        doc = inspect.getdoc(cls)
        # Extract truncated docstring and parameter listing
        lines = doc.split('\n')
        start, end = 0,0
        for i,line in enumerate(lines):
            # line = line.strip()
            if line.startswith('Args:'):
                start = i
            if line.startswith('==========') and start:
                end = i
                break
        parameter_list = sorted([_l.strip() for _l in lines[end+2:] if len(_l.strip())])
        short_lines = lines[:start-1] + lines[end:]
        short_doc = '\n'.join(short_lines)
        tooltip = '\n'.join(['Parameters:'] + [f'- {_p}' for _p in parameter_list])
        
        # Extract input fields and defaults
        inputs = []
        defaults = {}
        for parameter in parameter_list:
            if len(parameter) == 0:
                continue
            inputs.append(parameter.split(' ')[0])
            if 'Defaults' in parameter:
                defaults[inputs[-1]] = parameter.split(' ')[-1][:-1]
    
        cls.details = ProgramDetails(
            inputs=inputs,
            defaults=defaults,
            short_doc=short_doc,
            tooltip=tooltip
        )
        if verbose:
            print(short_doc)
        return cls.details
