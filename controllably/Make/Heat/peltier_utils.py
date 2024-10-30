# -*- coding: utf-8 -*-
"""
This module holds the class for Peltier devices.

Classes:
    Peltier (Maker)

Other constants and variables:
    COLUMNS (tuple)
"""
# Standard library imports
from __future__ import annotations
from collections import namedtuple
from datetime import datetime
import logging
from threading import Thread
import time
from types import SimpleNamespace

# Third party imports
import numpy as np
import pandas as pd

# Local application imports
from .. import Maker

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.debug(f"Import: OK <{__name__}>")

# COLUMNS = ('Time', 'Set', 'Hot', 'Cold', 'Power')
# """Headers for output data from Peltier device"""
FLAGS = SimpleNamespace(
    busy=False, get_feedback=False, pause_feedback=False, 
    record=False, verbose=False
)
"""Default flags for Peltier"""
Data = namedtuple('Data', 'time, target, hot, cold, power', defaults=[time.time()]+[np.nan]*4)

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
    - `buffer_df` (pd.DataFrame): buffer dataframe to store collected data
    - `power_threshold` (float): minimum threshold under which temperature can be considered stable
    - `set_temperature` (float): temperature set point
    - `stabilize_buffer_time` (float): buffer time over which temperature can be considered stable
    - `temperature` (float): temperature at sample site
    - `tolerance` (float): tolerance above and below target temperature
    
    ### Properties
    - `port`: COM port of device
    
    ### Methods
    - `clearCache`: clears and remove data in buffer
    - `execute`: alias for `holdTemperature()`
    - `getTemperature`: retrieve temperatures from device
    - `holdTemperature`: hold target temperature for desired duration
    - `isAtTemperature`: checks and returns whether target temperature has been reached
    - `reset`: reset the device
    - `setTemperature`: set a target temperature
    - `shutdown`: shutdown procedure for tool
    - `toggleFeedbackLoop`: start or stop feedback loop
    - `toggleRecord`: start or stop data recording
    """
    
    _default_flags = FLAGS
    def __init__(self, 
        port: str, 
        power_threshold: float = 20,
        stabilize_buffer_time: float = 10, 
        tolerance: float = 1.5, 
        *,
        baudrate: int = 115200,
        verbose: bool = False,
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
        super().__init__(port=port, baudrate=baudrate, verbose=verbose, **kwargs)
        self.buffer_df = pd.DataFrame()
        self.data = Data()
        
        self.power_threshold = power_threshold
        self.stabilize_buffer_time = stabilize_buffer_time
        self.tolerance = tolerance
        self._stabilize_start_time = None
        self._threads = {}
        
        self.connect()
        return
    
    # Properties
    @property
    def at_temperature(self) -> bool:
        """
        Checks and returns whether target temperature has been reached

        Returns:
            bool: whether target temperature has been reached
        """
        self.getTemperature()
        if self._stabilize_start_time is None:
            self._stabilize_start_time = time.perf_counter()
        temperature_reached = (abs(self.data.target-self.data.hot)<=self.tolerance)
        power_stable = (self.data.power <= self.power_threshold)
        time_exceeded = (time.perf_counter()-self._stabilize_start_time >= self.stabilize_buffer_time)
        return any([temperature_reached, power_stable, time_exceeded])
    
    @property
    def port(self) -> str:
        return self.device.connection_details.get('port', '')
    
    def getTemperature(self) -> tuple[float]:
        """
        Retrieve temperatures from device 
        Including the set temperature, hot temperature, cold temperature, and the power level
        
        Returns:
            tuple[float]: set temperature, current temperature
        """
        response = self.device.read()
        now = datetime.now()
        try:
            values = [float(v) for v in response.split(';')]
            self.data = Data(now, *values)
            logger.info(values)
        except ValueError:
            logger.error(f"Could not parse response: {response}")
        
        if self.flags.record:
            new_row_df = pd.DataFrame(self.data, index=[0])
            dfs = [df for df in [self.buffer_df, new_row_df] if len(df)]
            self.buffer_df = pd.concat(dfs, ignore_index=True)
        return self.data.hot
    
    def holdTemperature(self, temperature:float, time_s:float):
        """
        Hold target temperature for desired duration

        Args:
            temperature (float): temperature in degree Celsius
            time_s (float): duration in seconds
        """
        self.setTemperature(temperature)
        out = f"Holding at {self.set_temperature}°C for {time_s} seconds"
        logger.info(out)
        print(out)
        time.sleep(time_s)
        out = f"End of temperature hold"
        logger.info(out)
        print(out)
        return
    
    def setTemperature(self, temperature:int, blocking:bool = True):
        """
        Set a temperature

        Args:
            temperature (int): target temperature in degree Celsius
            blocking (bool, optional): whether to wait for temperature to reach set point. Defaults to True.
        """
        self.flags.pause_feedback = True
        time.sleep(0.5)
        self.device.query(temperature)
        if not self.is_connected:
            return
        while self.data.target != float(temperature):
            self.getTemperature()
        out = f"New set temperature at {self.data.target}°C"
        logger.info(out)
        print(out)
        
        self._stabilize_start_time = None
        self.flags.pause_feedback = False
        if not self.flags.get_feedback:
            self.getTemperature()
        if blocking:
            out = f"Waiting for temperature to reach {self.data.target}°C"
            logger.info(out)
            print(out)
            while not self.at_temperature:
                if not self.flags.get_feedback:
                    self.getTemperature()
                time.sleep(0.1)
            out = f"Temperature of {self.data.target}°C reached!"
            logger.info(out)
            print(out)
        return
    
    def clearCache(self):
        """Clears and remove data in buffer"""
        self.flags.pause_feedback = True
        time.sleep(0.1)
        self.buffer_df = pd.DataFrame(columns=self._columns)
        self.flags.pause_feedback = False
        return
    
    def reset(self):
        """Reset the device"""
        self.toggleRecord(False)
        self.clearCache()
        self.setTemperature(temperature=25, blocking=False)
        return
    
    def toggleFeedbackLoop(self, on:bool):
        """
        Start or stop feedback loop

        Args:
            on (bool): whether to start loop to continuously read from device
        """
        self.flags.get_feedback = on
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
        self.flags.record = on
        self.flags.get_feedback = on
        self.flags.pause_feedback = False
        self.toggleFeedbackLoop(on=on)
        return

    # Overridden methods
    def connect(self):
        self.device.connect()
        self.getTemperature()
        logger.info(self.data.hot)
        print(self.data.hot)
        return
    
    def execute(self, temperature:float, time_s:float, *args, **kwargs):
        """
        Alias for `holdTemperature()`
        
        Hold target temperature for desired duration

        Args:
            temperature (float): temperature in degree Celsius
            time_s (float): duration in seconds
        """
        return self.holdTemperature(temperature=temperature, time_s=time_s)
    
    def shutdown(self):
        """Shutdown procedure for tool"""
        for thread in self._threads.values():
            thread.join()
        self.disconnect()
        self.resetFlags()
        return
    
    # Protected method(s)
    def _loop_feedback(self):
        """Loop to constantly read from device"""
        print('Listening...')
        while self.flags['get_feedback']:
            if self.flags['pause_feedback']:
                continue
            self.getTemperature()
            time.sleep(0.1)
        print('Stop listening...')
        return

    # Deprecated methods
    def isAtTemperature(self) -> bool:
        """
        Checks and returns whether target temperature has been reached

        Returns:
            bool: whether target temperature has been reached
        """
        logger.warning("This method is deprecated. Use `at_temperature` instead.")
        return self.at_temperature
    