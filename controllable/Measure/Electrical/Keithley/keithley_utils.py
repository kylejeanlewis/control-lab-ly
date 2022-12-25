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

# Local application imports
from .. import ElectricalMeasurer
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
        self.ip_address = ip_address
        self.inst = None
        self.name = name
        self._connect(ip_address)
        
        self._attr = dict(
            buff_name=f'{name}data',
            buff_size=BUFFER_SIZE,
            count=NUM_READINGS
        )
        return
        
    def _connect(self, ip_address:str):
        """
        Establish connection with Keithley.
        
        Args:
            ip_address (str): IP address of Keithley
        """
        print("Setting up Keithley comms...")
        if ip_address == None:
            ip_address = self.ip_address
        inst = None
        try:
            rm = visa.ResourceManager('@py')
            inst = rm.open_resource(f"TCPIP0::{ip_address}::5025::SOCKET")
            self.inst = inst

            inst.write_termination = '\n'
            inst.read_termination = '\n'
            inst.write('SYST:BEEP 500, 1')
            inst.query('*IDN?')
            print(f"{self.name.title()} Keithley ready")
        except Exception as e:
            print("Unable to connect to Keithley!")
            print(e) 
        return
    
    def _read(self, prompt:str, field_titles:list, average=False, fill_attributes=False):
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
                output = self.inst.read()
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
                self.inst.write(line)
                # print(line)
        except AttributeError as e:
            print(e)
        return


class Keithley(ElectricalMeasurer):
    """
    Keithley class.
    
    Args:
        ip_address (str, optional): IP address of Keithley. Defaults to '192.168.1.125'.
        name (str, optional): nickname for Keithley. Defaults to 'def'.
    """
    def __init__(self, ip_address='192.168.1.125', name='def'):
        self.ip_address = ip_address
        self.inst = KeithleyDevice(ip_address, name)
        self.buffer_df = pd.DataFrame()
        self.data = None
        self.program = None
        self._flags = {
            'measured': False,
            'parameters_set': False,
            'read': False,
            'stop_measure': False
        }
        self._parameters = {}
        
        self._attr = dict(
            buff_name=f'{name}data',
            buff_size=BUFFER_SIZE,
            count=NUM_READINGS
        )
        self._program_template = None
        return

    def _read_data(self):
        """
        Read data output from Keithley, through the program object
        """
        try:
            self.buffer_df = self.program.data_df
            if len(self.program.data_df):
                self._flags['read'] = True
            else:
                print("No data found.")
        except AttributeError:
            print("Please load a program first.")
        return
        
    def connect(self, ip_address=None):
        """
        Establish connection to Keithley.

        Args:
            ip_address (str, optional): IP address of Keithley. Defaults to None.
        """
        if ip_address == None:
            ip_address = self.ip_address
        self.ip_address = ip_address
        return self.inst._connect(ip_address)
    
    def getData(self, datatype=None):
        """
        Read data and load custom datatype for data

        Args:
            datatype (any, optional): custom datatype for data. Defaults to None.

        Returns:
            pd.DataFrame: raw dataframe of measurement
        """
        if not self._flags['read']:
            self._read_data()
        if self._flags['read']:
            try:
                self.data = datatype(data=self.buffer_df, instrument='keithley_')
            except Exception as e:
                print(e)
        return self.buffer_df

    def loadProgram(self, program:str, params={}):
        """
        Retrieves the SCPI commands from either a file or text string, and replaces placeholder variables. 
        
        Args:
            program (str): name of program to load
            params (dict, optional): dictionary of (param, value)
        """
        if program in base_programs.PROGRAM_LIST:
            program_class = getattr(base_programs, program)
        else:
            print(f"Select program from list: {', '.join(base_programs.PROGRAM_LIST)}")
            return
        self.program = program_class(self.inst, params)
        return

    def measure(self, datatype=None, **kwargs):
        """
        Perform the desired measurement.
        
        Args:
            datatype (any, optional): custom datatype for data. Defaults to None.
            
        Kwargs:
            field_titles (list): list of parameters to read
            values (list): list of values to iterate through
            average (bool): whether to calculate the average and standard deviation of multiple readings
            wait (int/float): duration to wait before sending output prompt [s]
        """
        self.reset(keep_program=True)
        print("Measuring...")
        self.program.run(**kwargs)
        self.getData(datatype)
        if len(self.buffer_df):
            self._flags['measured'] = True
        self.plot()
        return

    def plot(self, plot_type=''):
        """
        Plot the measurement data

        Args:
            plot_type (str, optional): perform the requested plot of the data. Defaults to ''.
        """
        if self._flags['measured'] and self._flags['read']:
            try:
                self.data.plot(plot_type)
            except AttributeError:
                print('\nUnable to plot...')
                self.program.plot()
        return

    def recallParameters(self):
        """
        Recall the last used parameters.

        Raises:
            Exception: Program not loaded

        Returns:
            dict: dictionary of parameters used
        """
        if not self._flags['parameters_set']:
            raise Exception("Please load a program first.")
        return self.program.parameters

    def reset(self, keep_program=False):
        """
        Reset the Keithley

        Args:
            keep_program (bool, optional): whether to keep the loaded program. Defaults to False.
        """
        self.sendMessage(['*RST'])
        self.buffer_df = pd.DataFrame()
        self.data = None
        if not keep_program:
            self.program = None
        for key in self._flags.keys():
            self._flags[key] = False
        return

    def saveData(self, filename:str):
        """
        Save dataframe to csv file.

        Args:
            filename (str): filename to which data will be saved
        """
        if not self._flags['read']:
            self._read_data()
        if self._flags['read']:
            self.buffer_df.to_csv(filename)
        return

    def sendMessage(self, lines:list):
        """
        Relay parameters to Keithley.
        
        Args:
            lines (list): list of parameters to write to Keithley
        """
        return self.inst._write(lines)
    
    def setAddress(self, ip_address:str):
        """
        Set IP address of Keithley

        Args:
            ip_address (str): IP address of Keithley
        """
        self.ip_address = ip_address
        return
    
    def setParameters(self, params:dict):
        """
        Set program parameters

        Args:
            params (dict, optional): dictionary of (param, value)
        """
        for k,v in self._attr.items():
            if k in self.program.scpi.string and k not in params.keys():
                params[k] = v
        return self.program.setParameters(params)


