# %% -*- coding: utf-8 -*-
"""
Created: Tue 2022/11/02 17:13:35
@author: Chang Jie

Notes / actionables:
- validation on copper 
- rewrite the operation modes as programs, instead of subclasses
"""
# Standard library imports
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
    def __init__(self, ip_address):
        self.ip_address = ip_address
        self.inst = None
        self._connect(ip_address)
        return
        
    def _connect(self, ip_address=''):
        """
        Establish connection with Keithley.
        
        Args:
            ip_address (str/int): IP address of Keithley
        """
        print("Setting up Keithley comms...")
        if len(ip_address) == 0:
            ip_address = self.ip_address
        inst = None
        try:
            rm = visa.ResourceManager('@py')
            inst = rm.open_resource(f"TCPIP0::{ip_address}::5025::SOCKET")

            inst.write_termination = '\n'
            inst.read_termination = '\n'
            inst.write('SYST:BEEP 500, 1')
            inst.query('*IDN?')
            self.inst = inst
            print(f"{self.name.title()} Keithley ready")
        except Exception as e:
            print("Unable to connect to Keithley!")
            print(e) 
        return
    
    def _read(self, prompt, field_titles, average=False):
        """
        Read data output from Keithley.
        
        Args:
            prompt (str): SCPI prompt for retrieving output
            field_titles (list): list of parameters to read
            average (bool): whether to calculate the average and standard deviation of multiple readings
        """
        outp = ''
        try:
            self.inst.write(prompt[0])
            outp = None
            while outp is None:
                outp = self.inst.read()
        except AttributeError as e:
            print(e)
        data = np.reshape(np.array(outp.split(','), dtype=np.float64), (-1,len(field_titles)))
        if average:
            avg = np.mean(data, axis=0)
            std = np.std(data, axis=0)
            data = np.concatenate([avg, std])
            field_titles = field_titles + [c+'_std' for c in field_titles]
            data = np.reshape(data, (-1,len(field_titles)))
        df = pd.DataFrame(data, columns=field_titles, dtype=np.float64)
        return df
    
    def _write(self, lines=[]):
        """
        Relay parameters to Keithley.
        
        Args:
            params (list): list of parameters to write to Keithley
        """
        try:
            for line in lines:
                if '{' in line or '}' in line:
                    continue
                self.inst.write(line)
        except AttributeError as e:
            print(e)
        return


class Keithley(ElectricalMeasurer):
    """
    Keithley class.
    
    Args:
        ip_address (str/int): IP address of Keithley
        name (str): nickname for Keithley
    """
    def __init__(self, ip_address='192.168.1.125', name='def'):
        self.ip_address = ip_address
        self.inst = KeithleyDevice(ip_address)
        self.buffer_df = pd.DataFrame()
        self.data = None
        self.program = None
        self.flags = {
            'measured': False,
            'parameters_set': False,
            'read': False,
            'stop_measure': False
        }
        
        self._buffer = f'{name}data'
        self._buffer_size = BUFFER_SIZE
        self._num_readings = NUM_READINGS
        self._parameters = {}
        self._program_template = None
        return

    def _readData(self):
        """
        Read data output from Keithley.
        
        Args:
            prompt (str): SCPI prompt for retrieving output
            field_titles (list): list of parameters to read
            average (bool): whether to calculate the average and standard deviation of multiple readings
        """
        try:
            self.buffer_df = self.program.data_df
            if len(self.program.data_df):
                self.flags['read'] = True
            else:
                print("No data found.")
        except AttributeError:
            print("Please load a program first.")
        return
        
    def connect(self):
        return self.inst._connect()
    
    def getData(self, datatype=None):
        if not self.flags['read']:
            self._readData()
        if self.flags['read']:
            try:
                self.data = datatype(data=self.buffer_df, instrument='keithley_')
            except Exception as e:
                print(e)
        return self.buffer_df

    def loadProgram(self, program, params={}):
        """
        Retrieves the SCPI commands from either a file or text string, and replaces placeholder variables. 
        
        Args:
            filename (str): filename of txt file where SCPI commands are saved
            string (str): text string of SCPI commands
            
        Returns:
            list: SCPI prompts for settings, inputs, and outputs
        """
        if program in base_programs.PROGRAM_LIST:
            program_class = getattr(base_programs, program)
        else:
            print(f"Select program from list: {', '.join(base_programs.PROGRAM_LIST)}")
            return
        self.program = program_class(self.inst, params)
        return

    def measure(self):
        """
        Perform the desired measurement.
        
        Args:
            field_titles (list): list of parameters to read
            values (list): list of values to iterate through
            average (bool): whether to calculate the average and standard deviation of multiple readings
            wait (int/float): duration to wait before sending output prompt [s]
            
        Returns:
            pandas.DataFrame: dataframe of measurements
        """
        self.flags['stop_measure'] = False
        self.program.run()
        self._readData()
        if len(self.buffer_df):
            self.flags['measured'] = True
        self.plot()
        return

    def plot(self, plot_type=''):
        if self.flags['measured'] and self.flags['read']:
            self.data.plot(plot_type)
        return

    def recallParameters(self):
        if not self.flags['parameters_set']:
            raise Exception("Please load a program first.")
        return self.program.parameters

    def reset(self, full=False):
        """Reset the Keithley."""
        self.sendMessage(['*RST'])
        if full:
            self.buffer_df = pd.DataFrame()
            self.data = None
            self.program = None
            for key in self.flags.keys():
                self.flags[key] = False
        return

    def saveData(self, filename):
        if not self.flags['read']:
            self._readData()
        if self.flags['read']:
            self.buffer_df.to_csv(filename)
        return

    def sendMessage(self, lines=[]):
        """
        Relay parameters to Keithley.
        
        Args:
            params (list): list of parameters to write to Keithley
        """
        return self.inst._write(lines)
    
    def setParameters(self, params={}):
        attr = dict(
            buff_name=self._buffer,
            buff_size=self._buffer_size,
            count=self._num_readings
        )
        for k,v in attr.items():
            if f'{k}' in self.program.scpi.string and k not in params.keys():
                params[k] = v
        return self.program.setParameters(params)


class KeithleyTwo(object):
    def __init__(self) -> None:
        pass