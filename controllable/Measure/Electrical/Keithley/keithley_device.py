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

# Local application imports
print(f"Import: OK <{__name__}>")

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
        
        self.verbose = True
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
    def _get_fields(fields:list):
        """
        Check list of fields

        Args:
            fields (list): list of fields to retrieve from the buffer

        Raises:
            Exception: List should have 14 or fewer items

        Returns:
            list: list of fields
        """
        if len(fields) > 14:
            raise Exception("Please input 14 or fewer buffer elements to read out")
        return fields
    
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
    
    @staticmethod
    def _get_limit(limit, current=True):
        """
        Get the limits for input

        Args:
            limit (str, or float): limit of source or reading
            current (bool, optional): whether limit is for current. Defaults to True.

        Raises:
            Exception: Select a valid string from default, maximum, minimum
            Exception: Select a valid current limit

        Returns:
            str: limit
        """
        if limit is None:
            return 'AUTO ON'
        if type(limit) == str:
            if limit.upper() in ['DEF','DEFAULT','MAX','MAXIMUM','MIN','MINIMUM']:
                return limit
            raise Exception(f"Select a valid function from: default, maximum, minimum")
        lim = 0
        unit = ''
        if current:
            unit = 'A'
            for lim in [10e-9, 100e-9, 1e-6, 10e-6, 100e-6, 1e-3, 10e-3, 100e-3, 1]:
                if lim >= abs(limit):
                    return lim
        else:
            unit = 'V'
            for lim in [20e-3, 200e-3, 2, 20, 200]:
                if lim >= abs(limit):
                    return lim
        raise Exception(f'Please set a current limit that is between -{lim} and {lim} {unit}')
    
    @staticmethod
    def _get_limit_type(source):
        """
        Get the limit type for the source

        Args:
            source (str): function type of source

        Returns:
            str: 'ILIMit' or 'VLIMit'
        """
        if source == 'CURRent':
            return 'VLIMit'
        return 'ILIMit'
    
    def __info__(self):
        """
        Get device system info

        Returns:
            str: system info
        """
        return self._send('*IDN?')
    
    def _generate_commands(self, sense=True):
        func_details = self._sense_details if sense else self._source_details
        header = 'SENSe' if sense else 'SOURce'
        excluded_keys = ['COUNt', 'function', 'invoked']
        commands = [f'{header}:{func_details["function"]}:{key} {value}' for key,value in func_details.items() if key not in excluded_keys]
        
        for i,command in enumerate(commands):
            if 'AUTO' in command:
                new_command = ':AUTO'.join((command.split(' AUTO')))
                commands[i] = new_command
        if sense:
            commands = commands + [f'SENSe:COUNt {func_details.get("COUNt",1)}']
        return commands
    
    def _parse_reply(self, raw_reply:str):
        """
        Parse the response from instrument

        Args:
            raw_reply (str): raw response string from instrument

        Returns:
            float, str, or list: float for numeric values, str for strings, list for multiple replies
        """
        if ',' in raw_reply:
            replies = raw_reply.split(',')
        elif ';' in raw_reply:
            replies = raw_reply.split(';')
        else:
            try:
                raw_reply = float(raw_reply)
            finally:
                return raw_reply
        output = []
        for reply in replies:
            try:
                output.append(float(reply))
            except ValueError:
                output.append(reply)
        if self.verbose:
            print(output)
            self.getErrors()
        return output
    
    def _send(self, command:str):
        """
        Write command to instrument, using query if expecting reply

        Args:
            command (str): command string to write

        Returns:
            any: response from query, or None
        """
        reply = None 
        if self.instrument is None:
            print(command)
            if self.verbose:
                print("")
            _dummy_return = [0 for _ in range(command.count(';')+1)] if "?" in command else None
            return _dummy_return
        if self.verbose:
            print(command)
        try:
            if "?" not in command:
                self.instrument.write(command)
            else:
                raw_reply = self._query(command)
                reply = self._parse_reply(raw_reply=raw_reply)
            if self.verbose:
                self.getErrors()
        except visa.VisaIOError:
            self.getErrors()
        return reply
    
    def _query(self, command:str):
        """
        Perform a query on instrument

        Args:
            command (str): command string to query

        Returns:
            str: response from query, or None
        """
        reply = self.instrument.query(command)
        # reply = None
        # self.instrument.write(command)
        # while reply is None:
        #     reply = self.instrument.read()
        return reply
    
    def beep(self, frequency=440, duration=1):
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
            raise Exception('Please enter a frequency between 20 and 8000')
        if not 0.001<=duration<=100:
            raise Exception('Please enter a duration between 0.001 and 100')
        return self._send(f'SYSTem:BEEPer {frequency},{duration}')
    
    def clearBuffer(self, name=None):
        """
        Clear buffer

        Args:
            name (str, optional): name of buffer to clear. Defaults to None.
        """
        if name is None:
            name = self._active_buffer
        return self._send(f'TRACe:CLEar "{name}"')
    
    def configure(self, commands:list):
        """
        Write multiple commands to instrument

        Args:
            commands (list): list of commands to write
        """
        for command in commands:
            self._send(command)
        return

    def configureSense(self, func, limit='DEFault', probe_4_point=True, unit=None, count=1):
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
        self.sense = func
        self._send(f'SENSe:FUNCtion "{self.sense}"')
        
        is_current = (self.sense=='CURRent')
        if unit is None:
            if self.sense == 'CURRent':
                unit = 'AMP'
            elif self.sense == 'VOLTage':
                unit = 'VOLT'
        count_upper_limit = min(300000, 300000)
        count = max(1,count)
        if count>count_upper_limit:
            raise Exception(f"Please select a count from 1 to {count_upper_limit}")
        kwargs = {
            'RANGe': self._get_limit(limit=limit, current=is_current),
            'RSENse': 'ON' if probe_4_point else 'OFF',
            'UNIT': unit,
            'COUNt': int(count)
        }
        self._sense_details.update(kwargs)
        commands = self._generate_commands(sense=True)
        return self.configure(commands=commands)
    
    def configureSource(self, func, limit=None, measure_limit='DEFault'):
        """
        Configure the source function

        Args:
            func (str): function to be sourced, from current, and voltage
            limit (str or float, optional): sourcing range. Defaults to None.
            measure_limit (str or float, optional): limit imposed on the measurement range. Defaults to 'DEFault'.
        """
        self.source = func
        self._send(f'SOURce:FUNCtion {self.source}')
        
        is_current = (self.source=='CURRent')
        kwargs = {
            'RANGe': self._get_limit(limit=limit, current=is_current),
            self._get_limit_type(self.source): self._get_limit(limit=measure_limit, current=not(is_current))
        }
        self._source_details.update(kwargs)
        self._source_details.update({'invoked': 0})
        commands = self._generate_commands(sense=False)
        return self.configure(commands=commands)
    
    def connect(self, ip_address=None):
        """
        Establish connection with Keithley
        
        Args:
            ip_address (str, optional): IP address of Keithley. Defaults to None
            
        Returns:
            Instrument: Keithley object
        """
        print("Setting up Keithley communications...")
        if ip_address is None:
            ip_address = self.ip_address
        self._ip_address = ip_address
        instrument = None
        try:
            rm = visa.ResourceManager('@py')
            instrument = rm.open_resource(f"TCPIP0::{ip_address}::5025::SOCKET")
            self.instrument = instrument
            instrument.write_termination = '\n'
            instrument.read_termination = '\n'
            
            self.beep(500)
            print(f"{self.__info__()}")
            print(f"{self.name.title()} Keithley ready")
        except Exception as e:
            print("Unable to connect to Keithley!")
            if self.verbose:
                print(e) 
        return instrument
    
    def getBufferIndices(self, name=None):
        """
        Get the start and end buffer indices

        Args:
            name (str, optional): name of buffer. Defaults to None.

        Returns:
            list: start and end buffer indices
        """
        if name is None:
            name = self.buffer_name
        return self._send(f'TRACe:ACTual:STARt? "{name}" ; END? "{name}"')
    
    def getErrors(self):
        """
        Get Errors from Keithley
        """
        errors = []
        reply = self._query('SYSTem:ERRor:COUNt?')
        while not reply.isnumeric():
            print(reply)
            reply = self._query('SYSTem:ERRor:COUNt?')
        num_errors = int(reply)
        for i in range(num_errors):
            error = self._query('SYSTem:ERRor?')
            errors.append((error))
            print(f'>>> Error {i+1}: {error}')
        return errors
    
    def getStatus(self):
        """
        Get status of instrument

        Returns:
            str: instrument state
        """
        return self._send('TRIGger:STATe?')
    
    def isBusy(self):
        """
        Checks whether the instrument is busy
        
        Returns:
            bool: whether the instrument is busy
        """
        return self._flags['busy']
    
    def isConnected(self):
        """
        Check whether instrument is connected

        Returns:
            bool: whether instrument is connected
        """
        if self.instrument is None:
            return False
        return True
    
    def makeBuffer(self, name=None, buffer_size=100000):
        """
        Make a buffer on the instrument

        Args:
            name (str, optional): buffer name. Defaults to None.
            buffer_size (int, optional): buffer size. Defaults to 100000.
        """
        if name is None:
            name = self.buffer_name
            self._active_buffer = name
        if buffer_size < 10 and buffer_size != 0:
            buffer_size = 10
        return self._send(f'TRACe:MAKE "{name}",{buffer_size}')
    
    def readAll(self, name=None, fields=['SOURce','READing', 'SEConds'], average=True):
        """
        Read all data on buffer

        Args:
            name (str, optional): buffer name. Defaults to None.
            fields (list, optional): fields of interest. Defaults to ['SOURce','READing', 'SEConds'].
            average (bool, optional): whether to average the data of multiple readings. Defaults to True.

        Returns:
            pd.DataFrame: dataframe of measurements
        """
        if name is None:
            name = self._active_buffer
        fields = self._get_fields(fields=fields)
        start,end = self.getBufferIndices(name=name)
        count = self._sense_details.get('COUNt', 1)
        
        data = self._send(f'TRACe:DATA? {int(start)},{int(end)},"{name}",{",".join(fields)}')
        if not all([start,end]): # dummy data
            num_rows = count * max(1, self._source_details.get('invoked', 1))
            data = [0] * int(num_rows * len(fields))
        data = np.reshape(np.array(data), (-1,len(fields)))
        df = pd.DataFrame(data, columns=fields)
        if average and count > 1:
            avg = df.groupby(np.arange(len(df))//count).mean()
            std = df.groupby(np.arange(len(df))//count).std()
            df = avg.join(std, rsuffix='_std')
        return df
    
    def readPacket(self, name=None, fields=['SOURce','READing', 'SEConds'], average=True):
        """
        Read data on buffer as measurements take place

        Args:
            name (str, optional): buffer name. Defaults to None.
            fields (list, optional): fields of interest. Defaults to ['SOURce','READing', 'SEConds'].
            average (bool, optional): whether ot average the data of multiple readings. Defaults to True.

        Returns:
            pd.DataFrame: dataframe of measurements
        """
        if name is None:
            name = self._active_buffer
        fields = self._get_fields(fields=fields)
        _,end = self.getBufferIndices(name=name)
        count = self._sense_details.get('COUNt', 1)
        start = end - count + 1
        
        data = self._send(f'TRACe:DATA? {int(start)},{int(end)},"{name}",{",".join(fields)}')
        if not all([start,end]): # dummy data
            data = [0] * int(count * len(fields))
        data = np.reshape(np.array(data), (-1,len(fields)))
        df = pd.DataFrame(data, columns=fields)
        if average and count > 1:
            avg = df.groupby(np.arange(len(df))//count).mean()
            std = df.groupby(np.arange(len(df))//count).std()
            df = avg.join(std, rsuffix='_std')
        return df
    
    def recallState(self, state:int):
        """
        Recall a previously saved settings of instrument

        Args:
            state (int): state index to recall from

        Raises:
            Exception: Select an index from 0 to 4
        """
        if not 0 <= state <= 4:
            raise Exception("Please select a state index from 0 to 4")
        return self._send(f'*RCL {state}')
    
    def reset(self):
        """
        Reset the instrument
        """
        return self._send('*RST')
    
    def saveState(self, state:int):
        """
        Save current settings / state of instrument

        Args:
            state (int): state index to save to

        Raises:
            Exception: Select an index from 0 to 4
        """
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
        """
        Set source to desired value

        Args:
            value (int or float): value to set source to 

        Raises:
            Exception: Set a value within limits
        """
        capacity = 1 if self.source=='CURRent' else 200
        limit = self._source_details.get('RANGe', capacity)
        if type(limit) == str:
            limit = capacity
        unit = 'A' if self.source=='CURRent' else 'V'
        if abs(value) > limit:
            raise Exception(f'Please set a source value between -{limit} and {limit} {unit}')
        self._source_details['invoked'] += 1
        return self._send(f'SOURce:{self.source} {value}')

    def start(self, sequential_commands=True):
        """
        Initialise the measurement

        Args:
            sequential_commands (bool, optional): whether commands whose operations must finish before the next command is executed. Defaults to True.
        """
        if sequential_commands:
            command = f'TRACe:TRIGger "{self._active_buffer}"'
        else:
            command = 'INITiate ; *WAIt'
        return self._send(command=command)

    def stop(self):
        """
        Abort all actions
        """
        return self._send('ABORt')

    def toggleOutput(self, on:bool):
        """
        Toggle turning on output

        Args:
            on (bool): whether to turn on output
        """
        state = 'ON' if on else 'OFF'
        return self._send(f'OUTPut {state}')
    