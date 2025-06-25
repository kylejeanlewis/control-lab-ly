# -*- coding: utf-8 -*-
from __future__ import annotations
import ast
from collections import deque
from datetime import datetime
from inspect import getdoc, Signature, Parameter
import json
import logging
import nest_asyncio
from pathlib import Path
import threading
import time
from types import SimpleNamespace
from typing import NamedTuple, Any, Callable, Iterable

# Third party imports
import easy_biologic
from easy_biologic.lib import ec_lib as ecl     # pip install easy-biologic
from easy_biologic.device import BiologicDevice
from easy_biologic.program import BiologicProgram
import pandas as pd

# Local application imports
from ....core.connection import match_current_ip_address
from ....core import datalogger
from ... import Measurer, ProgramDetails

# Clear logging setup from easy_biologic
for handler in logging.root.handlers:
    if isinstance(handler, logging.StreamHandler) and handler.level == logging.NOTSET:
        handler.setLevel(logging.WARNING)

# INITIALIZING
nest_asyncio.apply()
path = Path(easy_biologic.__path__[0]) / 'techniques_version.json'
with open(path, 'r+') as f:
    content = json.load(f)
    version = content.get('version', None)
    if version not in ('6.04',):
        print(f"Updating easy-biologic techniques version from {version} to 6.04")
        f.seek(0)
        f.truncate()
        f.write(json.dumps({'version': '6.04'}, indent=4))
        
def parse_docstring(program_class:BiologicProgram, verbose:bool = True) -> ProgramDetails:
    method = getattr(program_class, '__init__')
    doc = getdoc(method)
    args_dict: dict[str, dict[str,Any]] = dict()
    parameter_descriptions: dict[str,str] = {}
    if doc is not None and 'Params are' in doc:
        arg_lines = doc.split(':param')[2].split('Params are', maxsplit=1)[1].splitlines()
        arg_lines = [arg_line.strip() for arg_line in arg_lines if len(arg_line)]
        args: dict[str,str] = {}
        previous_line_head = ''
        for line in arg_lines:
            line_head, line_tail = line.split(' ',maxsplit=1)
            if line_head.endswith(':') and not line_head.startswith('[Default:') and not line_head.startswith('[Defualt:'):
                args[line_head[:-1]] = line_tail.strip()
                previous_line_head = line_head[:-1]
            else:   # extra description / default in new line
                if previous_line_head in args:
                    args[previous_line_head] = ' '.join([args[previous_line_head], line])
        
        for arg, text in args.items():
            if '[Default:' in text or '[Defualt:' in text:
                sep = '[Default:' if '[Default:' in text else '[Defualt:'
                text = text.strip()[:-1] # remove the last character (i.e. ']')
                description, default = text.split(sep, maxsplit=1)
                default = default.strip()
                default = default.split(' ')[0] if ' ' in default else default
                try:
                    default_value = ast.literal_eval(default)
                except ValueError:
                    try:
                        value = ecl
                        for attr in default.split('.'):
                            if hasattr(value, attr):
                                value = getattr(value, attr)
                        default_value = value
                    except AttributeError:
                        default_value = default
                args_dict[arg] = {
                    # 'description': description.strip(),
                    'annotation': type(default_value).__name__,
                    'default': default_value
                }
                parameter_descriptions[arg] = description.strip()
            else:
                args_dict[arg] = {'annotation': ''}
                parameter_descriptions[arg] = text.strip()
        
        parameters = [Parameter(k,Parameter.KEYWORD_ONLY, **v) for k,v in args_dict.items()]
        signature = Signature(parameters=parameters)
        
    details = ProgramDetails(
        signature=signature,
        description=getdoc(program_class),
        parameter_descriptions=parameter_descriptions,
        return_descriptions=dict()
    )
    if verbose:
        print(details)
    return details


