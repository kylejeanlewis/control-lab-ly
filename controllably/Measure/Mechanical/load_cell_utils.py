# %% -*- coding: utf-8 -*-
"""

"""
# Standard library imports
from __future__ import annotations
from datetime import datetime
import logging
import numpy as np
import pandas as pd
from threading import Thread
import time

# Third party imports
import serial # pip install pyserial

# Local application imports
from ..measure_utils import Measurer

logger = logging.getLogger(__name__)
logger.debug(f"Import: OK <{__name__}>")

COLUMNS = ('Time', 'Value')
"""Headers for output data from load cell"""

class LoadCell(Measurer):
    """
    LoadCell provides methods to handle and process the data generated from a load cell

    ### Constructor
    Args:
        `device` (object): device connection object
        `calibration_factor` (float, optional): calibration factor for readout values. Defaults to 1.0.
        `columns` (tuple[str], optional): columns for buffer dataframe. Defaults to COLUMNS.
        `verbose` (bool, optional): verbosity of class. Defaults to False.

    ### Attributes
    - `baseline` (float): baseline reading of load cell when unloaded
    - `calibration_factor` (float): calibration factor for readout values
    - `precision` (int): number of decimal places to display readouts
    
    ### Methods
    #### Public
    - `clearCache`: clear most recent data and configurations
    - `disconnect`: disconnect from device
    - `getValue`: get the value of the force response on the load cell
    - `loadDevice`: load the device connection object into class
    - `reset`: reset the device
    - `shutdown`: shutdown procedure for tool
    - `toggleFeedBackLoop`: start or stop feedback loop
    - `toggleRecord`: start or stop data recording
    - `zero`: set current reading as baseline
    """
    
    _default_flags = {
        'busy': False,
        'connected': False,
        'get_feedback': False,
        'pause_feedback': False,
        'read': True,
        'record': False
    }
    def __init__(self, 
        device:object, 
        calibration_factor:float = 1.0, 
        columns: tuple[str] = COLUMNS,
        verbose: bool = False, 
        **kwargs
    ):
        """
        Instantiate the class

        Args:
            device (object): device connection object
            calibration_factor (float, optional): calibration factor for readout values. Defaults to 1.0.
            columns (tuple[str], optional): columns for buffer dataframe. Defaults to COLUMNS.
            verbose (bool, optional): verbosity of class. Defaults to False.
        """
        super().__init__(verbose, **kwargs)
        self.baseline = 0
        self.buffer_df = pd.DataFrame(columns=columns)
        self.calibration_factor = calibration_factor
        self.precision = 3
        
        self._columns = columns
        self._threads = {}
    
        self.loadDevice(device=device)
        return
    
    def clearCache(self):
        """Clear most recent data and configurations"""
        self.setFlag(pause_feedback=True)
        time.sleep(0.1)
        self.buffer_df = pd.DataFrame(columns=self._columns)
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
    
    def getValue(self) -> float:
        """
        Get the value of the force response on the load cell
        
        Returns:
            float: float value
        """
        response = self._read()
        now = datetime.now()
        value = np.nan
        try:
            value = float(response)
        except ValueError:
            return np.nan
        else:
            if self.flags['record']:
                values = [
                    now, 
                    value
                ]
                row = {k:v for k,v in zip(self._columns, values)}
                new_row_df = pd.DataFrame(row, index=[0])
                dfs = [_df for _df in [self.buffer_df, new_row_df] if len(_df)]
                self.buffer_df = pd.concat(dfs, ignore_index=True)
        return value
    
    def loadDevice(self, device: object): # TODO: generalise procedure
        """
        Load the device connection object into class

        Args:
            device (object): device connection object
        """
        self.device = device
        connection_details = {}
        is_connected = False
        if type(device) is serial.Serial:
            is_connected = device.is_open
            connection_details = dict(
                port = device.port,
                baudrate = device.baudrate,
                timeout = device.timeout
            )
        elif 'KeithleyDevice' in str(type(device)):
            is_connected = device.isConnected()
            connection_details = dict(
                ip_address = device.ip_address,
                name = device.name
            )
            device.reset()
            device.sendCommands(['ROUTe:TERMinals FRONT'])
            device.configureSource('current', measure_limit=0.2)
            device.configureSense('voltage', limit=0.2, four_point=True, count=1)
            device.makeBuffer()
            device.beep()
            device.setSource(0)
            device.toggleOutput(True)
        self.connection_details = connection_details
        print(is_connected)
        self.setFlag(connected=is_connected)
        self.zero()
        return
    
    def reset(self):
        """Reset the device"""
        super().reset()
        self.baseline = 0
        return
    
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
            on (bool): whether to start recording data
        """
        self.setFlag(record=on, get_feedback=on, pause_feedback=False)
        self.toggleFeedbackLoop(on=on)
        return
    
    def zero(self, wait:int = 5):
        """
        Set current reading as baseline
        
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
    def _connect(self, *args, **kwargs):
        """Connection procedure for tool"""
        return super()._connect(*args, **kwargs)

    def _loop_feedback(self):
        """Loop to constantly read from device"""
        print('Listening...')
        while self.flags['get_feedback']:
            if self.flags['pause_feedback']:
                continue
            self.getValue()
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
            response = response.decode('utf-8','replace').strip().replace('\uFFFD', '')
            if self.verbose:
                print(response)
        return response
