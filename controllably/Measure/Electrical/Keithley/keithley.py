# -*- coding: utf-8 -*-
from __future__ import annotations
from collections import deque
from datetime import datetime
from pathlib import Path
import threading
import time
from types import SimpleNamespace
from typing import NamedTuple, Any, Iterable

# Third party imports
import pandas as pd
from pymeasure.instruments.keithley.buffer import KeithleyBuffer
from pymeasure.instruments import keithley, SCPIMixin, Instrument
from pyvisa import VisaIOError

# Local application imports
from ....core.connection import match_current_ip_address
from ....core import datalogger
from ... import Measurer, Program

KeithleyBase = type('KeithleyBase', (KeithleyBuffer,SCPIMixin,Instrument), {})

class Keithley(Measurer):
    _default_flags: SimpleNamespace[str,bool] = SimpleNamespace(busy=False, connected=False, verbose=False)
    def __init__(self, 
        keithley_class: str,
        host: str|None = None,
        name: str|None = None,
        *, 
        adapter: str|None = None,
        read_termination: str ='\n', 
        write_termination: str = '\n',
        timeout: int = 2000,     # in milliseconds
        verbose: bool = False, 
        **kwargs
    ):
        """
        Initialize Measurer class

        Args:
            verbose (bool, optional): verbosity of class. Defaults to False.
        """
        assert hasattr(keithley, keithley_class), f"Keithley class {keithley_class} not found in pymeasure.instruments.keithley"
        device_type = getattr(keithley, keithley_class)
        assert all(issubclass(device_type, superclass) for superclass in (KeithleyBuffer,SCPIMixin,Instrument)), f"Keithley class {keithley_class} not a subclass of KeithleyBuffer, SCPIMixin and Instrument"
        
        self.device: KeithleyBase|None = None
        self._device_type = device_type
        
        if host is None and adapter is None:
            raise ValueError("Either host or adapter must be provided")
        
        kwargs['adapter'] = adapter or f'TCPIP0::{host}::5025::SOCKET'
        kwargs['read_termination'] = read_termination
        kwargs['write_termination'] = write_termination
        kwargs['timeout'] = timeout
        if name is not None:
            kwargs['name'] = name
        self._connection_details = kwargs
        
        self._connect(**self._connection_details)
        super().__init__(device=self.device, verbose=verbose, **kwargs)
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
    def name(self) -> str:
        """Device name"""
        return self.device.name if isinstance(self.device,Instrument) else self.connection_details.get('name', '')
    
    @property
    def is_connected(self) -> bool:
        """Whether the device is connected"""
        connected = True
        try:
            _ = self.device.id
        except VisaIOError:
            connected = False
        self.flags.connected = connected
        return self.flags.connected

    def _connect(self, **kwargs):
        adapter: str = kwargs.get('adapter','')
        if adapter.startswith('TCPIP0'):
            host = adapter.split('::')[1]
            if not match_current_ip_address(host):
                raise ConnectionError(f"Device IP address {host} does not match current network IP address.")
        try:
            self.device = self._device_type(**kwargs)
            for _ in range(3):
                self.device.write(':SYST:BEEP 440,0.1')
                time.sleep(0.1)
        except Exception as e:
            raise e

    def connect(self):
        """Connect to the device"""
        if self.is_connected:
            return
        # if issubclass(self.device.__class__, Instrument):
        #     self.device.shutdown()
        self._connect(**self._connection_details)
        self._logger.info(f"Connected to {self.host}")
        time.sleep(self.timeout)
        self.flags.connected = self.is_connected
        self.device.reset()
        return
    
    def disconnect(self):
        """Disconnect from the device"""
        if not self.is_connected:
            return
        try:
            self.device.shutdown()
        except Exception as e:
            raise e
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
        assert issubclass(self.program, Program), "No Program loaded"
        channels = parameters.pop('channels', [0])
        new_run = self.program(
            device = self, 
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
        if not isinstance(program, Program):
            self._logger.warning("Program not of type Program.")
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
