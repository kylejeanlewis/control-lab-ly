# %% -*- coding: utf-8 -*-
"""
This module holds the class for Peltier devices.

Classes:
    Peltier (Maker)

Other constants and variables:
    COLUMNS (tuple)
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
"""Headers for output data from Peltier device"""

class Peltier(Maker):
    """
    A Peltier device generates heat to provide local temperature control of the sample

    ### Constructor
    Args:
        `port` (str): COM port of device
        `power_threshold` (float, optional): minimum threshold under which temperature can be considered stable. Defaults to 20.
        `stabilize_buffer_time` (float, optional): buffer time over which temperature can be considered stable. Defaults to 10.
        `tolerance` (float, optional): tolerance above and below target temperature. Defaults to 1.5.
            
    ### Attributes
    - `power_threshold` (float): minimum threshold under which temperature can be considered stable
    - `set_point` (float): temperature set point
    - `stabilize_buffer_time` (float): buffer time over which temperature can be considered stable
    - `temperature` (float): temperature at sample site
    - `tolerance` (float): tolerance above and below target temperature
    
    ### Properties
    - `port`: COM port of device
    
    ### Methods
    - `clearCache`: clears and remove data in buffer
    - `getTemperatures`: retrieve temperatures from device
    - `holdTemperature`: hold target temperature for desired duration
    - `isReady`: checks and returns whether target temperature has been reached
    - `reset`: reset the device
    - `setTemperature`: set a target temperature
    - `shutdown`: shutdown procedure for tool
    - `toggleFeedbackLoop`: start or stop feedback loop
    - `toggleRecord`: start or stop data recording
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
        power_threshold: float = 20,
        stabilize_buffer_time: float = 10, 
        tolerance: float = 1.5, 
        **kwargs
    ):
        """
        Instantiate the class

        Args:
            port (str): COM port of device
            power_threshold (float, optional): minimum threshold under which temperature can be considered stable. Defaults to 20.
            stabilize_buffer_time (float, optional): buffer time over which temperature can be considered stable. Defaults to 10.
            tolerance (float, optional): tolerance above and below target temperature. Defaults to 1.5.
        """
        super().__init__(**kwargs)
        self.buffer_df = pd.DataFrame(columns=list(COLUMNS))
        self.power_threshold = power_threshold
        self.stabilize_buffer_time = stabilize_buffer_time
        self.tolerance = tolerance
        
        self._columns = list(COLUMNS)
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
        """Clears and remove data in buffer"""
        self.setFlag(pause_feedback=True)
        time.sleep(0.1)
        self.buffer_df = pd.DataFrame(columns=self._columns)
        self.setFlag(pause_feedback=False)
        return
    
    def getTemperatures(self) -> str:
        """
        Retrieve temperatures from device 
        Including the set temperature, hot temperature, cold temperature, and the power level
        
        Returns:
            str: response from device
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
        Hold target temperature for desired duration

        Args:
            temperature (float): temperature in degree Celsius
            time_s (float): duration in seconds
        """
        self.setTemperature(temperature)
        print(f"Holding at {self.set_point}°C for {time_s} seconds")
        time.sleep(time_s)
        print(f"End of temperature hold")
        return
    
    def isReady(self) -> bool:
        """
        Checks and returns whether target temperature has been reached

        Returns:
            bool: whether target temperature has been reached
        """
        return self.flags['temperature_reached']
    
    def reset(self):
        """Reset the device"""
        self.toggleRecord(False)
        self.clearCache()
        self.setTemperature(set_point=25, blocking=False)
        return
    
    def setTemperature(self, set_point:int, blocking:bool = True):
        """
        Set a temperature

        Args:
            set_point (int): target temperature in degree Celsius
            blocking (bool, optional): whether to wait for temperature to reach set point. Defaults to True.
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
        if blocking:
            print(f"Waiting for temperature to reach {self.set_point}°C")
        while not self.isReady():
            if not self.flags['get_feedback']:
                self.getTemperatures()
            time.sleep(0.1)
            if not blocking:
                break
        return
    
    def shutdown(self):
        """Shutdown procedure for tool"""
        for thread in self._threads.values():
            thread.join()
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
            print(self.getTemperatures())
        self.device = device
        return
    
    def _loop_feedback(self):
        """Loop to constantly read from device"""
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
    