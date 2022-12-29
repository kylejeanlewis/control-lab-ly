# %% -*- coding: utf-8 -*-
"""
Created: Tue 2022/11/02 17:13:35
@author: Chang Jie

Notes / actionables:
- validation on copper
"""
# Standard library imports
import numpy as np
import pandas as pd

# Third party imports
import pyvisa as visa # pip install -U pyvisa
# pip install pyvisa-py

# Local application imports
from ..electrical_utils import Electrical
from .programs import base_programs
print(f"Import: OK <{__name__}>")

BUFFER_SIZE = 100
NUM_READINGS = 3

class KeithleyDevice(object):
    """
    Keithley device object
    
    Args:
        ip_address (str): IP address of Keithley
        name (str, optional): nickname for Keithley. Defaults to 'def'.
    """
    def __init__(self, ip_address:str, name='def'):
        self._ip_address = ip_address
        self._name = name
        self.instrument = None
        
        self._active_buffer = None
        self._sense_details = {}
        self._source_details = {}
        
        self.verbose = False
        self._flags = {
            'busy': False
        }
        self.connect(ip_address)
        return
    
    @property
    def buffer_name(self):
        return f'{self.name}buffer'
    
    @property
    def ip_address(self):
        return self._ip_address
    
    @property
    def name(self):
        return self._name
    
    @property
    def sense(self):
        return self._sense_details['function']
    @sense.setter
    def sense(self, func:str):
        self._sense_details['function'] = self._get_function(func=func, sense=True)
        return
    
    @property
    def source(self):
        return self._source_details['function']
    @source.setter
    def source(self, func:str):
        self._source_details['function'] = self._get_function(func=func, sense=False)
        return
    
    @staticmethod
    def _get_function(func:str, sense=True):
        """
        Get the function name and check for validity

        Args:
            func (str): function name from current, resistance, and voltage
            sense (bool, optional): whether function is for sensing. Defaults to True.

        Raises:
            Exception: Select a valid function

        Returns:
            str: function name
        """
        func = func.upper()
        valid_functions = ['current', 'resistance', 'voltage'] if sense else ['current', 'voltage']
        if func in ['CURR','CURRENT']:
            return 'CURRent'
        elif func in ['RES','RESISTANCE'] and sense:
            return 'RESistance'
        elif func in ['VOLT','VOLTAGE']:
            return 'VOLTage'
        raise Exception(f"Select a valid function from: {', '.join(valid_functions)}")
    
    def __info__(self):
        return self._send('*IDN?')
    
    def _get_fields(self, fields:list):
        if len(fields) > 14:
            raise Exception("Please input 14 or fewer buffer elements to read out")
        return fields
    
    def _get_limit(self, limit):
        if limit is None:
            return 'AUTO ON'
        if type(limit) == str:
            if limit.upper() in ['DEF','DEFAULT','MAX','MAXIMUM','MIN','MINIMUM']:
                return limit
            raise Exception(f"Select a valid function from: default, maximum, minimum")
        lim = 0
        unit = ''
        if self.source == 'CURRent':
            unit = 'A'
            for lim in [10e-9, 100e-9, 1e-6, 10e-6, 100e-6, 1e-3, 10e-3, 100e-3, 1]:
                if lim > abs(limit):
                    return lim
        else:
            unit = 'V'
            for lim in [20e-3, 200e-3, 2, 20, 200]:
                if lim > abs(limit):
                    return lim
        raise Exception(f'Please set a current limit that is between -{lim} and {lim} {unit}')
    
    def _get_limit_type(self):
        source = self.source
        if source == 'CURRent':
            return 'VLIMit'
        return 'ILIMit'
    
    def _send(self, command:str):
        if self.instrument is None:
            print(command)
            if self.verbose:
                print("")
            return
        if "?" in command:
            reply = self.instrument.query(command)
            if ',' in reply:
                replies = reply.split(',')
            elif ';' in reply:
                replies = reply.split(';')
            else:
                try:
                    reply = float(reply)
                finally:
                    return reply
            
            output = []
            for reply in replies:
                try:
                    output.append(float(reply))
                except ValueError:
                    output.append(reply)
            return output
        self.instrument.write(command)
        return
    
    def beep(self, frequency=440, duration=1):
        if not 20<=frequency<=8000:
            raise Exception('Please enter a frequency between 20 and 8000')
        if not 0.001<=duration<=100:
            raise Exception('Please enter a duration between 0.001 and 100')
        return self._send(f'SYSTem:BEEPer {frequency}, {duration}')
    
    def clearBuffer(self, name=None):
        if name is None:
            name = self._active_buffer
        return self._send(f'TRACe:CLEar "{name}"')
    
    def configure(self, commands:list):
        for command in commands:
            self._send(command)
        return

    def configureSense(self, func, limit='DEFault', probe_4_point=True, unit=None, count=1):
        self.sense = func
        self._send(f'SENSe:FUNCtion "{self.sense}"')
        
        if unit is None:
            if self.sense == 'CURRent':
                unit = 'AMP'
            elif self.sense == 'VOLTage':
                unit = 'VOLT'
        count_upper_limit = min(300000, 300000)
        if not 1<=count<=count_upper_limit:
            raise Exception(f"Please select a count from 1 to {count_upper_limit}")
        kwargs = {
            'RANGe': self._get_limit(limit=limit),
            'RSENse': 'ON' if probe_4_point else 'OFF',
            'COUNt': count
        }
        self._sense_details.update(kwargs)
        commands = [f'SOURce:{self.source}:{key} {value}' for key,value in kwargs.items() if key!='COUNt']
        commands = commands + [f'SENSe:COUNt {count}']
        return self.configure(commands=commands)
    
    def configureSource(self, func, limit=None, measure_limit='DEFault'):
        self.source = func
        self._send(f'SOURce:FUNCtion {self.source}')
        
        kwargs = {
            'RANGe': self._get_limit(limit=limit),
            self._get_limit_type(self.source): self._get_limit(limit=measure_limit)
        }
        self._source_details.update(kwargs)
        commands = [f'SOURce:{self.source}:{key} {value}' for key,value in kwargs.items()]
        return self.configure(commands=commands)
    
    def connect(self, ip_address=None):
        """
        Establish connection with Keithley.
        
        Args:
            ip_address (str, optional): IP address of Keithley. Defaults to None
        """
        print("Setting up Keithley communications...")
        if ip_address is None:
            ip_address = self.ip_address
        instrument = None
        try:
            rm = visa.ResourceManager('@py')
            instrument = rm.open_resource(f"TCPIP0::{ip_address}::5025::SOCKET")
            self.instrument = instrument
            instrument.write_termination = '\n'
            instrument.read_termination = '\n'
            
            self.beep(500)
            print(f"{self.__info__}")
            print(f"{self.name.title()} Keithley ready")
        except Exception as e:
            print("Unable to connect to Keithley!")
            if self.verbose:
                print(e) 
        return instrument
    
    def getBufferIndices(self, name=None):
        if name is None:
            name = self.buffer_name
        return self._send(f'TRACe:ACTual:STARt? "{name}" ; END? "{name}"')
    
    def getStatus(self):
        return self._send('TRIGger:STATe?')
    
    def isBusy(self):
        return self._flags['busy']
    
    def isConnected(self):
        if self.instrument is None:
            return False
        return True
    
    def makeBuffer(self, name=None, buffer_size=100000):
        if name is None:
            name = self.buffer_name
            self._active_buffer = name
        if buffer_size < 10 and buffer_size != 0:
            buffer_size = 10
        return self._send(f'TRACe:MAKE "{name}", {buffer_size}')
    
    def readAll(self, name=None, fields=['SOURce','READing', 'SEConds'], average=True):
        if name is None:
            name = self._active_buffer
        fields = self._get_fields(fields=fields)
        start,end = self.getBufferIndices(name=name)
        
        data = self._send(f'TRACe:DATA? {start}, {end}, "{name}", {", ".join(fields)}')
        data = np.reshape(np.array(data), (-1,len(fields)))
        df = pd.DataFrame(data, columns=fields)
        if average:
            avg = df.groupby(np.arange(len(df))//2).mean()
            std = df.groupby(np.arange(len(df))//2).std()
            df = avg.join(std, rsuffix='_std')
        return df
    
    def readPacket(self, name=None, fields=['SOURce','READing', 'SEConds'], average=True):
        if name is None:
            name = self._active_buffer
        fields = self._get_fields(fields=fields)
        _,end = self.getBufferIndices(name=name)
        num_rows = self._sense_details.get('COUNt', 1)
        start = end - num_rows + 1
        
        data = self._send(f'TRACe:DATA? {start}, {end}, "{name}", {", ".join(fields)}')
        data = np.reshape(np.array(data), (-1,len(fields)))
        df = pd.DataFrame(data, columns=fields)
        if average:
            avg = df.groupby(np.arange(len(df))//2).mean()
            std = df.groupby(np.arange(len(df))//2).std()
            df = avg.join(std, rsuffix='_std')
        return df
    
    def recallState(self, state:int):
        if not 0 <= state <= 4:
            raise Exception("Please select a state index from 0 to 4")
        return self._send(f'*RCL {state}')
    
    def reset(self):
        """
        Reset the instrument
        """
        return self._send("*RST")
    
    def saveState(self, state:int):
        if not 0 <= state <= 4:
            raise Exception("Please select a state index from 0 to 4")
        return self._send(f'*SAV {state}')
    
    def setFlag(self, name:str, value:bool):
        """
        Set a flag truth value

        Args:
            name (str): label
            value (bool): flag value
        """
        self._flags[name] = value
        return

    def setSource(self, value):
        capacity = 1 if self.source=='CURRent' else 200
        limit = self._source_details.get('RANGe', capacity)
        unit = 'A' if self.source=='CURRent' else 'V'
        if abs(value) > limit:
            raise Exception(f'Please set a source value between -{limit} and {limit} {unit}')
        return self._send(f'SOURce:{self.source} {value}')

    def start(self, consecutive_readings=False):
        if consecutive_readings:
            self._send('INITiate; *WAIt')
        else:
            self._send(f'TRACe:TRIGger "{self._active_buffer}"')
        return

    def stop(self):
        return self._send('ABORt')

    def toggleOutput(self, on:bool):
        state = 'ON' if on else 'OFF'
        return self._send(f'OUTPut {state}')
    
    
    """======================================================================================================================"""
    
    def _readd(self, prompt:str, field_titles:list, average=False, fill_attributes=False):
        """
        Alias for _read_data_stream
        
        Args:
            prompt (str): SCPI prompt for retrieving output
            field_titles (list): list of parameters to read
            average (bool, optional): whether to calculate the average and standard deviation of multiple readings. Defaults to False.
            fill_attributes (bool, optional): whether to fill in attribute values (i.e. buffer name, buffer size, count). Defaults to False.
            
        Returns:
            pd.DataFrame: dataframe of output from Keithley 
        """
        return self._read_data_stream(prompt=prompt, field_titles=field_titles, average=average, fill_attributes=fill_attributes)
    
    def _read_data_stream(self, prompt:str, field_titles:list, average=False, fill_attributes=False):
        """
        Read data output from Keithley.
        
        Args:
            prompt (str): SCPI prompt for retrieving output
            field_titles (list): list of parameters to read
            average (bool, optional): whether to calculate the average and standard deviation of multiple readings. Defaults to False.
            fill_attributes (bool, optional): whether to fill in attribute values (i.e. buffer name, buffer size, count). Defaults to False.
            
        Returns:
            pd.DataFrame: dataframe of output from Keithley 
        """
        output = None
        try:
            self._write(prompt, fill_attributes)
            while output is None:
                output = self.instrument.read()
        except AttributeError as e:
            print(e)
        if type(output) == type(None):
            print('No output.')
            return pd.DataFrame()
        data = np.reshape(np.array(output.split(','), dtype=np.float64), (-1,len(field_titles)))
        if average:
            avg = np.mean(data, axis=0)
            std = np.std(data, axis=0)
            data = np.concatenate([avg, std])
            field_titles = field_titles + [c+'_std' for c in field_titles]
            data = np.reshape(data, (-1,len(field_titles)))
        df = pd.DataFrame(data, columns=field_titles, dtype=np.float64)
        return df
    
    def _write(self, lines:list, fill_attributes=False):
        """
        Alias for _write_bulk
        
        Args:
            lines (list): list of parameters to write to Keithley
            fill_attributes (bool, optional): whether to fill in attribute values (i.e. buffer name, buffer size, count). Defaults to False.
        """
        return self._write_bulk(lines=lines, fill_attributes=fill_attributes)
    
    def _write_bulk(self, lines:list, fill_attributes=False):
        """
        Relay parameters to Keithley.
        
        Args:
            lines (list): list of parameters to write to Keithley
            fill_attributes (bool, optional): whether to fill in attribute values (i.e. buffer name, buffer size, count). Defaults to False.
        """
        try:
            for line in lines:
                if fill_attributes:
                    for k,v in self._attr.items():
                            line = line.replace('{'+f'{k}'+'}', str(v)) if k in line else line
                if '{' in line or '}' in line:
                    continue
                self.instrument.write(line)
                # print(line)
        except AttributeError as e:
            print(e)
        return


class Keithley(Electrical):
    """
    Keithley class.
    
    Args:
        ip_address (str, optional): IP address of Keithley. Defaults to '192.168.1.125'.
        name (str, optional): nickname for Keithley. Defaults to 'def'.
    """
    model = 'keithley_'
    def __init__(self, ip_address='192.168.1.125', name='def'):
        self._ip_address = ''
        super().__init__(ip_address=ip_address, name=name)
        return

    @property
    def ip_address(self):
        return self._ip_address

    def _connect(self, ip_address:str, name:str):
        """
        Connect to device

        Args:
            ip_address (str): IP address of the Biologic device
            name (str): nickname for Keithley.
            
        Returns:
            KeithleyDevice: object representation
        """
        self._ip_address = ip_address
        self.device = KeithleyDevice(ip_address=ip_address, name=name)
        return self.device

    def _extract_data(self):
        """
        Extract data output from device, through the program object
        
        Returns:
            bool: whether the data extraction from program is successful
        """
        if self._program is None:
            print("Please load a program first.")
            return False
        self.buffer_df = self._program.data_df
        if len(self.buffer_df) == 0:
            print("No data found.")
            return False
        self.setFlag('read', True)
        return True
    
    def connect(self):
        """
        Establish connection to Keithley.

        Returns:
            KeithleyDevice: object representation
        """
        return self._connect(self.ip_address, self.name)
    
    def loadProgram(self, name=None, program_type=None, program_module=base_programs):
        """
        Load a program for device to run and its parameters

        Args:
            name (str, optional): name of program type in program_module. Defaults to None.
            program_type (any, optional): program to load. Defaults to None.
            program_module (module, optional): module containing relevant programs. Defaults to Keithley.programs.base_programs.

        Raises:
            Exception: Provide a module containing relevant programs
            Exception: Select a valid program name
            Exception: Input only one of 'name' or 'program_type'
        """
        return super().loadProgram(name=name, program_type=program_type, program_module=program_module)

    def reset(self):
        """
        Reset the Keithley and clear the program, data, and flags
        """
        self.device.reset()
        return super().reset()
