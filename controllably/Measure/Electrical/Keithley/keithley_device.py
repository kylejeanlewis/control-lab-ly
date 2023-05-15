# %% -*- coding: utf-8 -*-
"""
This module holds the instrument class for tools from Keithley.

Classes:
    KeithleyDevice (Instrument)
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
    KeithleyDevice provides methods to interface with the potentiometer from Keithley
    
    ### Constructor
    Args:
        `ip_address` (str): IP address of device
        `name` (str, optional): name of device. Defaults to 'def'.
        
    ### Attributes
    - `active_buffer` (str): name of active buffer in Keithley
    - `name` (str): name of device
    - `sense` (SenseDetails): parameters for Keithley's sense terminal
    - `source` (SourceDetails): parameters for Keithley's source terminal
    
    ### Properties
    - `buffer_name` (str): name of buffer
    - `fields` (tuple[str]): tuple of data fields to read from device
    
    ### Methods
    - `beep`: make device emit a beep sound
    - `clearBuffer`: clear the buffer on the device
    - `configureSense`: configure the sense terminal
    - `configureSource`: configure the source terminal
    - `disconnect`: disconnect from device (NOTE: not implemented)
    - `getBufferIndices`: get the buffer indices where the the data start and end
    - `getErrors`: get error messages from device
    - `getStatus`: get status of device
    - `makeBuffer`: create a new buffer on the device
    - `read`: read the latest data from buffer
    - `readAll`: read the data from buffer after a series of measurements
    - `recallState`: recall a previously saved device setting
    - `reset`: reset the device
    - `run`: start the measurement
    - `saveState`: save current settings on device
    - `sendCommands`: write a series of commands to device
    - `setSource`: set the source to a specified value
    - `stop`: abort all actions
    - `toggleOutput`: turn on or off output from device
    """
    
    _default_buffer = 'defbuffer1'
    def __init__(self, ip_address:str, name:str = 'def', **kwargs):
        """
        Instantiate the class
        
        Args:
            ip_address (str): IP address of device
            name (str, optional): name of device. Defaults to 'def'.
        """
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
        Make device emit a beep sound

        Args:
            frequency (int, optional): frequency of sound wave. Defaults to 440.
            duration (int, optional): duration to play beep. Defaults to 1.
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
        Clear the buffer on the device

        Args:
            name (Optional[str] , optional): name of buffer to clear. Defaults to None.
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
        Configure the sense terminal

        Args:
            func (str): name of function, choice from current, resistance, and voltage
            limit (Union[str, float, None], optional): sensing range. Defaults to 'DEFault'.
            four_point (bool, optional): whether to use four-point probe measurement. Defaults to True.
            count (int, optional): number of readings to measure for each condition. Defaults to 1.
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
        Configure the source terminal

        Args:
            func (str): name of function, choice from current and voltage
            limit (Union[str, float, None], optional): sourcing range. Defaults to None.
            measure_limit (Union[str, float, None], optional): limit imposed on the measurement range. Defaults to 'DEFault'.
        """
        self.source = SourceDetails(func, limit, measure_limit)
        self._query(f'SOURce:FUNCtion {self.source.function_type}')
        return self.sendCommands(commands=self.source.get_commands())
    
    def disconnect(self):       # NOTE: not implemented
        return super().disconnect()
    
    def getBufferIndices(self, name:Optional[str] = None) -> tuple[int]:
        """
        Get the buffer indices where the the data start and end

        Args:
            name (Optional[str], optional): name of buffer. Defaults to None.

        Returns:
            tuple[int]: start and end buffer indices
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
        Get error messages from device
        
        Returns:
            list[str]: list of error messages from device
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
            str: device status
        """
        return self._query('TRIGger:STATe?')
    
    def makeBuffer(self, name:Optional[str] = None, buffer_size:int = 100000):
        """
        Create a new buffer on the device

        Args:
            name (Optional[str] , optional): buffer name. Defaults to None.
            buffer_size (int, optional): buffer size. Defaults to 100000.
        """
        name = self.buffer_name if name is None else name
        self.active_buffer = name
        if buffer_size < 10 and buffer_size != 0:
            buffer_size = 10
        return self._query(f'TRACe:MAKE "{name}",{buffer_size}')
    
    def read(self, 
        name: Optional[str] = None, 
        fields: tuple[str] = ('SOURce','READing', 'SEConds'), 
        average: bool = True
    ) -> pd.DataFrame:
        """
        Read the latest data fom buffer

        Args:
            name (Optional[str], optional): buffer name. Defaults to None.
            fields (tuple[str], optional): fields of interest. Defaults to ('SOURce','READing', 'SEConds').
            average (bool, optional): whether to average the data of multiple readings. Defaults to True.

        Returns:
            pd.DataFrame: dataframe of measurements
        """
        return self._read(bulk=False, name=name, fields=fields, average=average)
        
    def readAll(self, 
        name: Optional[str] = None, 
        fields: tuple[str] = ('SOURce','READing', 'SEConds'), 
        average: bool = True
    ) -> pd.DataFrame:
        """
        Read the data from buffer after a series of measurements

        Args:
            name (Optional[str], optional): buffer name. Defaults to None.
            fields (tuple[str], optional): fields of interest. Defaults to ('SOURce','READing', 'SEConds').
            average (bool, optional): whether to average the data of multiple readings. Defaults to True.

        Returns:
            pd.DataFrame: dataframe of measurements
        """
        return self._read(bulk=True, name=name, fields=fields, average=average)
    
    def recallState(self, state:int):
        """
        Recall a previously saved device setting

        Args:
            state (int): state index to recall from

        Raises:
            ValueError: Select an index from 0 to 4
        """
        if not 0 <= state <= 4:
            raise ValueError("Please select a state index from 0 to 4")
        return self._query(f'*RCL {state}')
    
    def reset(self):
        """Reset the device"""
        self.active_buffer = self._default_buffer
        self.sense = SenseDetails()
        self.source = SourceDetails()
        return self._query('*RST')
    
    def run(self, sequential_commands:bool = True):
        """
        Start the measurement

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
        Save current settings on device

        Args:
            state (int): state index to save to

        Raises:
            ValueError: Select an index from 0 to 4
        """
        if not 0 <= state <= 4:
            raise ValueError("Please select a state index from 0 to 4")
        return self._query(f'*SAV {state}')
    
    def sendCommands(self, commands:list[str]):
        """
        Write a series of commands to device

        Args:
            commands (list[str]): list of commands strings
        """
        for command in commands:
            self._query(command)
        return
    
    def setSource(self, value:float):
        """
        Set the source to a specified value

        Args:
            value (float): value to set source to 

        Raises:
            ValueError: Please set a source value within limits
        """
        unit = 'A' if self.source.function_type == 'CURRent' else 'V'
        capacity = 1 if self.source.function_type == 'CURRent' else 200
        limit = capacity if type(self.source.range_limit) is str else self.source.range_limit
        
        if abs(value) > limit:
            raise ValueError(f'Please set a source value between -{limit} and {limit} {unit}')
        self.source._count += 1
        return self._query(f'SOURce:{self.source.function_type} {value}')

    def stop(self):
        """Abort all actions"""
        return self._query('ABORt')

    def toggleOutput(self, on:bool):
        """
        Turn on or off output from device

        Args:
            on (bool): whether to turn on output
        """
        state = 'ON' if on else 'OFF'
        return self._query(f'OUTPut {state}')
    
    # Protected method(s)
    def _connect(self, ip_address:str):
        """
        Connection procedure for tool
        
        Args:
            ip_address (str): IP address of device
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
            reply (str): raw response string from device

        Returns:
            Union[float, str, tuple[Union[float, str]]]: variable output including floats, strings, and tuples
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
        """
        Write command to and read response from device

        Args:
            command (str): SCPI command string

        Returns:
            str: response string
        """
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
            bulk (bool): whether to read data after a series of measurements
            name (Optional[str], optional): buffer name. Defaults to None.
            fields (tuple[str], optional): fields of interest. Defaults to ('SOURce','READing', 'SEConds').
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
        """
        Write command to device

        Args:
            command (str): SCPI command string

        Returns:
            bool: whether command was sent successfully
        """
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
