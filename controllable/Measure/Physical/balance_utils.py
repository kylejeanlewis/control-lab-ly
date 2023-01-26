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

READ_TIMEOUT_S = 2
CALIB_MASS = 6.700627450980402 * 0.9955 # initial calibration factor * subsequent validation factor

class MassBalance(object):
    def __init__(self, port:str, **kwargs):
        """
        Mass Balance object

        Args:
            port (str): com port address
        """
        self.device = None
        self._flags = {
            'busy': False,
            'connected': False,
            'get_feedback': False,
            'pause_feedback':False
        }
        self._mass = 0
        self._precision = 3
        self._threads = {}
        
        self.buffer_df = pd.DataFrame(columns=['Time', 'Value'])
        
        self.verbose = True
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
            self.toggleFeedbackLoop(on=True)
        except Exception as e:
            if self.verbose:
                print(f"Could not connect to {port}")
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
            # print(repr(response))
        except Exception as e:
            if self.verbose:
                # print(e)
                pass
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
            self._mass = value / CALIB_MASS
            self.buffer_df = self.buffer_df.append({'Time': datetime.now(), 'Value': self._mass}, ignore_index=True)
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
        Reset dataframe.
        
        Returns:
            str: device response
        """
        self.setFlag('pause_feedback', True)
        self.buffer_df = pd.DataFrame(columns=['Time', 'Value'])
        self.setFlag('pause_feedback', False)
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
        
        Args:
            channel (int, optional): channel to reset. Defaults to None.

        Returns:
            str: device response
        """
        return self.zero()
    
    def toggleFeedbackLoop(self, on:bool):
        """
        Toggle between start and stopping feedback loop
        
        Args:
            channel (int, optional): channel to toggle feedback loop. Defaults to None.

        Args:
            on (bool): whether to listen to feedback
        """
        self.setFlag('get_feedback', on)
        if on:
            thread = Thread(target=self._loop_feedback)
            thread.start()
            self._threads['feedback_loop'] = thread
        else:
            self._threads['feedback_loop'].join()
        return
    
    def toggleLivePlot(self, on:bool):
        """
        Toggle between start and stopping feedback loop
        
        Args:
            channel (int, optional): channel to toggle feedback loop. Defaults to None.

        Args:
            on (bool): whether to listen to feedback
        """
        if on:
            thread = Thread(target=self._loop_feedback)
            thread.start()
            self._threads['feedback_loop'] = thread
        else:
            self._threads['feedback_loop'].join()
        return

    def zero(self):
        """
        Zero the plunger position
        
        Args:
            channel (int, optional): channel to zero. Defaults to None.

        Returns:
            str: device response
        """
        return
    
    def update_plot(self, fig):
        return fig
        
