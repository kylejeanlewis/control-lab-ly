# %% -*- coding: utf-8 -*-
"""
Created: Tue 2022/11/02 17:13:35
@author: Chang Jie

Notes / actionables:
- validation on copper
"""
# Standard library imports
import asyncio
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
        
        self.verbose = False
        # self._attr = dict(
        #     buff_name=f'{name}data',
        #     buff_size=BUFFER_SIZE,
        #     count=NUM_READINGS
        # )
        self.connect(ip_address)
        return
    
    @property
    def ip_address(self):
        return self._ip_address
    
    @property
    def name(self):
        return self._name
    
    def configure(self, name:str, value):
        return
    
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
            instrument.write('SYST:BEEP 500, 1')
            instrument.query('*IDN?')
            print(f"{self.name.title()} Keithley ready")
        except Exception as e:
            print("Unable to connect to Keithley!")
            if self.verbose:
                print(e) 
        return instrument
    
    def _query(self, line:str):
        return
    
    def _read(self, prompt:str, field_titles:list, average=False, fill_attributes=False):
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

    def reset(self):
        return self._write(['*RST'])


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