class KeithleyTwo(object):
    def __init__(self, ip_addresses=[], names=[]):
        self._args = list(zip(ip_addresses, names))
        self.ip_addresses = ip_addresses
        self.names = names
        self.keithleys = {name: Keithley(ip_address,name) for ip_address,name in self._args}
        self.buffer_df = pd.DataFrame()
        self.data = None
        self.program = None
        self._flags = {
            'measured': False,
            'parameters_set': False,
            'read': False,
            'stop_measure': False
        }

        self._program_templates = []
        pass
    
    def _read_data(self):
        return
    
    def connect(self, name, ip_address=None):
        if ip_address == None:
            index = self.names.index(name)
            ip_address = self.ip_addresses[index]
        self.ip_addresses[index] = ip_address
        return self.keithleys[name].connect(ip_address)
    
    def getData(self):
        return
    
    def loadProgram(self):
        return
    
    def measure(self):
        self._flags['stop_measure'] = False
        self.program.run()
        self._read_data()
        if len(self.buffer_df):
            self._flags['measured'] = True
        self.plot()
        return
    
    def plot(self):
        return
    
    def recallParameters(self, names=[]):
        if len(names) == 0:
            names = self.names
        params = {}
        for name in self.names:
            params[name] = self.keithleys[name].recallParameters()
        return params
    
    def reset(self, names=[], full=False):
        if len(names) == 0:
            names = self.names
        for name in self.names:
            self.keithleys[name].reset(full)
        return
    
    def saveData(self, names=[], filenames=[]):
        if len(names) == 0:
            names = self.names
        if len(names) != len(filenames):
            raise Exception('Ensure input lists are the same lengths.')
        for i,name in enumerate(self.names):
            self.keithleys[name].saveData(filenames[i])
        return
    
    def sendMessage(self, name, lines=[]):
        """
        Relay parameters to Keithley.
        
        Args:
            params (list): list of parameters to write to Keithley
        """
        return self.keithleys[name].sendMessage(lines)
    
    def setAddress(self, name, ip_address):
        return self.keithleys[name].setAddress(ip_address)
    
    def setParameters(self, name, params={}):
        return self.keithleys[name].setParameters(params)
