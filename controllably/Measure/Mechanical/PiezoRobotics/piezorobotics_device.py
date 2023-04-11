# %% -*- coding: utf-8 -*-
"""
This module holds the instrument class for tools from PiezoRobotics.

Classes:
    PiezoRoboticsDevice (Instrument)

Other constants and variables:
    FREQUENCIES (tuple)
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

FREQUENCIES = tuple([frequency.value for frequency in FrequencyCode])
"""Collection of all available frequency values"""

class PiezoRoboticsDevice(Instrument):
    """
    PiezoRoboticsDevice provides methods to interface with the characterisation device from PiezoRobotics

    ### Constructor
    Args:
        `port` (str): COM port address
        `channel` (int, optional): channel id. Defaults to 1.
        
    ### Attributes
    - `channel` (int): channel id
    
    ### Properties
    - `frequency` (Frequency): lower and upper frequency range limit
    
    ### Methods
    - `disconnect`: disconnect from device
    - `initialise`: initialise the device with the desired frequency range
    - `readAll`: read all the data on device buffer
    - `reset`: reset the device
    - `run`: start the measurement
    - `setFrequency`: frequency range to measure
    - `shutdown`: shutdown procedure for tool
    - `toggleClamp`: close or open the clamp
    """
    
    _default_flags = {
        'busy': False,
        'connected': False,
        'initialised': False,
        'measured': False,
        'read': False
    }
    def __init__(self, port:str, channel:int = 1, **kwargs):
        """
        Instantiate the class

        Args:
            port (str): COM port address
            channel (int, optional): channel id. Defaults to 1.
        """
        super().__init__(**kwargs)
        self.channel = channel
        self._frequency = Frequency()
        self._connect(port)
        pass
    
    # Properties
    @property
    def frequency(self) -> Frequency:
        return self._frequency
    @frequency.setter
    def frequency(self, value: tuple[float]):
        """
        Set the operating frequency range

        Args:
            value (tuple[float]): frequency lower and upper limits
        """
        self._frequency = self._range_finder(frequencies=value)
        return
    
    @property
    def port(self) -> str:
        return self.connection_details.get('port', '')
    
    def disconnect(self):
        """Disconnect from device"""
        try:
            self.device.close()
        except Exception as e:
            if self.verbose:
                print(e)
        self.setFlag(connected=False)
        return
    
    def initialise(self, low_frequency:Optional[float] = None, high_frequency:Optional[float] = None):
        """
        Initialise the device with the desired frequency range

        Args:
            low_frequency (Optional[float], optional): lowest desired frequency. Defaults to None.
            high_frequency (Optional[float], optional): highest desired frequency. Defaults to None.
        """
        if not all((low_frequency, high_frequency)):
            low_frequency, high_frequency = FREQUENCIES[0], FREQUENCIES[-1]
        if self.flags['initialised']:
            return
        frequency = self._range_finder(low_frequency, high_frequency)
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

    def readAll(self, **kwargs) -> pd.DataFrame:
        """
        Read all data on device buffer
            
        Returns:
            pd.DataFrame: dataframe of measurements
        """
        data = [line.split(', ') for line in self._query('GET,0') if ',' in line]
        df = pd.DataFrame(data[1:], columns=data[0], dtype=float)
        return df
    
    def reset(self) -> str:
        """Reset the device"""
        self._frequency = Frequency()
        self.resetFlags()
        return self._query('CLR,0')
    
    def run(self, sample_thickness:float = 1E-6) -> Optional[str]:
        """Start the measurement"""
        if not self.flags['initialised']:
            self.initialise()
        return self._query(f"RUN,{sample_thickness}")
    
    def setFrequency(self, low_frequency:float = None, high_frequency:float = None):
        """
        Set the frequency range to measure

        Args:
            low_frequency (Optional[float], optional): lowest desired frequency. Defaults to None.
            high_frequency (Optional[float], optional): highest desired frequency. Defaults to None.
        """
        return self.initialise(low_frequency=low_frequency, high_frequency=high_frequency)
    
    def shutdown(self):
        """Shutdown procedure for tool"""
        self.toggleClamp(False)
        return super().shutdown()
    
    def toggleClamp(self, on:bool = False) -> str:
        """
        Close or open the clamp

        Args:
            on (bool, optional): whether to clamp down on sample. Defaults to False.
            
        Returns:
            str: response string
        """
        option = -1 if on else 1
        return self._query(f'CLAMP,{option}')

    # Protected method(s)
    def _connect(self, port:str, baudrate:int = 115200, timeout:int = 1):
        """
        Connection procedure for tool

        Args:
            port (str): COM port address
            baudrate (int): baudrate. Defaults to 115200.
            timeout (int, optional): timeout in seconds. Defaults to None.
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
    
    def _query(self, command:str, timeout_s:int = 60) -> Union[str, tuple[str]]:
        """
        Write command to and read response from device

        Args:
            command (str): command string
            timeout_s (float, optional): duration to wait before timeout. Defaults to 60.

        Returns:
            Union[str, tuple[str]]: response string, or list of response strings
        """
        command_code = command.split(',')[0].strip().upper()
        if command_code not in CommandCode._member_names_:
            raise Exception(f"Please select a valid command code from: {', '.join(CommandCode._member_names_)}")
        
        start_time = time.time()
        self._write(command)
        cache = []
        response = ''
        while response != 'OKC':
            if timeout_s is not None and (time.time()-start_time) > timeout_s:
                print('Timeout! Aborting run...')
                break
            response = self._read()
            if command_code == 'GET' and len(response):
                cache.append(response)
        self.setFlag(busy=False)
        time.sleep(0.1)
        if command_code == 'GET':
            return tuple(cache)
        return response
    
    @staticmethod
    def _range_finder(frequency_1:float, frequency_2:float) -> Frequency:
        """
        Find the appropriate the operating frequency range

        Args:
            frequency_1 (float): lower frequency limit
            frequency_2 (float): upper frequency limit
            
        Returns:
            Frequency: optimal frequency range that covers desired values
        """
        frequencies = np.array(FREQUENCIES)
        low_frequency, high_frequency = sorted((frequency_1, frequency_2))
        lower = frequencies[frequencies < low_frequency]
        higher = frequencies[frequencies > high_frequency]
        low = lower[-1] if len(lower) else frequencies[0]
        high = higher[0] if len(higher) else frequencies[-1]
        return Frequency(low, high)
    
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
    
    def _write(self, command:str) -> bool:
        """
        Write command to device

        Args:
            command (str): <command code>,<option 1>[,<option 2>]
        
        Returns:
            bool: whether command was sent successfully
        """
        if self.verbose:
            print(command)
        fstring = f'DMA,SN{self.channel},{command},END' # command template: <PRE>,<SN>,<CODE>,<OPTIONS>,<POST>
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
