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
import pkgutil
import time

# Third party imports
import pyvisa as visa # pip install -U pyvisa

# Local application imports
from ....Analyse.Data.Types.scpi_datatype import SCPI
from .. import Measurer
print(f"Import: OK <{__name__}>")

NUM_READINGS = 3
BUFFER_SIZE = 100
MAX_BUFFER_SIZE = 10000

class Keithley(Measurer):
    """
    Keithley class.
    
    Args:
        ip_address (str/int): IP address of Keithley
        name (str): nickname for Keithley
    """
    def __init__(self, ip_address='192.168.1.125', name=''):
        self.ip_address = ip_address
        self.inst = self.connect(ip_address)
        self.buffer_df = pd.DataFrame()
        self.data = None
        self.program = None # scpi
        self.flags = {
            'parameters_set': False,
            'stop_measure': False
        }
        
        self._buffer = f'{name}data'
        self._buffer_size = BUFFER_SIZE
        self._num_readings = NUM_READINGS
        self._parameters = {}
        self._program_template = None
        return

    def connect(self, ip_address):
        """
        Establish connection with Keithley.
        
        Args:
            ip_address (str/int): IP address of Keithley

        Returns: 
            pyvisa.Resource: Keithley instance
        """
        print("Setting up Keithley comms...")
        inst = None
        try:
            rm = visa.ResourceManager('@py')
            inst = rm.open_resource(f"TCPIP0::{ip_address}::5025::SOCKET")

            inst.write_termination = '\n'
            inst.read_termination = '\n'
            inst.write('SYST:BEEP 500, 1')
            inst.query('*IDN?')
            print(f"{self.name.title()} Keithley ready")
        except Exception as e:
            print("Unable to connect to Keithley!")
            print(e)
        return inst

    def loadProgram(self, program, params={}):
        """
        Retrieves the SCPI commands from either a file or text string, and replaces placeholder variables. 
        
        Args:
            filename (str): filename of txt file where SCPI commands are saved
            string (str): text string of SCPI commands
            
        Returns:
            list: SCPI prompts for settings, inputs, and outputs
        """
        if type(program) == str:
            if program.endswith('.txt'):
                program = pkgutil.get_data(__name__, program).decode('utf-8')
            program = SCPI(program)
        elif 'SCPI' in str(type(program)):
            pass
        else:
            print('Please input either filename or SCPI instruction string!')
            return
        
        if program.string.count('###') != 2:
            raise Exception('Check SCPI input! Please use exact 2 "###" dividers to separate settings, inputs, and outputs.')
        self._program_template = program
        if len(params):
            self.setParameters(params)
        return
    
    def logData(self, columns, average=False):
        """
        Logs data output as well as timestamp.
        
        Args:
            columns (list): list of parameters to read and log
            average  (bool): whether to calculate the average and standard deviation of multiple readings
        """
        start_time = time.time()
        while not self.flags['stop_measure'] and len(self.buffer_df) < MAX_BUFFER_SIZE:
            recv_msg = ['TRAC:TRIG "defbuffer1"', 'FETCH? "defbuffer1", READ, REL']
            self.readData(recv_msg, columns, average=average, cache=True)
            time.sleep(1)
        return

    def measure(self, columns=[], values=[], iterate=False, average=False, cache=False, pause=0, reset=False):
        """
        Perform the desired measurement.
        
        Args:
            columns (list): list of parameters to read
            values (list): list of values to iterate through
            iterate (bool): whether an iterative reading process is required
            average (bool): whether to calculate the average and standard deviation of multiple readings
            cache (bool): whetehr to save the measurements in a buffer dataframe
            pause (int/float): duration in seconds to wait before sending output prompt
            reset (bool): whether to reset Keithley before performing measurement
            
        Returns:
            pandas.DataFrame: dataframe of measurements
        """
        if reset:
            self.reset()
        settings, send_msg, recv_msg = self.program.parse()
        send_scpi = SCPI(scpi_list=[send_msg])

        df = pd.DataFrame()
        self.sendMessage(settings)
        if iterate:
            for value in values:
                if self.flags['stop_measure']:
                    break
                send_value_scpi = SCPI(send_scpi.replace(value=value))
                self.sendMessage(send_value_scpi.parse())
                time.sleep(pause)
                self.readData(recv_msg, columns=columns, average=average, cache=True)
            df = self.buffer_df
        else:
            self.sendMessage(send_msg)
            time.sleep(pause)
            df = self.readData(recv_msg, columns=columns, average=average, cache=cache)

        self.sendMessage(['OUTP OFF'])
        return df

    def readData(self, recv_msg, columns, average=False, cache=False):
        """
        Read data output from Keithley.
        
        Args:
            recv_msg (str): SCPI prompt for retrieving output
            columns (list): list of parameters to read
            average (bool): whether to calculate the average and standard deviation of multiple readings
            cache (bool): whetehr to save the measurements in a buffer dataframe
            
        Returns:
            pandas.DataFrame: dataframe of readings
        """
        outp = ''
        try:
            self.inst.write(recv_msg[0])
            outp = None
            while outp is None:
                outp = self.inst.read()
        except AttributeError as e:
            print(e)
        data = np.reshape(np.array(outp.split(','), dtype=np.float64), (-1,len(columns)))
        if average:
            avg = np.mean(data, axis=0)
            std = np.std(data, axis=0)
            data = np.concatenate([avg, std])
            columns = columns + [c+'_std' for c in columns]
            data = np.reshape(data, (-1,len(columns)))
        df = pd.DataFrame(data, columns=columns, dtype=np.float64)
        if cache:
            self.buffer_df = pd.concat([self.buffer_df, df], ignore_index=True)
        return df

    def recallParameters(self):
        return self._parameters

    def reset(self):
        """Reset the Keithley."""
        self.sendMessage(['*RST'])
        self.buffer_df = pd.DataFrame()
        self.data = None
        self.program = None
        self.flags['stop_measure'] = False
        return

    def sendMessage(self, lines=[]):
        """
        Relay parameters to Keithley.
        
        Args:
            params (list): list of parameters to write to Keithley
        """
        try:
            for line in lines:
                if '<' in line or '>' in line:
                    continue
                self.inst.write(line)
        except AttributeError as e:
            print(e)
            pass
        return
    
    def setParameters(self, params={}):
        this_program = None
        this_program = SCPI(self._program_template.replace(**params))
        self.flags['parameters_set'] = True
        self.program = this_program
        self._parameters = params
        return

