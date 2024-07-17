# %% -*- coding: utf-8 -*-
"""
This module holds the class for pH meter probe from Sentron.

Classes:
    SentronProbe (Measurer)
"""
# Standard library imports
from __future__ import annotations
from datetime import datetime
import logging
import pandas as pd
from threading import Thread
import time

# Third party imports
import serial # pip install pyserial

# Local application imports
from ...measure_utils import Measurer

logger = logging.getLogger(__name__)
logger.debug(f"Import: OK <{__name__}>")

COLUMNS = ('Time', 'pH', 'Temperature')
"""Headers for output data from pH meter"""

class SentronProbe(Measurer):
    """
    SentronProbe provides methods to read out values from a pH meter from Sentron

    ### Constructor
    Args:
        `port` (str): COM port address
    
    ### Attributes
    - `precision` (int): number of decimal places to print mass value

    ### Properties
    - `pH` (float): pH of sample
    - `port` (str): COM port address
    - `temperature (float): temperature of sample
    
    ### Methods
    - `clearCache`: clear most recent data and configurations
    - `disconnect`: disconnect from device
    - `getReadings`: get pH and temperature readings from tool
    - `shutdown`: shutdown procedure for tool
    - `toggleFeedbackLoop`: start or stop feedback loop
    - `toggleRecord`: start or stop data recording
    """
    
    _default_flags = {
        'busy': False,
        'connected': False,
        'get_feedback': False,
        'pause_feedback': False,
        'read': True,
        'record': False
    }
    
    _place: str = '.'.join(__name__.split('.')[1:-1])
    model = 'sentron_'
    def __init__(self, port:str, **kwargs):
        """
        Instantiate the class

        Args:
            port (str): COM port address
        """
        super().__init__(**kwargs)
        self.buffer_df = pd.DataFrame(columns=COLUMNS)
        self.precision = 3
        self._pH = 7
        self._temperature = 0
        self._threads = {}
        self._connect(port=port)
        return
    
    # Properties
    @property
    def pH(self) -> float:
        return round(self._pH, self.precision)
    
    @property
    def port(self) -> str:
        return self.connection_details.get('port', '')
    
    @property
    def temperature(self) -> float:
        return round(self._temperature, self.precision)
    
    def clearCache(self):
        """Clear most recent data and configurations"""
        return super().clearCache()
    
    def disconnect(self):
        """Disconnect from device"""
        self.device.close()
        return
    
    def getReadings(self, wait:int = 10) -> str:
        """
        Get pH and temperature readings from tool

        Args:
            wait (int, optional): duration to wait for the hardware to respond. Defaults to 10.

        Returns:
            str: device response
        """
        response = self._query(wait=wait)
        now = datetime.now()
        try:
            pH = float(response[26:33])
            temperature = float(response[34:38])
        except ValueError:
            pass
        else:
            self._pH = pH
            self._temperature = temperature
            if self.flags['record']:
                values = [
                    now, 
                    self._pH, 
                    self._temperature
                ]
                row = {k:v for k,v in zip(COLUMNS, values)}
                new_row_df = pd.DataFrame(row, index=[0])
                dfs = [_df for _df in [self.buffer_df, new_row_df] if len(_df)]
                self.buffer_df = pd.concat(dfs, ignore_index=True)
            print(f"pH = {pH:.3f}, temperature = {temperature:.1f}°C")
        return response
    
    def shutdown(self):
        """Shutdown procedure for tool"""
        self.toggleFeedbackLoop(on=False)
        return super().shutdown()
    
    def toggleFeedbackLoop(self, on:bool):
        """
        Start or stop feedback loop

        Args:
            on (bool): whether to start loop to continuously read from device
        """
        self.setFlag(get_feedback=on)
        if on:
            if 'feedback_loop' in self._threads:
                self._threads['feedback_loop'].join()
            thread = Thread(target=self._loop_feedback)
            thread.start()
            self._threads['feedback_loop'] = thread
        else:
            self._threads['feedback_loop'].join()
        return
    
    def toggleRecord(self, on:bool):
        """
        Start or stop data recording

        Args:
            on (bool): whether to start recording temperature
        """
        self.setFlag(record=on, get_feedback=on, pause_feedback=False)
        self.toggleFeedbackLoop(on=on)
        return
        
    # Protected method(s)
    def _connect(self, port:str, baudrate:int = 9600, timeout:int = 1):
        """
        Connection procedure for tool

        Args:
            port (str): COM port address
            baudrate (int, optional): baudrate. Defaults to 9600.
            timeout (int, optional): timeout in seconds. Defaults to 1.
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
            time.sleep(1)
        self.device = device
        return
    
    def _loop_feedback(self):
        """Loop to constantly read from device"""
        print('Listening...')
        while self.flags['get_feedback']:
            if self.flags['pause_feedback']:
                continue
            self.getReadings()
        print('Stop listening...')
        return
    
    def _query(self, wait:float = 10) -> str:
        """
        Write command to and read response from device

        Args:
            wait (float, optional): duration, in seconds, to wait for response. Defaults to 10.

        Returns:
            str: response string
        """
        if self.device is None:
            return ''
        self.device.write('ACT'.encode('utf-8'))    # Manual pp.36 sending the string 'ACT' queries the pH meter
        time.sleep(wait)                            # require a delay between writing to and reading from the pH meter 
        return self._read()
    
    def _read(self) -> str:
        """
        Read response from device

        Returns:
            str: response string
        """
        response = ''
        try:
            response = self.device.read_until('\r\n')
        except Exception as e:
            if self.verbose:
                print(e)
        else:
            response = response.decode('utf-8').strip()
            if self.verbose:
                print(response)
        return response
    