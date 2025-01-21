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
from collections import deque
from dataclasses import dataclass, field
import inspect
import logging
import pandas as pd
from pathlib import Path
from typing import Callable, Optional, Protocol, Any

# Local application imports
from ..core.device import StreamingDevice, DataLoggerUtils

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


@dataclass
class _ProgramDetails:
    """
    ProgramDetails dataclass represents the set of inputs, default values, truncated docstring and tooltip of a program class
    
    ### Constructor
    Args:
        `inputs` (list[str]): list of input field names
        `defaults` (dict[str, Any]): dictionary of kwargs and default values
        `short_doc` (str): truncated docstring of the program
        `tooltip` (str): descriptions of input fields
    """
    
    signature: inspect.Signature
    description: str = ''
    parameter_descriptions: dict[str, str] = field(default_factory=dict)
    return_descriptions: dict[tuple[str], str] = field(default_factory=dict)
    
    def __str__(self):
        text = str(self.signature)
        text += f"\n\n{self.description}"
        if len(self.parameter_descriptions):
            text += f"\n\nArgs:"
            for k,v in self.parameter_descriptions.items():
                parameter = self.signature.parameters[k]
                text += f"\n    {parameter.name} ({parameter.annotation}): {v}."
                if parameter.default != inspect.Parameter.empty:
                    text += f" Defaults to {parameter.default}."
        if len(self.return_descriptions):
            text += f"\n\nReturns:"
            for k,v in self.return_descriptions.items():
                key = ', '.join(k) if isinstance(k,tuple) else k
                text += f"\n    {key}: {v}"
        return text


class _Program:
    """
    Base Program template

    ### Constructor
    Args:
        `device` (Device): device object
        `parameters` (Optional[dict], optional): dictionary of kwargs. Defaults to None.
        `verbose` (bool, optional): verbosity of class. Defaults to False.
        
    ### Attributes and properties
    - `data_df` (pd.DataFrame): data collected from device when running the program
    - `device` (Device): device object
    - `parameters` (dict[str, ...]): parameters
    - `verbose` (bool): verbosity of class

    ==========
    """
    def __init__(self, 
        device: StreamingDevice|None = None, 
        parameters: dict|None = None,
        verbose: bool = False, 
        **kwargs
    ):
        self.data = deque()
        self.device = device
        self.parameters = parameters or dict()
        self.verbose = verbose
        
        self.__doc__ = getattr(self,'run').__doc__
        return
    
    def __call__(self, *args, **kwargs):
        return self.run(*args, **kwargs)
    
    @property
    def data_df(self) -> pd.DataFrame:
        return DataLoggerUtils.getDataframe(data_store=self.data, fields=self.device.data_type._fields)
    
    @staticmethod
    def parseDocstring(program_class: _Program, verbose:bool = False) -> ProgramDetails:
        """
        Get the input fields and defaults
        
        Args:
            program_class (Callable): program class of interest
            verbose: whether to print out truncated docstring. Defaults to False.

        Returns:
            ProgramDetails: details of program class
        """
        method = getattr(program_class, 'run')
        doc = inspect.getdoc(method)
        
        description = ''
        args_dict = dict()
        ret_dict = dict()
        if doc is not None:
            description = doc.split('Args:')[0].split('Returns:')[0]
            description = ' '.join([l.strip() for l in description.split('\n') if len(l.strip())])
            
            if 'Args:' in doc:
                args = doc.split('Args:',1)[1].split('Returns:')[0]
                args = [l.split('Defaults',1)[0].strip() for l in args.split('\n') if len(l.strip())]
                args_dict = {a.split(' ')[0]: a.split(':',1)[1].strip() for a in args}
            
            if 'Returns:' in doc:
                ret = doc.split('Returns:',1)[1]
                ret = [l.strip() for l in ret.split('\n') if len(l.strip())]
                return_types, return_descriptions = [s for s in zip(*[r.split(':',1) for r in ret])]
                ret_keys = [tuple([s.strip() for s in r.split(',')]) for r in return_types]
                ret_keys = [r if len(r) > 1 else r[0] for r in ret_keys]
                ret_dict = {k: v.strip() for k,v in zip(ret_keys, return_descriptions)}

        details = _ProgramDetails(
            signature=inspect.signature(method),
            description=description,
            parameter_descriptions=args_dict,
            return_descriptions=ret_dict
        )
        if verbose:
            print(details)
        return details
    
    def run(self, *args, **kwargs) -> pd.DataFrame:
        """
        Measurement program to run

        Returns:
            pd.DataFrame: Dataframe of data collected
        """
        assert isinstance(self.device, StreamingDevice), "Ensure device is a StreamingDevice"
        return self.data_df
    
    def saveData(self, filepath: str|Path):
        self.data_df.to_csv(filepath)
        return
