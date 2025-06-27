# -*- coding: utf-8 -*-
""" 
This module contains the base classes for making measurements with a device.

Attributes:
    MAX_LEN (int): maximum length of data buffer
    
## Classes:
    `Measurer`: Base class for maker tools
    `Program`: Base Program template
    `ProgramDetails`: ProgramDetails dataclass represents the set of inputs, default values, truncated docstring and tooltip of a program class
    
<i>Documentation last updated: 2025-02-22</i>
"""
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
from typing import Any, NamedTuple, Iterable, Callable

# Local application imports
from ..core import datalogger, factory
from ..core.device import StreamingDevice

# Configure logging
from controllably import CustomLevelFilter
logger = logging.getLogger(__name__)

MAX_LEN = 100

class Measurer:
    """
    Base class for maker tools.
    
    ### Constructor:
        `verbose` (bool, optional): verbosity of class. Defaults to False.
    
    ### Attributes and properties:
        `buffer` (deque): data buffer for the device
        `buffer_df` (pd.DataFrame): data buffer as a DataFrame
        `records` (deque): records for the device
        `records_df` (pd.DataFrame): records as a DataFrame
        `record_event` (threading.Event): event for recording data
        `program` (Program): program to run
        `runs` (dict): dictionary of runs
        `n_runs` (int): number of runs
        `connection_details` (dict): connection details for the device
        `device` (Device): device object that communicates with physical tool
        `flags` (SimpleNamespace[str, bool]): flags for the class
        `is_busy` (bool): whether the device is busy
        `is_connected` (bool): whether the device is connected
        `verbose` (bool): verbosity of class
    
    ### Methods:
        `connect`: connect to the device
        `disconnect`: disconnect from the device
        `resetFlags`: reset all flags to class attribute `_default_flags`
        `shutdown`: shutdown procedure for tool
    """
    
    _default_flags: SimpleNamespace[str,bool] = SimpleNamespace(busy=False, verbose=False)
    def __init__(self, *, verbose:bool = False, **kwargs):
        """
        Initialize Measurer class

        Args:
            verbose (bool, optional): verbosity of class. Defaults to False.
        """
        self.device: StreamingDevice = kwargs.get('device', factory.create_from_config(kwargs))
        self.flags: SimpleNamespace = deepcopy(self._default_flags)
        
        self._logger = logger.getChild(f"{self.__class__.__name__}.{id(self)}")
        self.verbose = verbose
        
        # Category specific attributes
        # Data logging attributes
        self.buffer: deque[tuple[NamedTuple, datetime]] = deque(maxlen=MAX_LEN)
        self.records: deque[tuple[NamedTuple, datetime]] = deque()
        self.record_event = threading.Event()
        
        # Measurer specific attributes
        self.program: Program|Any|None = None
        self.runs = dict()
        self.n_runs = 0
        self._threads = dict()
        
        if kwargs.get('final', True):
            self.connect()
        return
    
    def __del__(self):
        self.shutdown()
        return
    
    def __enter__(self):
        """Context manager enter method"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        """Context manager exit method"""
        self.disconnect()
        return False
    
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
        CustomLevelFilter().setModuleLevel(self._logger.name, level)
        return
    
    # Data logging properties
    @property
    def buffer_df(self) -> pd.DataFrame:
        """Data buffer as a DataFrame"""
        return self.getDataframe(data_store=self.buffer)
    
    @property
    def records_df(self) -> pd.DataFrame:
        """Records as a DataFrame"""
        return self.getDataframe(data_store=self.records)

    def connect(self):
        """Connect to the device"""
        self.device.connect()
        return
    
    def disconnect(self):
        """Disconnect from the device"""
        self.device.disconnect()
        return
    
    def reset(self):
        """Reset the device and clear cache"""
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
        """
        Run the measurement program
        
        Args:
        *args: positional arguments
            parameters (dict, optional): dictionary of kwargs. Defaults to None.
            blocking (bool, optional): whether to block until completion. Defaults to True.
            **kwargs: keyword arguments
            
        Returns:
            pd.DataFrame|None: dataframe of data collected
        """
        assert issubclass(self.program, Program), "No Program loaded"
        new_run = self.program(
            instrument = self, 
            parameters = parameters,
            verbose = self.verbose
        )
        kwargs.update(new_run.parameters)
        
        self.n_runs += 1
        self._logger.info(f"Run ID: {self.n_runs}")
        self.runs[self.n_runs] = new_run
        if not blocking:
            thread = threading.Thread(target=new_run.run, args=args, kwargs=kwargs)
            thread.start()
            self._threads['measure'] = thread
            self.flags.busy = True
            return
        new_run.run(*args, **kwargs)
        self.flags.busy = False
        return new_run.data_df
        
    def loadProgram(self, program: Program, docstring_parser: Callable[[Any,bool],ProgramDetails]|None = None):
        """
        Load a program to the Measurer
        
        Args:
            program (Program): program to load
        """
        assert issubclass(program, Program), "Ensure program type is a subclass of Program"
        self.program = program
        if docstring_parser is None and hasattr(program, 'parseDocstring'):
            docstring_parser = program.parseDocstring
        if docstring_parser is not None:
            self.measure.__func__.__doc__ = docstring_parser(program, verbose=self.verbose)
        return
        
    def clearCache(self):
        """Clear the cache"""
        self.device.clearDeviceBuffer()
        self.buffer.clear()
        self.records.clear()
        self.n_runs = 0
        self.runs.clear()
        self._threads.clear()
        return
        
    def getData(self, query:Any|None = None, *args, **kwargs) -> Any|None:
        """
        Get data from the device
        
        Args:
            query (Any, optional): query to device. Defaults to None.
            
        Returns:
            Any|None: data from device
        """
        if not self.device.stream_event.is_set():
            self.device.clearDeviceBuffer()
            return self.device.query(query, multi_out=False)
        
        data_store = self.records if self.record_event.is_set() else self.buffer
        out = data_store[-1] if len(data_store) else None
        data,_ = out if out is not None else (None,None)
        return data
    
    def getDataframe(self, data_store: Iterable[tuple[NamedTuple, datetime]]) -> pd.DataFrame:
        """
        Get dataframe of data collected
        
        Args:
            data_store (Iterable[tuple[NamedTuple, datetime]]): data store
            
        Returns:
            pd.DataFrame: dataframe of data collected
        """
        return datalogger.get_dataframe(data_store=data_store, fields=self.device.data_type._fields)
    
    def saveData(self, filepath:str|Path):
        """
        Save data to file
        
        Args:
            filepath (str|Path): path to save file
        """
        if not len(self.records):
            raise ValueError("No records to save. Ensure you have recorded data before saving.")
        self.records_df.to_csv(filepath)
        return
    
    def record(self, on: bool, show: bool = False, clear_cache: bool = False, *, callback: Callable|None = None, **kwargs):
        """
        Record data from the device
        
        Args:
            on (bool): whether to record data
            show (bool, optional): whether to show data. Defaults to False.
            clear_cache (bool, optional): whether to clear the cache. Defaults to False.
            callback (Callable, optional): callback function to process data. Defaults to None.
        """
        self.device.clearDeviceBuffer()
        return datalogger.record(
            on=on, show=show, clear_cache=clear_cache, data_store=self.records, 
            device=self.device, callback=callback, event=self.record_event, **kwargs
        )
    
    def stream(self, on: bool, show: bool = False, *, callback: Callable|None = None, **kwargs):
        """
        Stream data from the device
        
        Args:
            on (bool): whether to stream data
            show (bool, optional): whether to show data. Defaults to False.
            callback (Callable, optional): callback function to process data. Defaults to None.
        """
        self.device.clearDeviceBuffer()
        return datalogger.stream(
            on=on, show=show, data_store=self.buffer, device=self.device, callback=callback, **kwargs
        )


class Program:
    """
    Base Program template

    ### Constructor:
        `instrument` (Measurer, optional): Measurer object. Defaults to None.
        `parameters` (dict, optional): dictionary of kwargs. Defaults to None.
        `verbose` (bool, optional): verbosity of class. Defaults to False.
        
    ### Attributes and properties:
        `data` (deque): data collected from device when running the program
        `instrument` (Measurer): Measurer object
        `parameters` (dict): dictionary of kwargs
        `verbose` (bool): verbosity of class
        `data_df` (pd.DataFrame): dataframe of data collected
        
    ### Methods:
        `getDataframe`: get dataframe of data collected
        `run`: measurement program to run
        `saveData`: save data to file

    ==========
    """
    def __init__(self, 
        instrument: Measurer|None = None, 
        parameters: dict|None = None,
        verbose: bool = False, 
        **kwargs
    ):
        """
        Initialize Program class
        
        Args:
            instrument (Measurer, optional): Measurer object. Defaults to None.
            parameters (dict, optional): dictionary of kwargs. Defaults to None.
            verbose (bool, optional): verbosity of class. Defaults to False.
        """
        
        self.data = deque()
        self.instrument = instrument
        self.parameters = parameters or dict()
        self.verbose = verbose
        
        self.__doc__ = getattr(self,'run').__doc__
        return
    
    def __call__(self, *args, **kwargs):
        return self.run(*args, **kwargs)
    
    @property
    def data_df(self) -> pd.DataFrame:
        """Data collected from device when running the program"""
        return self.getDataframe(self.data)
    
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
            description = ' '.join([line.strip() for line in description.split('\n') if len(line.strip())])
            
            if 'Args:' in doc:
                args = doc.split('Args:',1)[1].split('Returns:')[0]
                args = [line.split('Defaults',1)[0].strip() for line in args.split('\n') if len(line.strip())]
                args_dict = {a.split(' ')[0]: a.split(':',1)[1].strip() for a in args}
            
            if 'Returns:' in doc:
                ret = doc.split('Returns:',1)[1]
                ret = [line.strip() for line in ret.split('\n') if len(line.strip())]
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
    
    def getDataframe(self, data_store: Iterable[NamedTuple, datetime]) -> pd.DataFrame:
        """
        Get dataframe of data collected
        
        Args:
            data_store (Iterable[NamedTuple, datetime]): data store
            
        Returns:
            pd.DataFrame: dataframe of data collected
        """
        assert issubclass(self.instrument, Measurer), "Ensure instrument is a (subclass of) Measurer"
        return self.instrument.getDataframe(data_store=data_store)
    
    def run(self, *args, **kwargs) -> pd.DataFrame:
        """
        Measurement program to run

        Returns:
            pd.DataFrame: Dataframe of data collected
        """
        assert issubclass(self.instrument, Measurer), "Ensure instrument is a (subclass of) Measurer"
        return self.data_df
    
    def saveData(self, filepath: str|Path):
        """
        Save data to file
        
        Args:
            filepath (str|Path): path to save file
        """
        self.data_df.to_csv(filepath)
        return


@dataclass
class ProgramDetails:
    """
    ProgramDetails dataclass represents the set of inputs, default values, truncated docstring and tooltip of a program class
    
    ### Constructor:
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
            text += "\n\nArgs:"
            for k,v in self.parameter_descriptions.items():
                parameter = self.signature.parameters[k]
                text += f"\n    {parameter.name} ({parameter.annotation}): {v}"
                if not v.endswith('.'):
                    text += "."
                if parameter.default != inspect.Parameter.empty:
                    text += f" Defaults to {parameter.default}."
        if len(self.return_descriptions):
            text += "\n\nReturns:"
            for k,v in self.return_descriptions.items():
                key = ', '.join(k) if isinstance(k,tuple) else k
                text += f"\n    {key}: {v}"
        return text
    