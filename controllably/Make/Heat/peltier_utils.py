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

COLUMNS = ['Time', 'Set', 'Hot', 'Cold', 'Power']
POWER_THRESHOLD = 10
TEMPERATURE_TOLERANCE = 1.5

class Peltier(object):
    """
    Peltier object

    Args:
        port (str): com port address
    """
    def __init__(self, port:str, tolerance:float = TEMPERATURE_TOLERANCE, **kwargs):
        
        self.device = None
        self._flags = {
            'busy': False,
            'connected': False,
            'get_feedback': False,
            'pause_feedback': False,
            'record': False,
            'temperature_reached': False
        }
        self._set_point = None
        self._temperature = None
        self._cold_point = None
        self._power = None
        
        self._precision = 3
        self._tolerance = tolerance
        self._threads = {}
        
        self.buffer_df = pd.DataFrame(columns=COLUMNS)
        
        self.verbose = False
        self.port = ''
        self._baudrate = None
        self._timeout = None
        self._connect(port)
        return
    @property
    def precision(self):
        return 10**(-self._precision)
    @precision.setter
    def precision(self, value:int):
        self._precision = value
        return
    
    @property
    def temperature(self):
        return round(self._temperature, self._precision)
    
    @property
    def tolerance(self):
        return f"+- {self._tolerance} °C"
    @tolerance.setter
    def tolerance(self, value:float):
        self._tolerance = abs(value)
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
            self.getTemperatures()
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
        print(response)
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
    
    def getTemperatures(self):
        """
        Get the temperatures from device
        
        Returns:
            str: device response
        """
        response = self._read()
        now = datetime.now()
        try:
            values = [float(v) for v in response.split(';')]
            self._set_point, self._temperature, self._cold_point, self._power = values
            ready = (abs(self._set_point - self._temperature)<=TEMPERATURE_TOLERANCE)
            if self.isReady():
                pass
            elif ready and self._power <= POWER_THRESHOLD:
                self.setFlag('temperature_reached', True)
                print(f"Temperature of {self._set_point}°C reached!")
            if self._flags.get('record', False):
                values = [now] + values
                row = {k:v for k,v in zip(COLUMNS, values)}
                self.buffer_df = self.buffer_df.append(row, ignore_index=True)
        except ValueError:
            pass
        return response
    
    def holdTemperature(self, temperature:float, time_s:float):
        """
        Hold a set temperature for duration

        Args:
            temperature (float): temperature in degree Celsius
            time_s (float): duration in seconds
        """
        self.setTemperature(temperature)
        print(f"Waiting for temperature to reach {self._set_point}°C")
        while not self.isReady():
            time.sleep(0.1)
        print(f"Holding at {self._set_point}°C for {time_s} seconds")
        time.sleep(time_s)
        print(f"End of temperature hold")
        return
    
    def isBusy(self):
        """
        Checks whether the Peltier device is busy
        
        Returns:
            bool: whether the Peltier device is busy
        """
        return self._flags['busy']
    
    def isConnected(self):
        """
        Check whether Peltier device is connected

        Returns:
            bool: whether Peltier device is connected
        """
        return self._flags['connected']
    
    def isReady(self):
        """
        Check whether target temperature is reached

        Returns:
            bool: whether target temperature is reached
        """
        return self._flags['temperature_reached']
    
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
    
    def setTemperature(self, set_point:int):
        """
        Set temperature of Pelteir device

        Args:
            set_point (int): temperature in degree Celsius
        """
        self.setFlag('pause_feedback', True)
        self.setFlag('temperature_reached', False)
        time.sleep(0.1)
        try:
            self.device.write(bytes(f"{set_point}\n", 'utf-8'))
        except AttributeError:
            pass
        print(f"New set temperature at {set_point}°C")
        self.setFlag('pause_feedback', False)
        return
    
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
        Toggle between start and stopping temperature records

        Args:
            on (bool): whether to start recording
        """
        self.setFlag('record', on)
        self.setFlag('get_feedback', on)
        self.setFlag('pause_feedback', False)
        self.toggleFeedbackLoop(on=on)
        return
