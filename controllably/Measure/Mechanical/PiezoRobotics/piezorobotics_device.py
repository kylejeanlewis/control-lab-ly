# %% -*- coding: utf-8 -*-
"""
Adapted from DMA code by @pablo

Created: Tue 2023/01/03 17:13:35
@author: Chang Jie

Notes / actionables:
-
"""
# Standard library imports
from __future__ import annotations
import numpy as np
import pandas as pd
import time
from typing import Optional, Union

# Third party imports
import serial # pip install pyserial

# Local application imports
from ...instrument_utils import Instrument
from .piezorobotics_lib import CommandCode, ErrorCode, FrequencyCode, Frequency
print(f"Import: OK <{__name__}>")

FREQUENCIES = np.array([frequency.value for frequency in FrequencyCode])

class PiezoRoboticsDevice(Instrument):
    """
    PiezoRoboticsDevice object

    Args:
        port (str): com port address
        channel (int, optional): assigned device channel. Defaults to 1.
    """
    _default_flags = {
        'busy': False,
        'connected': False,
        'initialised': False,
        'measured': False,
        'read': False
    }
    def __init__(self, port:str, channel=1, **kwargs):
        self.channel = channel
        self._frequency = Frequency()
        self._connect(port)
        pass
    
    @property
    def frequency(self) -> Frequency:
        return self._frequency
    @frequency.setter
    def frequency(self, value: tuple[float]):
        """
        Set the operating frequency range

        Args:
            frequencies (iterable): frequency lower and upper limits
                low_frequency (float): lower frequency limit
                high_frequency (float): upper frequency limit
        """
        self._frequency = self.range_finder(frequencies=value)
        return
    
    def disconnect(self):
        try:
            self.device.close()
        except Exception as e:
            if self.verbose:
                print(e)
        self.setFlag(connected=False)
        return
    
    def initialise(self, low_frequency:Optional[float] = None, high_frequency:Optional[float] = None):
        if not all((low_frequency, high_frequency)):
            low_frequency, high_frequency = FREQUENCIES[0], FREQUENCIES[-1]
        if self.flags['initialised']:
            return
        frequency = self.range_finder(low_frequency, high_frequency)
        if frequency == self.frequency:
            print('Appropriate frequency range remains the same!')
        else:
            self.reset()
            self._frequency = frequency
            input("Ensure no samples within the clamp area during initialization. Press 'Enter' to proceed.")
            self._query(f"INIT,{','.join(self.frequency.code)}")
        self.setFlag(initialised=True)
        print(self.frequency)
        return

    @staticmethod
    def range_finder(frequency_1:float, frequency_2:float) -> Frequency:
        """
        Find the appropriate the operating frequency range

        Args:
            frequencies (iterable): frequency lower and upper limits
                low_frequency (float): lower frequency limit
                high_frequency (float): upper frequency limit
        """
        low_frequency, high_frequency = sorted((frequency_1, frequency_2))
        lower = FREQUENCIES[FREQUENCIES < low_frequency]
        higher = FREQUENCIES[FREQUENCIES > high_frequency]
        low = lower[-1] if len(lower) else FREQUENCIES[0]
        high = higher[0] if len(higher) else FREQUENCIES[-1]
        return Frequency(low, high)

    def readAll(self, **kwargs) -> pd.DataFrame:
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
    
    def reset(self) -> str:
        """
        Clear settings from device. Reset the program, data, and flags
        """
        self._frequency = Frequency()
        self.resetFlags()
        return self._query('CLR,0')
    
    def run(self, sample_thickness:float = 1E-6) -> Optional[str]:
        """
        Initialise the measurement
        """
        if not self.flags['initialised']:
            self.initialise()
        return self._query(f"RUN,{sample_thickness}")
    
    def setFrequency(self, low_frequency:float = None, high_frequency:float = None):
        return self.initialise(low_frequency=low_frequency, high_frequency=high_frequency)
    
    def shutdown(self):
        """
        Close serial connection and shutdown
        """
        self.toggleClamp(False)
        self.reset()
        self.disconnect()
        return
    
    def toggleClamp(self, on:bool = False) -> str:
        """
        Toggle between clamp and release state

        Args:
            on (bool, optional): whether to clamp down on sample. Defaults to False.
        """
        option = -1 if on else 1
        return self._query(f'CLAMP,{option}')

    # Protected method(s)
    def _connect(self, port:str, baudrate:int = 115200, timeout:int = 1):
        """
        Connect to machine control unit

        Args:
            port (str): com port address
            baudrate (int): baudrate. Defaults to 115200.
            timeout (int, optional): timeout in seconds. Defaults to None.
            
        Returns:
            serial.Serial: serial connection to machine control unit if connection is successful, else None
        """
        self.connection_details = {
            'port': port,
            'baudrate': baudrate,
            'timeout': timeout
        }
        device = None
        try:
            device = serial.Serial(port, baudrate, timeout=timeout)
        except Exception as e:
            print(f"Could not connect to {port}")
            if self.verbose:
                print(e)
        else:
            print(f"Connection opened to {port}")
            self.setFlag(connected=True)
        self.device = device
        return
    
    def _query(self, message:str, timeout_s:int = 60) -> Union[str, tuple[str]]:
        """
        Send query and wait for response

        Args:
            message (str): message string
            timeout_s (int, optional): duration to wait before timeout. If None, no timeout duration. Defaults to 60.

        Yields:
            str: response string
        """
        message_code = message.split(',')[0].strip().upper()
        if message_code not in CommandCode._member_names_:
            raise Exception(f"Please select a valid command code from: {', '.join(CommandCode._member_names_)}")
        
        start_time = time.time()
        self._write(message)
        cache = []
        response = ''
        while response != 'OKC':
            if timeout_s is not None and (time.time()-start_time) > timeout_s:
                print('Timeout! Aborting run...')
                break
            response = self._read()
            if message_code == 'GET' and len(response):
                cache.append(response)
        self.setFlag(busy=False)
        time.sleep(0.1)
        if message_code == 'GET':
            return tuple(cache)
        return response
    
    def _read(self) -> str:
        """
        Read response from device

        Returns:
            str: response string
        """
        response = ''
        try:
            response = self.device.readline()
            response = response.decode("utf-8").strip()
        except AttributeError:
            pass
        except Exception as e:
            if self.verbose:
                print(e)
        else:
            if len(response) and (self.verbose or 'High-Voltage' in response):
                print(response)
            if response in ErrorCode._member_names_:
                print(ErrorCode[response].value)
        return response
    
    def _write(self, message:str) -> bool:
        """
        Sends message to device

        Args:
            message (str): <message code>,<option 1>[,<option 2>]

        Raises:
            Exception: Select a valid command code.
        
        Returns:
            str: two-character message code
        """
        if self.verbose:
            print(message)
        fstring = f'DMA,SN{self.channel},{message},END' # message template: <PRE>,<SN>,<CODE>,<OPTIONS>,<POST>
        # bstring = bytearray.fromhex(fstring.encode('utf-8').hex())
        try:
            self.device.write(fstring.encode('utf-8'))
        except AttributeError:
            pass
        except Exception as e:
            if self.verbose:
                print(e)
            return False
        self.setFlag(busy=True)
        return True


    ### NOTE: DEPRECATE
    def stopClamp(self):
        """
        Stop clamp movement
        """
        # self._query('CLAMP,0')
        print('Stop clamp function not available.')
        return