class BioLogic(Measurer):
    _default_flags: SimpleNamespace[str,bool] = SimpleNamespace(busy=False, connected=False, verbose=False)
    def __init__(self, 
        host:str = '192.109.209.128', 
        timeout:int = 5, 
        populate_info:bool = True, 
        *, 
        verbose:bool = False, 
        **kwargs
    ):
        """
        Initialize Measurer class

        Args:
            verbose (bool, optional): verbosity of class. Defaults to False.
        """
        self.device: BiologicDevice|None = None
        self._connection_details = dict(host=host, timeout=timeout, populate_info=populate_info)
        if not match_current_ip_address(host):
            raise ConnectionError(f"Device IP address {host} does not match current network IP address.")
        try: 
            self.device = BiologicDevice(host, timeout=timeout, populate_info=populate_info)
        except ecl.EcError as e:
            print(e)
            raise ConnectionError('Could not establish communication with instrument.')
        super().__init__(device=self.device,verbose=verbose, **kwargs)
        self._records_cache: dict[int, deque[tuple[NamedTuple, datetime]]] = dict()
        return
    
    @property
    def connection_details(self) -> dict:
        """Connection details for the device"""
        return self._connection_details
    
    @property
    def host(self) -> str:
        """BioLogicDevice address"""
        return self._connection_details.get('host', '')
    @host.setter
    def host(self, value:str):
        self._connection_details['host'] = value
        return
    
    @property
    def timeout(self) -> int:
        """Device timeout"""
        return self._connection_details.get('timeout', '')
    @timeout.setter
    def timeout(self, value:int):
        self._connection_details['timeout'] = value
        return
    
    @property
    def is_connected(self) -> bool:
        """Whether the device is connected"""
        self.flags.connected = self.device.is_connected()
        return self.flags.connected

    def connect(self):
        """Connect to the device"""
        if self.is_connected:
            return
        if not match_current_ip_address(self.host):
            raise ConnectionError(f"Device IP address {self.host} does not match current network IP address.")
        try:
            self.device.connect()
        except (RuntimeError, ecl.EcError) as e:
            self._logger.error(f"Failed to connect to {self.host}")
            self._logger.debug(e)
        else:
            self._logger.info(f"Connected to {self.host}")
            time.sleep(self.timeout)
        self.flags.connected = self.is_connected
        return
    
    def disconnect(self):
        """Disconnect from the device"""
        if not self.is_connected:
            return
        try:
            self.device.disconnect()
        except (RuntimeError, ecl.EcError) as e:
            self._logger.error(f"Failed to disconnect from {self.host}")
            self._logger.debug(e)
        else:
            self._logger.info(f"Disconnected from {self.host}")
        self.flags.connected = self.is_connected
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
        assert issubclass(self.program, BiologicProgram), "No Program loaded"
        channels = parameters.pop('channels', [0])
        new_run = self.program(
            device = self.device, 
            params = parameters,
            channels = channels
        )
        
        self.n_runs += 1
        self._logger.info(f"Run ID: {self.n_runs}")
        self.runs[self.n_runs] = new_run
        if not blocking:
            thread = threading.Thread(target=new_run.run)
            thread.start()
            self._threads['measure'] = thread
            self.flags.busy = True
            return
        new_run.run()
        self.records = self.getData(self.n_runs)
        self.flags.busy = False
        return self.records_df
    
    def loadProgram(self, program: BiologicProgram, docstring_parser: Callable[[Any,bool],ProgramDetails]|None = None):
        """
        Load a program to the Measurer
        
        Args:
            program (BiologicProgram): program to load
        """
        assert issubclass(program, BiologicProgram), "Ensure program type is a subclass of Program"
        self.program = program
        if docstring_parser is None:
            docstring_parser = parse_docstring
        self.measure.__func__.__doc__ = docstring_parser(program, verbose=self.verbose)
        return
     
    def clearCache(self):
        """Clear the cache"""
        self.buffer.clear()
        self.records.clear()
        self.n_runs = 0
        self.runs.clear()
        self._threads.clear()
        self._records_cache.clear()
        return
    
    def getData(self, run_id:int,  *args, **kwargs) -> Any|None:
        if run_id in self._records_cache:
            self.records = self._records_cache[run_id]
            return self.records
        
        program = self.runs.get(run_id, None)
        if program is None:
            self._logger.warning(f"Run ID {run_id} not found.")
            return None
        if not isinstance(program, BiologicProgram):
            self._logger.warning("Program not of type BiologicProgram.")
            return None
        if len(program.data) == 0:
            self._logger.warning("No data found.")
            return None
        
        records = []
        data_name = None
        for chn,data in program.data.items():  # dict of {channel: list[namedtuple]}
            if data_name is None and len(data):
                datum: NamedTuple = data[0]
                data_name = datum.__class__.__name__
                field_titles = ['channel'] + list(datum._fields)
                field_types = [int] + [type(d) for d in datum]
                fields = [(title,type_) for title,type_ in zip(field_titles,field_types)]
                self._logger.info(field_titles)
                data_type = NamedTuple(data_name, fields)
            channel_data = [data_type(chn, *datum) for datum in data]
            records.extend(channel_data)
        now = datetime.now()
        dated_records = deque([(r,now) for r in records])  
        self._records_cache[run_id] = deque([(r,now) for r in records])
        self.records = dated_records
        return self.records
    
    def getDataframe(self, data_store: Iterable[tuple[NamedTuple, datetime]]) -> pd.DataFrame:
        """
        Get dataframe of data collected
        
        Args:
            data_store (Iterable[tuple[NamedTuple, datetime]]): data store
            
        Returns:
            pd.DataFrame: dataframe of data collected
        """
        if len(data_store) == 0:
            return pd.DataFrame()
        field = data_store[0][0]._fields
        return datalogger.get_dataframe(data_store=data_store, fields=field)
    
    def saveData(self, filepath:str|Path):
        """
        Save data to file
        
        Args:
            filepath (str|Path): path to save file
        """
        if not len(self.records):
            raise
        self.records_df.to_csv(filepath)
        return
    
    def record(self, on: bool, show: bool = False, clear_cache: bool = False):
        raise NotImplementedError
    
    def stream(self, on: bool, show: bool = False):
        raise NotImplementedError
