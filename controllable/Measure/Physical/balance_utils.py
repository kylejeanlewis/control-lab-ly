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
print(f"Import: OK <{__name__}>")

CALIBRATION_FACTOR = 6.862879436681862 # factor by which to divide output reading by to get mass in mg
COLUMNS = ['Time', 'Value', 'Factor', 'Baseline', 'Mass']

class MassBalance(object):
    def __init__(self, port:str, calibration_factor:float = CALIBRATION_FACTOR, **kwargs):
        """
        Mass Balance object

        Args:
            port (str): com port address
        """
        self.device = None
        self.baseline = 0
        self.calibration_factor = calibration_factor
        self._flags = {
            'busy': False,
            'connected': False,
            'get_feedback': False,
            'pause_feedback': False,
            'record': False
        }
        self._mass = 0
        self._precision = 3
        self._threads = {}
        
        self.buffer_df = pd.DataFrame(columns=COLUMNS)
        
        self.verbose = False
        self.port = ''
        self._baudrate = None
        self._timeout = None
        self._connect(port)
        return
    
    @property
    def mass(self):
        return round(self._mass, self._precision)
    
    @property
    def precision(self):
        return 10**(-self._precision)
    @precision.setter
    def precision(self, value:int):
        self._precision = value
        return
    
    def __delete__(self):
        self._shutdown()
        return
    
    def _connect(self, port:str, baudrate=115200, timeout=1):
        """
        Connect to machine control unit

        Args:
            port (str): com port address
            baudrate (int): baudrate. Defaults to 9600.
            timeout (int, optional): timeout in seconds. Defaults to None.
            
        Returns:
            serial.Serial: serial connection to machine control unit if connection is successful, else None
        """
        self.port = port
        self._baudrate = baudrate
        self._timeout = timeout
        device = None
        try:
            device = serial.Serial(port, self._baudrate, timeout=self._timeout)
            self.device = device
            print(f"Connection opened to {port}")
            self.setFlag('connected', True)
            # self.toggleFeedbackLoop(on=True)
        except Exception as e:
            print(f"Could not connect to {port}")
            if self.verbose:
                print(e)
        return self.device
    
    def _loop_feedback(self):
        """
        Feedback loop to constantly check status and liquid level
        """
        print('Listening...')
        while self._flags['get_feedback']:
            if self._flags['pause_feedback']:
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
            response = response.decode('utf-8').strip()
        except Exception as e:
            if self.verbose:
                print(e)
        return response
    
    def _shutdown(self):
        """
        Close serial connection and shutdown
        """
        self.toggleFeedbackLoop(on=False)
        self.device.close()
        self._flags = {
            'busy': False,
            'connected': False,
            'get_feedback': False,
            'pause_feedback':False
        }
        return
    
    def clearCache(self):
        """
        Clear dataframe.
        """
        self.setFlag('pause_feedback', True)
        time.sleep(0.1)
        self.buffer_df = pd.DataFrame(columns=COLUMNS)
        self.setFlag('pause_feedback', False)
        return
    
    def connect(self):
        """
        Reconnect to device using existing port and baudrate
        
        Returns:
            serial.Serial: serial connection to machine control unit if connection is successful, else None
        """
        return self._connect(self.port, self._baudrate, self._timeout)
    
    def getMass(self):
        """
        Get the mass by measuring force response
        
        Returns:
            str: device response
        """
        response = self._read()
        try:
            value = int(response)
            self._mass = (value - self.baseline) / self.calibration_factor
            if self._flags.get('record', False):
                row = {
                    'Time': datetime.now(), 
                    'Value': value,
                    'Factor': self.calibration_factor,
                    'Baseline': self.baseline,
                    'Mass': self._mass
                }
                self.buffer_df = self.buffer_df.append(row, ignore_index=True)
        except ValueError:
            pass
        return response

    def isBusy(self):
        """
        Checks whether the pipette is busy
        
        Returns:
            bool: whether the pipette is busy
        """
        return self._flags['busy']
    
    def isConnected(self):
        """
        Check whether pipette is connected

        Returns:
            bool: whether pipette is connected
        """
        return self._flags['connected']
    
    def reset(self):
        """
        Reset baseline and clear buffer
        """
        self.baseline = 0
        self.clearCache()
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
        self.setFlag('get_feedback', on)
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
        self.setFlag('record', on)
        self.setFlag('get_feedback', on)
        self.setFlag('pause_feedback', False)
        self.toggleFeedbackLoop(on=on)
        return

    def zero(self, wait=5):
        """
        Set current reading as baseline (i.e. zero mass)
        
        Args:
            wait (int, optional): duration to wait while zeroing (seconds). Defaults to 5.
        """
        temp_record_state = self._flags.get('record', False)
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
