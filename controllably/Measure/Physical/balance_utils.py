# %% -*- coding: utf-8 -*-
"""
This module holds the class for mass balances.

Classes:
    MassBalance (Measurer)

Other constants and variables:
    CALIBRATION_FACTOR (float)
    COLUMNS (tuple)
"""
# Standard library imports
from datetime import datetime
import pandas as pd
from threading import Thread
import time

# Third party imports
import serial # pip install pyserial

# Local application imports
from ..measure_utils import Measurer
print(f"Import: OK <{__name__}>")

CALIBRATION_FACTOR = 6.862879436681862
"""Empirical factor by which to divide output reading by to get mass in mg"""
COLUMNS = ('Time', 'Value', 'Factor', 'Baseline', 'Mass')
"""Headers for output data from mass balance"""

class MassBalance(Measurer):
    """
    MassBalance provides methods to read out values from a precision mass balance

    ### Constructor
    Args:
        `port` (str): COM port address
        `calibration_factor` (float, optional): calibration factor of device readout to mg. Defaults to CALIBRATION_FACTOR.
    
    ### Attributes
    - `baseline` (float): baseline readout at which zero mass is set
    - `calibration_factor` (float): calibration factor of device readout to mg
    - `precision` (int): number of decimal places to print mass value
    
    ### Properties
    - `mass` (float): mass of sample
    - `port` (str): COM port address
    
    ### Methods
    - `clearCache`: clear most recent data and configurations
    - `disconnect`: disconnect from device
    - `getMass`: get the mass of the sample by measuring the force response
    - `reset`: reset the device
    - `shutdown`: shutdown procedure for tool
    - `tare`: alias for `zero()`
    - `toggleFeedbackLoop`: start or stop feedback loop
    - `toggleRecord`: start or stop data recording
    - `zero`: set the current reading as baseline (i.e. zero mass)
    """
    
    _default_flags = {
        'busy': False,
        'connected': False,
        'get_feedback': False,
        'pause_feedback': False,
        'read': True,
        'record': False
    }
    def __init__(self, port:str, calibration_factor:float = CALIBRATION_FACTOR, **kwargs):
        """
        Instantiate the class

        Args:
            port (str): COM port address
            calibration_factor (float, optional): calibration factor of device readout to mg. Defaults to CALIBRATION_FACTOR.
        """
        super().__init__(**kwargs)
        self.baseline = 0
        self.buffer_df = pd.DataFrame(columns=COLUMNS)
        self.calibration_factor = calibration_factor
        self.precision = 3
        self._mass = 0
        self._threads = {}
        self._connect(port)
        return
    
    # Properties
    @property
    def mass(self) -> float:
        return round(self._mass, self.precision)
    
    @property
    def port(self) -> str:
        return self.connection_details.get('port', '')
   
    def clearCache(self):
        """Clear most recent data and configurations"""
        self.setFlag(pause_feedback=True)
        time.sleep(0.1)
        self.buffer_df = pd.DataFrame(columns=COLUMNS)
        self.setFlag(pause_feedback=False)
        return
    
    def disconnect(self):
        """Disconnect from device"""
        try:
            self.device.close()
        except Exception as e:
            if self.verbose:
                print(e)
        self.setFlag(connected=False)
        return
    
    def getMass(self) -> str:
        """
        Get the mass of the sample by measuring the force response
        
        Returns:
            str: device response
        """
        response = self._read()
        now = datetime.now()
        try:
            value = int(response)
        except ValueError:
            pass
        else:
            self._mass = (value - self.baseline) / self.calibration_factor
            if self.flags['record']:
                values = [
                    now, 
                    value, 
                    self.calibration_factor, 
                    self.baseline, 
                    self._mass
                ]
                row = {k:v for k,v in zip(COLUMNS, values)}
                new_row_df = pd.DataFrame(row, index=[0])
                self.buffer_df = pd.concat([self.buffer_df, new_row_df], ignore_index=True)
        return response
  
    def reset(self):
        """Reset the device"""
        super().reset()
        self.baseline = 0
        return
    
    def shutdown(self):
        """Shutdown procedure for tool"""
        self.toggleFeedbackLoop(on=False)
        return super().shutdown()
 
    def tare(self):
        """Alias for `zero()`"""
        return self.zero()
    
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
            on (bool): whether to start recording data
        """
        self.setFlag(record=on, get_feedback=on, pause_feedback=False)
        self.toggleFeedbackLoop(on=on)
        return

    def zero(self, wait:int = 5):
        """
        Set current reading as baseline (i.e. zero mass)
        
        Args:
            wait (int, optional): duration to wait while zeroing, in seconds. Defaults to 5.
        """
        if self.flags['record']:
            print("Unable to zero while recording.")
            print("Use `toggleRecord(False)` to stop recording.")
            return
        temp_record_state = self.flags['record']
        temp_buffer_df = self.buffer_df.copy()
        self.reset()
        self.toggleRecord(True)
        print(f"Zeroing... ({wait}s)")
        time.sleep(wait)
        self.toggleRecord(False)
        self.baseline = self.buffer_df['Value'].mean()
        self.clearCache()
        self.buffer_df = temp_buffer_df.copy()
        print("Zeroing complete.")
        self.toggleRecord(temp_record_state)
        return

    # Protected method(s)
    def _connect(self, port:str, baudrate:int = 115200, timeout:int = 1):
        """
        Connection procedure for tool

        Args:
            port (str): COM port address
            baudrate (int, optional): baudrate. Defaults to 115200.
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
            self.zero()
        self.device = device
        return
    
    def _loop_feedback(self):
        """Loop to constantly read from device"""
        print('Listening...')
        while self.flags['get_feedback']:
            if self.flags['pause_feedback']:
                continue
            self.getMass()
        print('Stop listening...')
        return

    def _read(self) -> str:
        """
        Read response from device

        Returns:
            str: response string
        """
        response = ''
        try:
            response = self.device.readline()
        except Exception as e:
            if self.verbose:
                print(e)
        else:
            response = response.decode('utf-8').strip()
            if self.verbose:
                print(response)
        return response
 