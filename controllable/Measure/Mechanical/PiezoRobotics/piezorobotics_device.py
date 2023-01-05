# %% -*- coding: utf-8 -*-
"""
Created: Tue 2023/01/03 17:13:35
@author: Chang Jie

Notes / actionables:
-
"""
# Standard library imports
import numpy as np
import pandas as pd
import time

# Third party imports
import serial # pip install pyserial

# Local application imports
from .piezorobotics_lib import ErrorCode, FrequencyCode
from .piezorobotics_lib import COMMANDS, ERRORS, FREQUENCIES
print(f"Import: OK <{__name__}>")

READ_TIMEOUT_S = 1

class PiezoRoboticsDevice(object):
    """
    PiezoRoboticsDevice object

    Args:
        port (str): com port address
        channel (int, optional): assigned device channel. Defaults to 1.
    """
    def __init__(self, port:str, channel=1, **kwargs):
        self.channel = channel
        self.instrument = None
        
        self._frequency_range_codes = ('','')
        
        self.verbose = True
        self._flags = {
            'busy': False,
            'connected': False,
            'initialised': False,
            'measured': False,
            'read': False
        }
        self.port = ''
        self._baudrate = None
        self._timeout = None
        self._connect(port)
        pass
    
    @property
    def frequency_codes(self):
        lo_code, hi_code = self._frequency_range_codes
        return int(lo_code[-2:]), int(hi_code[-2:])
    
    @property
    def frequency_range(self):
        lo_code, hi_code = self._frequency_range_codes
        return FrequencyCode[lo_code].value, FrequencyCode[hi_code].value
    @frequency_range.setter
    def frequency_range(self, frequencies):
        """
        Set the operating frequency range

        Args:
            frequencies (iterable): frequency lower and upper limits
                low_frequency (float): lower frequency limit
                high_frequency (float): upper frequency limit
        """
        low_frequency, high_frequency = list(frequencies).sorted()
        all_freq = np.array(FREQUENCIES)
        freq_in_range_indices = np.where((all_freq>=low_frequency) & (all_freq<=high_frequency))
        lo_code_number = max( (freq_in_range_indices[0]+1) - 1, 1)
        hi_code_number = min( (freq_in_range_indices[-1]+1) + 1, len(all_freq))
        self._frequency_range_codes = (f'FREQ_{lo_code_number:02}', f'FREQ_{hi_code_number:02}')
        return
    
    def __delete__(self):
        self._shutdown()
        return
    
    def _connect(self, port:str, baudrate=115200, timeout=1):
        """
        Connect to machine control unit

        Args:
            port (str): com port address
            baudrate (int): baudrate. Defaults to 115200.
            timeout (int, optional): timeout in seconds. Defaults to None.
            
        Returns:
            serial.Serial: serial connection to machine control unit if connection is successful, else None
        """
        self.port = port
        self._baudrate = baudrate
        self._timeout = timeout
        instrument = None
        try:
            instrument = serial.Serial(port, self._baudrate, timeout=self._timeout)
            self.instrument = instrument
            print(f"Connection opened to {port}")
            self.setFlag('connected', True)
            
        except Exception as e:
            if self.verbose:
                print(f"Could not connect to {port}")
                print(e)
        return self.instrument
    
    def _is_expected_reply(self, message_code:str, response:str):
        """
        Check whether the response is an expected reply

        Args:
            message_code (str): command code
            response (str): response string from instrument

        Returns:
            bool: whether the response is an expected reply
        """
        if response in ERRORS:
            return True
        if response in ['OKR', 'OKC']:
            return True
        if message_code == 'GET':
            if self.verbose:
                print(f'[{message_code}] {response}')
            return True
        return False
    
    def _read(self):
        """
        Read response from instrument

        Returns:
            str: response string
        """
        response = ''
        try:
            response = self.instrument.readline()
            if len(response) == 0:
                response = self.instrument.readline()
            if response in ERRORS:
                print(ErrorCode[response].value)
                return response
            elif response in ['OKR', 'OKC']:
                return response
        except Exception as e:
            if self.verbose:
                print(e)
        return response
    
    def _shutdown(self):
        """
        Close serial connection and shutdown
        """
        self.instrument.close()
        self.reset()
        return

    def _write(self, string:str):
        """
        Sends message to instrument

        Args:
            string (str): <message code>,<option 1>[,<option 2>]

        Raises:
            Exception: Select a valid command code.
        
        Returns:
            str: two-character message code
        """
        message_code = string.split(',')[0].strip().upper()
        if message_code not in COMMANDS:
            raise Exception(f"Please select a valid command code from: {', '.join(COMMANDS)}")
        fstring = f'DMA,SN{self.channel},{string},END' # message template: <PRE>,<SN>,<CODE>,<OPTIONS>,<POST>
        bstring = bytearray.fromhex(fstring.encode('utf-8').hex())
        try:
            self.instrument.write(bstring)
            self.setFlag('busy', True)
        except Exception as e:
            if self.verbose:
                print(e)
        return message_code
    
    def _query(self, string:str, timeout_s=READ_TIMEOUT_S):
        """
        Send query and wait for response

        Args:
            string (str): message string
            timeout_s (int, optional): duration to wait before timeout. Defaults to READ_TIMEOUT_S.

        Returns:
            str: message readout
        """
        message_code = self._write(string)
        _start_time = time.time()
        response = ''
        while not self._is_expected_reply(message_code, response):
            if time.time() - _start_time > timeout_s and message_code != 'RUN':
                break
            response = self._read()
        self.setFlag('busy', False)
        time.sleep(0.1)
        return response
    
    def clearCache(self):
        """
        Clear data from instrument.
        """
        self._query('CLR,0')
        return
    
    def connect(self):
        """
        Reconnect to instrument using existing port and baudrate
        
        Returns:
            serial.Serial: serial connection to machine control unit if connection is successful, else None
        """
        return self._connect(self.port, self._baudrate, self._timeout)
    
    def initialise(self, low_frequency, high_frequency):
        if self._flags['initialised']:
            return
        self.frequency_range = low_frequency, high_frequency
        self._query(f"INIT,{','.join(self.frequency_codes)}")
        self.setFlag('initialised', True)
        return
    
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
        return self._flags['connected']

    def readAll(self, fields=[]):
        """
        Read all data on buffer

        Args:
            fields (list, optional): fields of interest. Defaults to [].
            
        Returns:
            pd.DataFrame: dataframe of measurements
        """
        response = self._query('GET,0') # Retrieve data from program here
        df = pd.DataFrame(response)
        return df
    
    def reset(self):
        """
        Reset the program, data, and flags
        """
        self._frequency_range_codes = ('','')
        self._flags = {
            'busy': False,
            'connected': False,
            'initialised': False,
            'measured': False,
            'read': False
        }
        return
        
    def setFlag(self, name:str, value:bool):
        """
        Set a flag truth value

        Args:
            name (str): label
            value (bool): flag value
        """
        self._flags[name] = value
        return
    
    def start(self, sample_thickness=1E-6):
        """
        Initialise the measurement
        """
        if not self._flags['initialised']:
            print("Please initialise the instrument using the 'initialise' method first")
            return
        self._query(f"RUN,{sample_thickness}")
        return
    
    def stopClamp(self):
        """
        Stop clamp movement
        """
        self._query('CLAMP,0')
        return
    
    def toggleClamp(self, on=False):
        """
        Toggle between clamp and release state

        Args:
            on (bool, optional): whether to clamp down on sample. Defaults to False.
        """
        option = -1 if on else 1
        self._query(f'CLAMP,{option}')
        return
