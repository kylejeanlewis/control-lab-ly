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
POWER_THRESHOLD = 20
STABILIZE_TIME_S = 10
TEMPERATURE_TOLERANCE = 1.5

class Peltier(object):
    """
    A Peltier device generates heat to provide local temperature control of the sample.

    ### Constructor
    Args:
        `port` (str): com port address
        `tolerance` (float, optional): temperature tolerance to determine if device has reached target temperature. Defaults to `TEMPERATURE_TOLERANCE` (i.e. 1.5).
        
    ### Attributes:
    - `buffer_df` (pandas.DataFrame): data output from device
    - `device` (serial.Serial): serial connection to device
    - `port` (str): com port address
    - `precision` (int): number of decimal places to display current temperature
    - `temperature` (float): current temperature of device
    - `tolerance` (float): temperature tolerance
    - `verbose` (bool): verbosity of class
    
    ### Methods:
    - `clearCache`: clears and remove data in buffer
    - `connect`: connects to the device using the existing port, baudrate and timeout values
    - `getTemperatures`: reads from the device the set temperature, hot temperature, cold temperature, and the power level
    - `holdTemperature`: holds the device temperature at target temperature for specified duration
    - `isBusy`: checks whether the device is busy
    - `isConnected`: checks whether the device is connected
    - `isReady`: checks whether the device has reached the set temperature
    - `reset`: clears data in buffer and set the temperature to room temperature (i.e. 25°C)
    - `setFlag`: set value of flag
    - `setTemperature`: change the set temperature
    - `toggleFeedbackLoop`: toggle the feedback loop thread on or off
    - `toggleRecord`: toggle the data recording on or off
    """
    
    def __init__(self, port:str, tolerance:float = TEMPERATURE_TOLERANCE):
        """
        Construct the Peltier object

        Args:
            `port` (str): com port address
            `tolerance` (float, optional): temperature tolerance to determine if device has reached target temperature. Defaults to `TEMPERATURE_TOLERANCE` (i.e. 1.5).
        """
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
        self._stabilize_time = None
        self._tolerance = tolerance
        self._threads = {}
        
        self.buffer_df = pd.DataFrame(columns=COLUMNS)
        
        self.verbose = True
        self.port = ''
        self._baudrate = None
        self._timeout = None
        self._connect(port)
        return
    
    @property
    def precision(self):
        return self._precision
    @precision.setter
    def precision(self, value:int):
        self._precision = abs(value)
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
    
    def _connect(self, port:str, baudrate:int = 115200, timeout:int = 1):
        """
        Connect to machine control unit

        Args:
            `port` (str): com port address
            `baudrate` (int, optional): baudrate. Defaults to 115200.
            `timeout` (int, optional): timeout in seconds. Defaults to 1.
            
        Returns:
            `serial.Serial`: serial connection to machine control unit if connection is successful, else `None`
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
            time.sleep(1)
            print(self.getTemperatures())
            # self.toggleFeedbackLoop(on=True)
        except Exception as e:
            print(f"Could not connect to {port}")
            if self.verbose:
                print(e)
        return self.device
    
    def _loop_feedback(self):
        """
        Feedback loop to constantly read values from device
        """
        print('Listening...')
        while self._flags['get_feedback']:
            if self._flags['pause_feedback']:
                continue
            self.getTemperatures()
            time.sleep(0.1)
        print('Stop listening...')
        return

    def _read(self):
        """
        Read values from the device

        Returns:
            `str`: response string
        """
        response = ''
        try:
            response = self.device.readline()
            response = response.decode('utf-8').strip()
        except Exception as e:
            if self.verbose:
                print(e)
        # print(response)
        return response
    
    def _shutdown(self):
        """
        Close serial connection and shutdown feedback loop
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
        Clear data from buffer
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
            `serial.Serial`: serial connection to machine control unit if connection is successful, else `None`
        """
        return self._connect(self.port, self._baudrate, self._timeout)
    
    def getTemperatures(self):
        """
        Reads from the device the set temperature, hot temperature, cold temperature, and the power level
        
        Returns:
            `str`: response from device output
        """
        response = self._read()
        now = datetime.now()
        try:
            values = [float(v) for v in response.split(';')]
            self._set_point, self._temperature, self._cold_point, self._power = values
            ready = (abs(self._set_point - self._temperature)<=TEMPERATURE_TOLERANCE)
            if not ready:
                pass
            elif not self._stabilize_time:
                self._stabilize_time = time.time()
                print(response)
            elif self._flags['temperature_reached']:
                pass
            elif (self._power <= POWER_THRESHOLD) or (time.time()-self._stabilize_time >= STABILIZE_TIME_S):
                print(response)
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
        Hold the device temperature at target temperature for specified duration

        Args:
            `temperature` (float): temperature in degree Celsius
            `time_s` (float): duration in seconds
        """
        self.setTemperature(temperature)
        print(f"Holding at {self._set_point}°C for {time_s} seconds")
        time.sleep(time_s)
        print(f"End of temperature hold")
        return
    
    def isBusy(self):
        """
        Check whether the device is busy
        
        Returns:
            `bool`: whether the device is busy
        """
        return self._flags['busy']
    
    def isConnected(self):
        """
        Check whether the device is connected

        Returns:
            `bool`: whether the device is connected
        """
        return self._flags['connected']
    
    def isReady(self):
        """
        Check whether target temperature has been reached

        Returns:
            `bool`: whether target temperature has been reached
        """
        return self._flags['temperature_reached']
    
    def reset(self):
        """
        Clears data in buffer and set the temperature to room temperature (i.e. 25°C)
        """
        self.toggleRecord(False)
        self.clearCache()
        self.setTemperature(set_point=25, blocking=False)
        return

    def setFlag(self, name:str, value:bool):
        """
        Set a flag's truth value

        Args:
            `name` (str): label
            `value` (bool): flag value
        """
        self._flags[name] = value
        return
    
    def setTemperature(self, set_point:int, blocking:bool = True):
        """
        Set temperature of the device

        Args:
            `set_point` (int): target temperature in degree Celsius
        """
        self.setFlag('pause_feedback', True)
        time.sleep(0.5)
        try:
            self.device.write(bytes(f"{set_point}\n", 'utf-8'))
            while self._set_point != float(set_point):
                self.getTemperatures()
        except AttributeError:
            pass
        print(f"New set temperature at {set_point}°C")
        
        self._stabilize_time = None
        self.setFlag('temperature_reached', False)
        self.setFlag('pause_feedback', False)
        print(f"Waiting for temperature to reach {self._set_point}°C")
        while not self.isReady():
            if not self._flags['get_feedback']:
                self.getTemperatures()
            time.sleep(0.1)
            if not blocking:
                break
        return
    
    def toggleFeedbackLoop(self, on:bool):
        """
        Toggle between starting and stopping feedback loop

        Args:
            `on` (bool): whether to have loop to continuously read from device
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
        Toggle between starting and stopping temperature recording

        Args:
            `on` (bool): whether to start recording temperature
        """
        self.setFlag('record', on)
        self.setFlag('get_feedback', on)
        self.setFlag('pause_feedback', False)
        self.toggleFeedbackLoop(on=on)
        return
