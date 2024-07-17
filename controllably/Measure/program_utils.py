# %% -*- coding: utf-8 -*-
"""
This module holds the base class for measurement programs.

Classes:
    Program (ABC)
    ProgramDetails (dataclass)

Functions:
    get_program_details
"""
# Standard library imports
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import inspect
import logging
import pandas as pd
from typing import Callable, Optional, Protocol, Any

logger = logging.getLogger(__name__)
logger.debug(f"Import: OK <{__name__}>")

class Device(Protocol):
    ...

@dataclass
class ProgramDetails:
    """
    ProgramDetails dataclass represents the set of inputs, default values, truncated docstring and tooltip of a program class
    
    ### Constructor
    Args:
        `inputs` (list[str]): list of input field names
        `defaults` (dict[str, Any]): dictionary of kwargs and default values
        `short_doc` (str): truncated docstring of the program
        `tooltip` (str): descriptions of input fields
    """
    
    inputs: list[str] = field(default_factory=lambda: [])
    defaults: dict[str, Any] = field(default_factory=lambda: {})
    short_doc: str = ''
    tooltip: str = ''


class Program(ABC):
    """
    Base Program template

    ### Constructor
    Args:
        `device` (Device): device object
        `parameters` (Optional[dict], optional): dictionary of kwargs. Defaults to None.
        `verbose` (bool, optional): verbosity of class. Defaults to False.
    
    ### Attributes
    - `data_df` (pd.DataFrame): data collected from device when running the program
    - `device` (Device): device object
    - `parameters` (dict[str, ...]): parameters
    - `verbose` (bool): verbosity of class
    
    ### Methods
    #### Abstract
    - `run`: run the measurement program
    
    ==========
    
    ### Parameters:
        None
    """
    
    details: ProgramDetails = ProgramDetails()
    def __init__(self, 
        device: Device, 
        parameters: Optional[dict] = None,
        verbose: bool = False, 
        **kwargs
    ):
        """
        Instantiate the class

        Args:
            device (Device): device object
            parameters (Optional[dict], optional): dictionary of kwargs. Defaults to None.
            verbose (bool, optional): verbosity of class. Defaults to False.
        """
        self.device = device
        self.data_df = pd.DataFrame()
        self.parameters = parameters
        self.verbose = verbose
        return
    
    @abstractmethod
    def run(self, *args, **kwargs):
        """Run the measurement program"""


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
