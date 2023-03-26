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
import serial   # pip install pyserial

# Local application imports
from ..make_utils import Maker
print(f"Import: OK <{__name__}>")

COLUMNS = ('Time', 'Set', 'Hot', 'Cold', 'Power')

class Peltier(Maker):
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
    
    _default_flags = {
        'busy': False,
        'connected': False,
        'get_feedback': False,
        'pause_feedback': False,
        'record': False,
        'temperature_reached': False
    }
    
    def __init__(self, 
        port: str, 
        columns: list = COLUMNS,
        power_threshold: float = 20,
        stabilize_buffer_time: float = 10, 
        tolerance: float = 1.5, 
        **kwargs
    ):
        """
        Construct the Peltier object

        Args:
            `port` (str): com port address
            `tolerance` (float, optional): temperature tolerance to determine if device has reached target temperature. Defaults to `TEMPERATURE_TOLERANCE` (i.e. 1.5).
        """
        super().__init__(**kwargs)
        self.buffer_df = pd.DataFrame(columns=list(columns))
        self.power_threshold = power_threshold
        self.stabilize_buffer_time = stabilize_buffer_time
        self.tolerance = tolerance
        
        self._columns = list(columns)
        self._stabilize_time = None
        self._threads = {}
        
        # Device read-outs
        self.set_point = None
        self.temperature = None
        self._cold_point = None
        self._power = None
        self._connect(port)
        return
    
    # Properties
    @property
    def port(self) -> str:
        return self.connection_details.get('port', '')
    
    def clearCache(self):
        """
        Clear data from buffer
        """
        self.setFlag(pause_feedback=True)
        time.sleep(0.1)
        self.buffer_df = pd.DataFrame(columns=self._columns)
        self.setFlag(pause_feedback=False)
        return
    
    def getTemperatures(self) -> str:
        """
        Reads from the device the set temperature, hot temperature, cold temperature, and the power level
        
        Returns:
            `str`: response from device output
        """
        response = self._read()
        now = datetime.now()
        try:
            values = [float(v) for v in response.split(';')]
            self.set_point, self.temperature, self._cold_point, self._power = values
        except ValueError:
            pass
        else:
            ready = (abs(self.set_point - self.temperature)<=self.tolerance)
            if not ready:
                pass
            elif not self._stabilize_time:
                self._stabilize_time = time.time()
                print(response)
            elif self.flags['temperature_reached']:
                pass
            elif (self._power <= self.power_threshold) or (time.time()-self._stabilize_time >= self.stabilize_buffer_time):
                print(response)
                self.setFlag(temperature_reached=True)
                print(f"Temperature of {self.set_point}°C reached!")
            if self.flags['record']:
                values = [now] + values
                row = {k:v for k,v in zip(self._columns, values)}
                self.buffer_df = self.buffer_df.append(row, ignore_index=True)
        return response
    
    def holdTemperature(self, temperature:float, time_s:float):
        """
        Hold the device temperature at target temperature for specified duration

        Args:
            `temperature` (float): temperature in degree Celsius
            `time_s` (float): duration in seconds
        """
        self.setTemperature(temperature)
        print(f"Holding at {self.set_point}°C for {time_s} seconds")
        time.sleep(time_s)
        print(f"End of temperature hold")
        return
    
    def isReady(self) -> bool:
        """
        Check whether target temperature has been reached

        Returns:
            `bool`: whether target temperature has been reached
        """
        return self.flags['temperature_reached']
    
    def reset(self):
        """
        Clears data in buffer and set the temperature to room temperature (i.e. 25°C)
        """
        self.toggleRecord(False)
        self.clearCache()
        self.setTemperature(set_point=25, blocking=False)
        return
    
    def setTemperature(self, set_point:int, blocking:bool = True):
        """
        Set temperature of the device

        Args:
            `set_point` (int): target temperature in degree Celsius
        """
        self.setFlag(pause_feedback=True)
        time.sleep(0.5)
        try:
            self.device.write(bytes(f"{set_point}\n", 'utf-8'))
        except AttributeError:
            pass
        else:
            while self.set_point != float(set_point):
                self.getTemperatures()
        print(f"New set temperature at {set_point}°C")
        
        self._stabilize_time = None
        self.setFlag(temperature_reached=False, pause_feedback=False)
        print(f"Waiting for temperature to reach {self.set_point}°C")
        while not self.isReady():
            if not self.flags['get_feedback']:
                self.getTemperatures()
            time.sleep(0.1)
            if not blocking:
                break
        return
    
    def shutdown(self):
        """
        Close serial connection and shutdown feedback loop
        """
        for thread in self._threads.values():
            thread.join()
        return super().shutdown()

    def toggleFeedbackLoop(self, on:bool):
        """
        Toggle between starting and stopping feedback loop

        Args:
            `on` (bool): whether to have loop to continuously read from device
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
        Toggle between starting and stopping temperature recording

        Args:
            `on` (bool): whether to start recording temperature
        """
        self.setFlag(record=on, get_feedback=on, pause_feedback=False)
        self.toggleFeedbackLoop(on=on)
        return

    # Protected method(s)
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
            print(self.getTemperatures())
        self.device = device
        return
    
    def _loop_feedback(self):
        """
        Feedback loop to constantly read values from device
        """
        print('Listening...')
        while self.flags['get_feedback']:
            if self.flags['pause_feedback']:
                continue
            self.getTemperatures()
            time.sleep(0.1)
        print('Stop listening...')
        return

    def _read(self) -> str:
        """
        Read values from the device

        Returns:
            `str`: response string
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
    