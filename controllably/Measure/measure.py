# -*- coding: utf-8 -*-
# Standard library imports
from __future__ import annotations
from collections import deque
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime
import inspect
import logging
import pandas as pd
import threading
from pathlib import Path
from types import SimpleNamespace
from typing import Any, NamedTuple

# Local application imports
from ..core import factory
from ..core.device import StreamingDevice, DataLoggerUtils

_logger = logging.getLogger("controllably.Measure")
_logger.debug(f"Import: OK <{__name__}>")

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
logger.addHandler(handler)

MAX_LEN = 100

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


class Program:
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
    def parseDocstring(program_class: Program, verbose:bool = False) -> ProgramDetails:
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

        details = ProgramDetails(
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


class Measurer:
    """
    Base class for maker tools.
    
    ### Constructor
        `verbose` (bool, optional): verbosity of class. Defaults to False.
    
    ### Attributes and properties
        `connection_details` (dict): connection details for the device
        `device` (Device): device object that communicates with physical tool
        `flags` (SimpleNamespace[str, bool]): flags for the class
        `is_busy` (bool): whether the device is busy
        `is_connected` (bool): whether the device is connected
        `verbose` (bool): verbosity of class
    
    ### Methods
        `connect`: connect to the device
        `disconnect`: disconnect from the device
        `execute`: execute task
        `resetFlags`: reset all flags to class attribute `_default_flags`
        `run`: alias for `execute()`
        `shutdown`: shutdown procedure for tool
    """
    
    _default_flags: SimpleNamespace[str,bool] = SimpleNamespace(busy=False, verbose=False)
    def __init__(self, *, verbose:bool = False, **kwargs):
        """
        Instantiate the class

        Args:
            verbose (bool, optional): verbosity of class. Defaults to False.
        """
        self.device: StreamingDevice = kwargs.get('device', factory.create_from_config(kwargs))
        self.flags: SimpleNamespace = deepcopy(self._default_flags)
        
        self._logger = logger.getChild(f"{self.__class__.__name__}_{id(self)}")
        self._logger.addHandler(logging.StreamHandler())
        self.verbose = verbose
        
        # Category specific attributes
        # Data logging attributes
        self.buffer: deque[tuple[NamedTuple, datetime]] = deque(maxlen=MAX_LEN)
        self.records: deque[tuple[NamedTuple, datetime]] = deque()
        self.record_event = threading.Event()
        
        # Measurer specific attributes
        self.program: Program|None = None
        self.runs = dict()
        self.n_runs = 0
        self._threads = dict()
        return
    
    def __del__(self):
        self.shutdown()
        return
    
    @property
    def connection_details(self) -> dict:
        """Connection details for the device"""
        return self.device.connection_details
    
    @property
    def is_busy(self) -> bool:
        """Whether the device is busy"""
        return self.flags.busy
    
    @property
    def is_connected(self) -> bool:
        """Whether the device is connected"""
        return self.device.is_connected
    
    @property
    def verbose(self) -> bool:
        """Verbosity of class"""
        return self.flags.verbose
    @verbose.setter
    def verbose(self, value:bool):
        assert isinstance(value,bool), "Ensure assigned verbosity is boolean"
        self.flags.verbose = value
        level = logging.DEBUG if value else logging.INFO
        for handler in self._logger.handlers:
            if not isinstance(handler, logging.StreamHandler):
                continue
            handler.setLevel(level)
        return
    
    # Data logging properties
    @property
    def buffer_df(self) -> pd.DataFrame:
        return DataLoggerUtils.getDataframe(data_store=self.buffer, fields=self.device.data_type._fields)
    
    @property
    def records_df(self) -> pd.DataFrame:
        return DataLoggerUtils.getDataframe(data_store=self.records, fields=self.device.data_type._fields)
    
    def connect(self):
        """Connect to the device"""
        self.device.connect()
        return
    
    def disconnect(self):
        """Disconnect from the device"""
        self.device.disconnect()
        return
    
    def reset(self):
        self.clearCache()
        self.program = None
        return
    
    def resetFlags(self):
        """Reset all flags to class attribute `_default_flags`"""
        self.flags = deepcopy(self._default_flags)
        return
    
    def shutdown(self):
        """Shutdown procedure for tool"""
        self.disconnect()
        self.resetFlags()
        return

    # Category specific properties and methods
    def measure(self, *args, parameters: dict|None = None, blocking:bool = True, **kwargs) -> pd.DataFrame|None:
        assert issubclass(self.program, Program), "No Program loaded"
        new_run = self.program(
            device = self.device, 
            parameters = parameters,
            verbose = self.verbose
        )
        kwargs.update(new_run.parameters)
        
        self.n_runs += 1
        self.runs[self.n_runs] = new_run
        if not blocking:
            thread = threading.Thread(target=new_run.run, args=args, kwargs=kwargs)
            thread.start()
            self._threads['measure'] = thread
            return
        new_run.run(*args, **kwargs)
        return new_run.data_df
        
    def loadProgram(self, program:Program):
        assert issubclass(program, Program), "Ensure program type is a subclass of Program"
        self.program = program
        self.measure.__func__.__doc__ = program.parseDocstring(program, verbose=self.verbose)
        return
        
    def clearCache(self):
        self.buffer.clear()
        self.records.clear()
        self.n_runs = 0
        return
        
    def getData(self, query:Any|None = None, *args, **kwargs) -> Any|None:
        if not self.device.stream_event.is_set():
            return self.device.query(query, multi_out=False)
        
        data_store = self.records if self.record_event.is_set() else self.buffer
        out = data_store[-1] if len(data_store) else None
        data,_ = out if out is not None else (None,None)
        return data
    
    def saveData(self, filepath:str|Path):
        if not len(self.records):
            raise
        self.records_df.to_csv(filepath)
        return
    
    def record(self, on: bool, show: bool = False, clear_cache: bool = False):
        return DataLoggerUtils.record(
            on=on, show=show, clear_cache=clear_cache, data_store=self.records, 
            device=self.device, event=self.record_event
        )
    
    def stream(self, on: bool, show: bool = False):
        return DataLoggerUtils.stream(
            on=on, show=show, data_store=self.buffer, 
            device=self.device, event=self.record_event
        )
