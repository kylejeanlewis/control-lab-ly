# %% -*- coding: utf-8 -*-
"""
This module holds the instrument class for tools from Keithley.

Classes:
    KeithleyDevice (Instrument)
"""
# Standard library imports
from __future__ import annotations
import ipaddress
import logging
import numpy as np
import pandas as pd
import socket
from typing import Iterable

# Third party imports
import pyvisa as visa # pip install -U pyvisa; pip install -U pyvisa-py

# Local application imports
from ...instrument_utils import Instrument
from .keithley_lib import SenseDetails, SourceDetails

logger = logging.getLogger(__name__)
logger.debug(f"Import: OK <{__name__}>")

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
    - `ip_address` (str): IP address of Keithley
    
    ### Methods
    - `beep`: make device emit a beep sound
    - `clearBuffer`: clear the buffer on the device
    - `configureSense`: configure the sense terminal
    - `configureSource`: configure the source terminal
    - `disconnect`: disconnect from device
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
        self._model = ''
        
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
        response = self._query('*IDN?')
        self._model = response.split(',')[1].split(' ')[1]
        return response
    
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
    
    @property
    def ip_address(self) -> str:
        return self.connection_details.get('ip_address', '')
    
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
    
    def clearBuffer(self, name:str|None = None):
        """
        Clear the buffer on the device

        Args:
            name (str|None , optional): name of buffer to clear. Defaults to None.
        """
        name = self.active_buffer if name is None else name
        return self._query(f'TRACe:CLEar "{name}"')
    
    def clearErrors(self):
        """Clear errors from event logs"""
        return self._write('SYSTem:CLEar')
    
    def configureSense(self, 
        func: str, 
        limit: Iterable|None = 'DEFault',
        four_point: bool = True,
        count: int = 1
    ):
        """
        Configure the sense terminal

        Args:
            func (str): name of function, choice from current, resistance, and voltage
            limit (str|float|None, optional): sensing range. Defaults to 'DEFault'.
            four_point (bool, optional): whether to use four-point probe measurement. Defaults to True.
            count (int, optional): number of readings to measure for each condition. Defaults to 1.
        """
        self.sense = SenseDetails(func, limit, four_point, count)
        self.setFunction(self.sense.function_type)
        # self._query(f'SENSe:FUNCtion "{self.sense.function_type}"')
        return self.sendCommands(commands=self.sense.get_commands())
    
    def configureSource(self, 
        func: str, 
        limit: str|float|None = None,
        measure_limit: str|float|None = 'DEFault'
    ):
        """
        Configure the source terminal

        Args:
            func (str): name of function, choice from current and voltage
            limit (str|float|None, optional): sourcing range. Defaults to None.
            measure_limit (str|float|None, optional): limit imposed on the measurement range. Defaults to 'DEFault'.
        """
        self.source = SourceDetails(func, limit, measure_limit)
        self.setFunction(self.source.function_type, sense=False)
        # self._query(f'SOURce:FUNCtion {self.source.function_type}')
        return self.sendCommands(commands=self.source.get_commands())
    
    def disconnect(self):
        """Disconnect from device"""
        try:
            self.device.close()
        except Exception as e:
            if self.verbose:
                print(e)
        self.setFlag(connected=False)
        return
    
    def getBufferIndices(self, name:str|None = None) -> tuple[int]:
        """
        Get the buffer indices where the the data start and end

        Args:
            name (str|None, optional): name of buffer. Defaults to None.

        Returns:
            tuple[int]: start and end buffer indices
        """
        name = self.buffer_name if name is None else name
        reply = self._query(f'TRACe:ACTual:STARt? "{name}" ; END? "{name}"')
        response = self._parse(reply=reply)
        if '__len__' not in response.__dir__():
            return 0,0
        try:
            start,end = response
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
        self.clearErrors()
        return errors
    
    def getStatus(self) -> str:
        """
        Get status of device

        Returns:
            str: device status
        """
        return self._query('TRIGger:STATe?')
    
    def makeBuffer(self, name:str|None = None, buffer_size:int = 100000):
        """
        Create a new buffer on the device

        Args:
            name (str|None , optional): buffer name. Defaults to None.
            buffer_size (int, optional): buffer size. Defaults to 100000.
        """
        name = self.buffer_name if name is None else name
        self.active_buffer = name
        if buffer_size < 10 and buffer_size != 0:
            buffer_size = 10
        return self._query(f'TRACe:MAKE "{name}",{buffer_size}')
    
    def read(self,  # TODO: improve compatibility of read functions with other standards
        name: str|None = None, 
        fields: tuple[str] = ('SOURce','READing', 'SEConds'), 
        average: bool = True,
        quick: bool = False
    ) -> pd.DataFrame:
        """
        Read the latest data fom buffer

        Args:
            name (str|None, optional): buffer name. Defaults to None.
            fields (tuple[str], optional): fields of interest. Defaults to ('SOURce','READing', 'SEConds').
            average (bool, optional): whether to average the data of multiple readings. Defaults to True.
            quick (bool, optional): whether to take a quick reading using existing Sense function and settings. Defaults to False.

        Returns:
            pd.DataFrame: dataframe of measurements
        """
        return self._read(bulk=False, name=name, fields=fields, average=average, quick=quick)
        
    def readAll(self, 
        name: str|None = None, 
        fields: tuple[str] = ('SOURce','READing', 'SEConds'), 
        average: bool = True
    ) -> pd.DataFrame:
        """
        Read the data from buffer after a series of measurements

        Args:
            name (str|None, optional): buffer name. Defaults to None.
            fields (tuple[str], optional): fields of interest. Defaults to ('SOURce','READing', 'SEConds').
            average (bool, optional): whether to average the data of multiple readings. Defaults to True.

        Returns:
            pd.DataFrame: dataframe of measurements
        """
        return self._read(bulk=True, name=name, fields=fields, average=average)
    
    def readline(self) -> bytes:
        """
        Read latest data point from buffer

        Returns:
            bytes: latest data point value
        """
        df = self._read(bulk=False, fields=('READing',), quick=True)
        return str(df.iat[0,0]).encode()
        # return self._query('READ?').encode()
    
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
        self.clearErrors()
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
    
    def setDisplay(self, brightness:int = 50):
        """
        Set display on the instrument

        Args:
            brightness (int, optional): display brightness values from [0,25,50,75,100]. Defaults to 50.
        """
        state = 'ON' if brightness else 'OFF'
        values = [25,50,75,100]
        if brightness:
            diff = [abs(brightness-b) for  b in values]
            brightness_value = values[diff.index(min(diff))]
            state += str(brightness_value)
        return self._query(f'DISPlay:LIGHt:STATe {state}')
    
    def setFunction(self, function:str, sense:bool = True):
        """
        Set the function for either the sense or source terminals

        Args:
            function (str): type of function
            sense (bool, optional): whether to set the sense terminal. Defaults to True.
        """
        terminal = 'SENSe' if sense else 'SOURce'
        function = f'"{function}"' if sense else function
        return self._query(f'{terminal}:FUNCtion {function}')
    
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
                
        # Check if machine is connected to the same network as device
        hostname = socket.getfqdn()
        local_ip = socket.gethostbyname_ex(hostname)[2][0]
        local_network = f"{'.'.join(local_ip.split('.')[:-1])}.0/24"
        if ipaddress.ip_address(ip_address) not in ipaddress.ip_network(local_network):
            print(f"Current IP Network: {local_network[:-3]}")
            print(f"Device  IP Address: {ip_address}")
            return
        
        try:
            rm = visa.ResourceManager('@py')
            device: visa.resources.TCPIPSocket = rm.open_resource(f"TCPIP0::{ip_address}::5025::SOCKET")
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

    def _parse(self, reply:str) -> str|float|tuple[str|float]:
        """
        Parse the response from device

        Args:
            reply (str): raw response string from device

        Returns:
            str|float|tuple[str|float]: variable output including floats, strings, and tuples
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
                # self.getErrors()
                ...
        return reply
    
    def _read(self, 
        bulk: bool,
        name: str|None = None, 
        fields: tuple[str] = ('SOURce','READing','SEConds'), 
        average: bool = True,
        quick: bool = False
    ) -> pd.DataFrame:
        """
        Read all data on buffer

        Args:
            bulk (bool): whether to read data after a series of measurements
            name (str|None, optional): buffer name. Defaults to None.
            fields (tuple[str], optional): fields of interest. Defaults to ('SOURce','READing', 'SEConds').
            average (bool, optional): whether to average the data of multiple readings. Defaults to True.
            quick (bool, optional): whether to take a quick reading using existing Sense function and settings. Defaults to False.

        Returns:
            pd.DataFrame: dataframe of measurements
        """
        name = self.active_buffer if name is None else name
        self.fields = fields
        # self.fields = ('CHANnel', *fields)
        if quick:
            reply = self._query(f'READ? "{name}",{",".join(self.fields)}')
            data = self._parse(reply=reply)
            data = np.reshape(np.array(data), (-1,len(self.fields)))
            return pd.DataFrame(data, columns=self.fields)
        
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
        except AttributeError:
            print(f'Not connected to Keithley ({self.ip_address})')
        if self.verbose and "*WAI" not in command:
            # self.getErrors()
            ...
        return True


class DAQ6510(KeithleyDevice):
    def __init__(self, ip_address: str, name: str = 'def', **kwargs):
        super().__init__(ip_address, name, **kwargs)
    
    def createScanList(self, channel_count:int|None = None, channels:Iterable|None = None):
        """
        Deletes existing scan list and creates a new list of channles to scan

        Args:
            channel_count (int|None, optional): number of channels. Defaults to None.
            channels (Iterable|None, optional): array of channel ids. Defaults to None.
        """
        channel_text = f'(@101:{100+channel_count})' if channel_count else ''
        channel_text = f'(@{",".join(channels)})' if channels and not channel_text else channel_text
        return self._query(f'ROUTe:SCAN:CREate {channel_text}')
    
    def setScanCount(self, scan_count:int = 1):
        """
        Set the number of times the scan is repeated

        Args:
            scan_count (int, optional): number of times the scan is repeated. Defaults to 1.
        """
        return self._query(f'ROUTe:SCAN:COUNt:SCAN {scan_count}')
    
    def setScanInterval(self, interval_time_s:float):
        """
        Set the interval time between scan starts when the scan count if greater than one

        Args:
            interval_time_s (float): scan interval in seconds between 0 and 1E5
        """
        return self._query(f'ROUTe:SCAN:INTerval {interval_time_s}')
    
    
class SMU2450(KeithleyDevice):
    def __init__(self, ip_address: str, name: str = 'def', **kwargs):
        super().__init__(ip_address, name, **kwargs)
