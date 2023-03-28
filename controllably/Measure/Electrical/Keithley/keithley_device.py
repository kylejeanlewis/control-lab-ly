# %% -*- coding: utf-8 -*-
"""
Created: Tue 2022/11/02 17:13:35
@author: Chang Jie

Notes / actionables:
- validation on copper
"""
# Standard library imports
from __future__ import annotations
import numpy as np
import pandas as pd
from typing import Optional, Union

# Third party imports
import pyvisa as visa # pip install -U pyvisa

# Local application imports
from ...instrument_utils import Instrument
from .keithley_lib import SenseDetails, SourceDetails
print(f"Import: OK <{__name__}>")

class KeithleyDevice(Instrument):
    """
    Keithley device object
    
    Args:
        ip_address (str): IP address of Keithley
        name (str, optional): nickname for Keithley. Defaults to 'def'.
    """
    _default_buffer = 'defbuffer1'
    def __init__(self, ip_address:str, name:str = 'def', **kwargs):
        super().__init__(**kwargs)
        self.name = name
        self._fields = ('',)
        
        self.active_buffer = self._default_buffer
        self.sense = SenseDetails()
        self.source = SourceDetails()
        self._connect(ip_address)
        return
    
    def __info__(self) -> str:
        """
        Get device system info

        Returns:
            str: system info
        """
        return self._query('*IDN?')
    
    # Properties
    @property
    def buffer_name(self) -> str:
        return f'{self.name}buffer'
    
    @property
    def fields(self) -> tuple[str]:
        return self._fields
    @fields.setter
    def fields(self, value:tuple[str]):
        if len(value) > 14:
            raise RuntimeError("Please input 14 or fewer fields to read out from instrument.")
        self._fields = tuple(value)
        return
    
    def beep(self, frequency:int = 440, duration:float = 1):
        """
        Set off beeper

        Args:
            frequency (int, optional): frequency of sound wave. Defaults to 440.
            duration (int, optional): duration to play beep. Defaults to 1.

        Raises:
            Exception: Select a valid frequency
            Exception: select a valid duration
        """
        if not 20<=frequency<=8000:
            print('Please enter a frequency between 20 and 8000')
            print('Defaulting to 440 Hz')
            frequency = 440
        if not 0.001<=duration<=100:
            print('Please enter a duration between 0.001 and 100')
            print('Defaulting to 1 s')
            duration = 1
        return self._query(f'SYSTem:BEEPer {frequency},{duration}')
    
    def clearBuffer(self, name:Optional[str] = None):
        """
        Clear buffer

        Args:
            name (str, optional): name of buffer to clear. Defaults to None.
        """
        name = self.active_buffer if name is None else name
        return self._query(f'TRACe:CLEar "{name}"')
    
    def configureSense(self, 
        func: str, 
        limit: Union[str, float, None] = 'DEFault',
        four_point: bool = True,
        count: int = 1
    ):
        """
        Configure the sense function

        Args:
            func (str): function to be read, from current, resistance, and voltage
            limit (str or float, optional): sensing range. Defaults to 'DEFault'.
            probe_4_point (bool, optional): whether to use 4-point reading. Defaults to True.
            unit (str, optional): units for reading. Defaults to None.
            count (int, optional): number of readings per measurement. Defaults to 1.

        Raises:
            Exception: Select a valid count number
        """
        self.sense = SenseDetails(func, limit, four_point, count)
        self._query(f'SENSe:FUNCtion "{self.sense.function_type}"')
        return self.sendCommands(commands=self.sense.get_commands())
    
    def configureSource(self, 
        func: str, 
        limit: Union[str, float, None] = None,
        measure_limit: Union[str, float, None] = 'DEFault'
    ):
        """
        Configure the source function

        Args:
            func (str): function to be sourced, from current, and voltage
            limit (str or float, optional): sourcing range. Defaults to None.
            measure_limit (str or float, optional): limit imposed on the measurement range. Defaults to 'DEFault'.
        """
        self.source = SourceDetails(func, limit, measure_limit)
        self._query(f'SOURce:FUNCtion {self.source.function_type}')
        return self.sendCommands(commands=self.source.get_commands())
    
    def disconnect(self):       # NOTE: not implemented
        return super().disconnect()
    
    def getBufferIndices(self, name:Optional[str] = None) -> tuple[int]:
        """
        Get the start and end buffer indices

        Args:
            name (str, optional): name of buffer. Defaults to None.

        Returns:
            list: start and end buffer indices
        """
        name = self.buffer_name if name is None else name
        reply = self._query(f'TRACe:ACTual:STARt? "{name}" ; END? "{name}"')
        try:
            start,end = self._parse(reply=reply)
            start = int(start)
            end = int(end)
        except ValueError:
            return 0,0
        start = max(1, start)
        end = max(start, end)
        return start,end
    
    def getErrors(self) -> list[str]:
        """
        Get Errors from Keithley
        """
        errors = []
        reply = ''
        while not reply.isnumeric():
            reply = self._query('SYSTem:ERRor:COUNt?')
            print(reply)
        num_errors = int(reply)
        for i in range(num_errors):
            reply = self._query('SYSTem:ERRor?')
            error = self._parse(reply=reply)
            errors.append((error))
            print(f'>>> Error {i+1}: {error}')
        return errors
    
    def getStatus(self) -> str:
        """
        Get status of device

        Returns:
            str: device state
        """
        return self._query('TRIGger:STATe?')
    
    def makeBuffer(self, name:Optional[str] = None, buffer_size:int = 100000):
        """
        Make a buffer on the device

        Args:
            name (str, optional): buffer name. Defaults to None.
            buffer_size (int, optional): buffer size. Defaults to 100000.
        """
        name = self.buffer_name if name is None else name
        self.active_buffer = name
        if buffer_size < 10 and buffer_size != 0:
            buffer_size = 10
        return self._query(f'TRACe:MAKE "{name}",{buffer_size}')
    
    def recallState(self, state:int):
        """
        Recall a previously saved settings of device

        Args:
            state (int): state index to recall from

        Raises:
            Exception: Select an index from 0 to 4
        """
        if not 0 <= state <= 4:
            raise Exception("Please select a state index from 0 to 4")
        return self._query(f'*RCL {state}')
    
    def reset(self):
        """
        Reset the device
        """
        self.active_buffer = self._default_buffer
        self.sense = SenseDetails()
        self.source = SourceDetails()
        return self._query('*RST')
    
    def run(self, sequential_commands:bool = True):
        """
        Initialise the measurement

        Args:
            sequential_commands (bool, optional): whether commands whose operations must finish before the next command is executed. Defaults to True.
        """
        if sequential_commands:
            commands = [f'TRACe:TRIGger "{self.active_buffer}"']
        else:
            commands = ['INITiate ; *WAI']
        return self.sendCommands(commands=commands)
    
    def saveState(self, state:int):
        """
        Save current settings / state of device

        Args:
            state (int): state index to save to

        Raises:
            Exception: Select an index from 0 to 4
        """
        if not 0 <= state <= 4:
            raise Exception("Please select a state index from 0 to 4")
        return self._query(f'*SAV {state}')
    
    def sendCommands(self, commands:list[str]):
        """
        Write multiple commands to device

        Args:
            commands (list): list of commands to write
        """
        for command in commands:
            self._query(command)
        return
    
    def setSource(self, value:float):
        """
        Set source to desired value

        Args:
            value (int or float): value to set source to 

        Raises:
            Exception: Set a value within limits
        """
        unit = 'A' if self.source.function_type == 'CURRent' else 'V'
        capacity = 1 if self.source.function_type == 'CURRent' else 200
        limit = capacity if type(self.source.range_limit) is str else self.source.range_limit
        
        if abs(value) > limit:
            raise ValueError(f'Please set a source value between -{limit} and {limit} {unit}')
        self.source._count += 1
        return self._query(f'SOURce:{self.source.function_type} {value}')

    def stop(self):
        """
        Abort all actions
        """
        return self._query('ABORt')

    def toggleOutput(self, on:bool):
        """
        Toggle turning on output

        Args:
            on (bool): whether to turn on output
        """
        state = 'ON' if on else 'OFF'
        return self._query(f'OUTPut {state}')
    
    # Protected method(s)
    def _connect(self, ip_address:str):
        """
        Establish connection with Keithley
        
        Args:
            ip_address (str, optional): IP address of Keithley. Defaults to None
            
        Returns:
            Instrument: Keithley object
        """
        print("Setting up Keithley communications...")
        self.connection_details['ip_address'] = ip_address
        device = None
        try:
            rm = visa.ResourceManager('@py')
            device = rm.open_resource(f"TCPIP0::{ip_address}::5025::SOCKET")
            device.write_termination = '\n'
        except Exception as e:
            print("Unable to connect to Keithley")
            if self.verbose:
                print(e) 
        else:
            device.read_termination = '\n'
            self.device = device
            self.setFlag(connected=True)
            self.beep(500)
            print(f"{self.__info__()}")
            print(f"{self.name.title()} Keithley ready")
        self.device = device
        return

    def _parse(self, reply:str) -> Union[float, str, tuple[Union[float, str]]]:
        """
        Parse the response from device

        Args:
            raw_reply (str): raw response string from device

        Returns:
            float, str, or list: float for numeric values, str for strings, list for multiple replies
        """
        if ',' not in reply and ';' not in reply:
            try:
                reply = float(reply)
            except ValueError:
                pass
            return reply
        
        if ',' in reply:
            replies = reply.split(',')
        elif ';' in reply:
            replies = reply.split(';')

        outs = []
        for reply in replies:
            try:
                out = float(reply)
            except ValueError:
                pass
            outs.append(out)
        if self.verbose:
            print(tuple(outs))
        return tuple(outs)
    
    def _query(self, command:str) -> str:
        if self.verbose:
            print(command)
        
        if not self.isConnected():
            print(command)
            dummy_return = ';'.join(['0' for _ in range(command.count(';')+1)]) if "?" in command else ''
            return dummy_return
        
        if "?" not in command:
            self._write(command)
            return ''
        
        reply = ''
        try:
            reply = self.device.query(command)
            # self.device.write(command)
            # while raw_reply is None:
            #     raw_reply = self.device.read()
        except visa.VisaIOError:
            self.getErrors()
        else:
            if self.verbose and "*WAI" not in command:
                self.getErrors()
        return reply
    
    def _read(self, 
        bulk: bool,
        name: Optional[str] = None, 
        fields: tuple[str] = ('SOURce','READing', 'SEConds'), 
        average: bool = True
    ) -> pd.DataFrame:
        """
        Read all data on buffer

        Args:
            name (str, optional): buffer name. Defaults to None.
            fields (list, optional): fields of interest. Defaults to ['SOURce','READing', 'SEConds'].
            average (bool, optional): whether to average the data of multiple readings. Defaults to True.

        Returns:
            pd.DataFrame: dataframe of measurements
        """
        name = self.active_buffer if name is None else name
        self.fields = fields
        count = int(self.sense.count)
        start,end = self.getBufferIndices(name=name)
        
        start = start if bulk else max(1, end-count+1)
        if not all([start,end]): # dummy data
            num_rows = count * max(1, int(self.source._count)) if bulk else count
            data = [0] * num_rows * len(self.fields)
        else:
            reply = self._query(f'TRACe:DATA? {int(start)},{int(end)},"{name}",{",".join(self.fields)}')
            data = self._parse(reply=reply)
        
        data = np.reshape(np.array(data), (-1,len(self.fields)))
        df = pd.DataFrame(data, columns=self.fields)
        if average and count > 1:
            avg = df.groupby(np.arange(len(df))//count).mean()
            std = df.groupby(np.arange(len(df))//count).std()
            df = avg.join(std, rsuffix='_std')
        return df
    
    def _write(self, command:str) -> bool:
        if self.verbose:
            print(command)
        try:
            self.device.write(command)
        except visa.VisaIOError:
            self.getErrors()
            return False
        if self.verbose and "*WAI" not in command:
            self.getErrors()
        return True
