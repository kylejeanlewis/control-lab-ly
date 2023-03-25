# %% -*- coding: utf-8 -*-
"""
Created: Tue 2023/01/16 11:11:00
@author: Chang Jie

Notes / actionables:
-
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

CALIBRATION_FACTOR = 6.862879436681862 # Empirical: factor by which to divide output reading by to get mass in mg
COLUMNS = ['Time', 'Value', 'Factor', 'Baseline', 'Mass']

class MassBalance(Measurer):
    """
    Mass Balance object

    Args:
        port (str): com port address
    """
    _default_flags = {
        'busy': False,
        'connected': False,
        'get_feedback': False,
        'pause_feedback': False,
        'record': False
    }
    def __init__(self, port:str, calibration_factor:float = CALIBRATION_FACTOR, **kwargs):
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
   
    def clearCache(self):
        """
        Clear dataframe.
        """
        self.setFlag(pause_feedback=True)
        time.sleep(0.1)
        self.buffer_df = pd.DataFrame(columns=COLUMNS)
        self.setFlag(pause_feedback=False)
        return
    
    def connect(self):
        """
        Reconnect to device using existing port and baudrate
        
        Returns:
            serial.Serial: serial connection to machine control unit if connection is successful, else None
        """
        return self._connect(**self.connection_details)
    
    def disconnect(self):
        try:
            self.device.close()
        except Exception as e:
            if self.verbose:
                print(e)
        self.setFlag(connected=False)
        return
    
    def getMass(self) -> str:
        """
        Get the mass by measuring force response
        
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
                self.buffer_df = self.buffer_df.append(row, ignore_index=True)
        return response
  
    def reset(self):
        """
        Reset baseline and clear buffer
        """
        self.baseline = 0
        self.clearCache()
        return
    
    def shutdown(self):
        """
        Close serial connection and shutdown
        """
        self.toggleFeedbackLoop(on=False)
        self.disconnect()
        self.resetFlags()
        return
 
    def tare(self):
        """
        Alias for zero
        """
        return self.zero()
    
    def toggleFeedbackLoop(self, on:bool):
        """
        Toggle between start and stopping feedback loop

        Args:
            on (bool): whether to listen to feedback
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
        Toggle between start and stopping mass records

        Args:
            on (bool): whether to start recording
        """
        self.setFlag(record=on, get_feedback=on, pause_feedback=False)
        self.toggleFeedbackLoop(on=on)
        return

    def zero(self, wait:int = 5):
        """
        Set current reading as baseline (i.e. zero mass)
        
        Args:
            wait (int, optional): duration to wait while zeroing (seconds). Defaults to 5.
        """
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
        Connect to machine control unit

        Args:
            port (str): com port address
            baudrate (int): baudrate. Defaults to 9600.
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
            time.sleep(1)
            self.zero()
        self.device = device
        return
    
    def _loop_feedback(self):
        """
        Feedback loop to constantly check status and liquid level
        """
        print('Listening...')
        while self.flags['get_feedback']:
            if self.flags['pause_feedback']:
                continue
            self.getMass()
        print('Stop listening...')
        return

    def _read(self):
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
 