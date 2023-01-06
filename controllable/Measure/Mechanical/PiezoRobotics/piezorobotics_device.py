# %% -*- coding: utf-8 -*-
"""
Adapted from DMA code by @pablo

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

TIMEOUT_S = 60

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
        
        self._frequency_range_codes = ('0','0')
        
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
        lo_code_number, hi_code_number = self.range_finder(frequencies=frequencies)
        self._frequency_range_codes = (f'FREQ_{lo_code_number:02}', f'FREQ_{hi_code_number:02}')
        return
    
    @staticmethod
    def range_finder(frequencies):
        """
        Find the appropriate the operating frequency range

        Args:
            frequencies (iterable): frequency lower and upper limits
                low_frequency (float): lower frequency limit
                high_frequency (float): upper frequency limit
        """
        low_frequency, high_frequency = sorted(list(frequencies))
        all_freq = np.array(FREQUENCIES)
        freq_in_range_indices = np.where((all_freq>=low_frequency) & (all_freq<=high_frequency))
        lo_code_number = max( (freq_in_range_indices[0][0]+1) - 1, 1)
        hi_code_number = min( (freq_in_range_indices[0][-1]+1) + 1, len(all_freq))
        return lo_code_number, hi_code_number
    
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
        return self.instrument
    
    def _query(self, string:str, timeout_s=TIMEOUT_S):
        """
        Send query and wait for reponse

        Args:
            string (str): message string
            timeout_s (int, optional): duration to wait before timeout. If None, no timeout duration. Defaults to TIMEOUT_S.

        Yields:
            str: response string
        """
        start_time = time.time()
        message_code = self._write(string)
        cache = []
        response = ''
        while response != 'OKC':
            if timeout_s is not None and (time.time()-start_time) > timeout_s:
                print('Timeout! Aborting run...')
                break
            response = self._read()
            if message_code == 'GET' and len(response):
                cache.append(response)

        self.setFlag('busy', False)
        time.sleep(0.1)
        if message_code == 'GET':
            return cache
        return response
    
    def _read(self):
        """
        Read response from instrument

        Returns:
            str: response string
        """
        response = ''
        try:
            response = self.instrument.readline()
            response = response.decode("utf-8").strip()
            if len(response) and (self.verbose or 'High-Voltage' in response):
                print(response)
            if response in ERRORS:
                print(ErrorCode[response].value)
        except Exception as e:
            if self.verbose:
                pass
        return response
    
    def _shutdown(self):
        """
        Close serial connection and shutdown
        """
        self.toggleClamp(False)
        self.reset()
        self.instrument.close()
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
            print(e)
        if self.verbose:
            print(fstring)
        return message_code
    
    def close(self):
        """
        Alias for _shutdown method
        """
        return self._shutdown()
    
    def connect(self):
        """
        Reconnect to instrument using existing port and baudrate
        
        Returns:
            serial.Serial: serial connection to machine control unit if connection is successful, else None
        """
        return self._connect(self.port, self._baudrate, self._timeout)
    
    def initialise(self, low_frequency, high_frequency): # TODO: check frequencies if same as previous
        if self._flags['initialised']:
            return
        if self.range_finder((low_frequency, high_frequency)) == self.frequency_codes:
            print('Appropriate frequency range remains the same!')
        else:
            if any(self.frequency_codes):
                self.reset()
            self.frequency_range = low_frequency, high_frequency
            input("Ensure no samples within the clamp area during initialization. Press 'Enter' to proceed.")
            self._query(f"INIT,{','.join([str(_f) for _f in self.frequency_codes])}")
        self.setFlag('initialised', True)
        print(self.frequency_range)
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

    def readAll(self, **kwargs):
        """
        Read all data on buffer

        Args:
            fields (list, optional): fields of interest. Defaults to [].
            
        Returns:
            pd.DataFrame: dataframe of measurements
        """
        data = [line.split(', ') for line in self._query('GET,0') if ',' in line]
        df = pd.DataFrame(data[1:], columns=data[0], dtype=float)
        return df
    
    def reset(self):
        """
        Clear settings from instrument. Reset the program, data, and flags
        """
        self._query('CLR,0')
        self._frequency_range_codes = ('0','0')
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
        # self._query('CLAMP,0')
        print('Stop clamp function not available.')
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
