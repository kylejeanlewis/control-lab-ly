# -*- coding: utf-8 -*-
""" 
This module provides a class for the actuated sensor.

Attributes:
    MAX_SPEED (float): Maximum speed
    READ_FORMAT (str): Format for reading data
    MoveForceData (NamedTuple): NamedTuple for move force data
    
## Classes:
    `ActuatedSensor`: Actuated sensor class
    `ForceDisplacement`: Stress-Strain program
    
<i>Documentation last updated: 2025-02-22</i>
"""
# Standard library imports
from __future__ import annotations
from datetime import datetime
import time
from typing import NamedTuple, Iterable, Callable

# Third party imports
import pandas as pd

# Local application imports
from ...core import datalogger
from ...core.compound import Ensemble
from ..measure import Program
from .load_cell import LoadCell

MAX_SPEED = 0.375 # mm/s (22.5mm/min)
READ_FORMAT = "{target},{speed},{displacement},{end_stop},{value}\n"
OUT_FORMAT = '{data}\r\n'
Data = NamedTuple('Data', [('data',str)])
MoveForceData = NamedTuple('MoveForceData', [('target', float),('speed', float),('displacement', float),('value', int),('end_stop', bool)])

class ActuatedSensor(LoadCell):
    """ 
    Actuated sensor class
    
    ### Constructor:
        `port` (str): Serial port
        `limits` (Iterable[float]): Lower and upper limits for the actuator
        `force_threshold` (float): Force threshold
        `stabilize_timeout` (float): Time to wait for the device to stabilize
        `force_tolerance` (float): Tolerance for
        `home_displacement` (float): Home position
        `max_speed` (float): Maximum speed
        `steps_per_second` (int): Steps per second
        `calibration_factor` (float): Calibration factor
        `correction_parameters` (tuple[float]): Polynomial correction parameters
        `baudrate` (int): Baudrate for serial communication
        `verbose` (bool): Print verbose output
        
    ### Attributes and properties:
        `force_threshold` (float): Force threshold
        `home_displacement` (float): Home position
        `limits` (Tuple[float]): Lower and upper limits for the actuator
        `max_speed` (float): Maximum speed
        `program` (Program): program to run
        `displacement` (float): current displacement
        `baseline` (int): Baseline value
        `buffer` (deque): data buffer for the device
        `buffer_df` (pd.DataFrame): data buffer as a DataFrame
        `records` (deque): records for the device
        `records_df` (pd.DataFrame): records as a DataFrame
        `record_event` (threading.Event): event for recording data
        `runs` (dict): dictionary of runs
        `n_runs` (int): number of runs
        `connection_details` (dict): connection details for the device
        `device` (Device): device object that communicates with physical tool
        `flags` (SimpleNamespace[str, bool]): flags for the class
        `is_busy` (bool): whether the device is busy
        `is_connected` (bool): whether the device is connected
        `verbose` (bool): verbosity of class
        
    ### Methods:
        `connect`: Connect to the device
        `getData`: Get data from device
        `getDataframe`: Get data as a DataFrame
        `atDisplacement`: Check if the device is at the target displacement
        `getDisplacement`: Get displacement
        `zero`: Set current reading as baseline
        `home`: Move the actuator to the home position
        `move`: Move the actuator to the target displacement and apply the target force
        `moveBy`: Move the actuator by desired distance
        `moveTo`: Move the actuator to desired displacement
        `touch`: Apply the target force
        `run`: Run the program
    """
    
    def __init__(self,
        port: str,
        limits: Iterable[float] = (-30.0, 0),
        force_threshold: float = 10000,
        stabilize_timeout: float = 1, 
        force_tolerance: float = 0.01, 
        *, 
        home_displacement: float = -1.0,
        max_speed: float = MAX_SPEED,
        steps_per_second: int = 6400,
        calibration_factor: float = 1.0,
        correction_parameters: tuple[float] = (1.0,0.0),
        baudrate: int = 115200,
        verbose: bool = False, 
        **kwargs
    ):
        """ 
        Initialize the actuated sensor
        
        Args:
            port (str): Serial port
            limits (Iterable[float]): Lower and upper limits for the actuator
            force_threshold (float): Force threshold
            stabilize_timeout (float): Time to wait for the device to stabilize
            force_tolerance (float): Tolerance for
            home_displacement (float): Home position
            max_speed (float): Maximum speed
            steps_per_second (int): Steps per second
            calibration_factor (float): Calibration factor
            correction_parameters (tuple[float]): Polynomial correction parameters
            baudrate (int): Baudrate for serial communication
            verbose (bool): Print verbose output
        """
        defaults = dict(
            init_timeout=3, 
            data_type=MoveForceData, 
            read_format=READ_FORMAT, 
        )
        defaults.update(kwargs)
        kwargs = defaults
        self.displacement = None
        self.force_threshold = force_threshold
        self.home_displacement = home_displacement
        self.limits = (min(limits), max(limits))
        self.max_speed = max_speed
        self._steps_per_second = steps_per_second
        super().__init__(
            port=port, baudrate=baudrate,
            stabilize_timeout=stabilize_timeout, force_tolerance=force_tolerance,
            calibration_factor=calibration_factor, correction_parameters=correction_parameters,
            verbose=verbose, final=False, **kwargs
        )
        self.program = ForceDisplacement
        if kwargs.get('final', True):
            self.connect()
        return
    
    def connect(self):
        super().connect()
        self.home()
        self.zero()
        return 
    
    def getData(self, *args, **kwargs) -> MoveForceData|None:
        """
        Get data from device
        
        Returns:
            MoveForceData: displacement, value, end_stop
        """
        return super().getData(*args, **kwargs)
    
    def getDataframe(self, data_store: Iterable[NamedTuple, datetime]) -> pd.DataFrame:
        df = datalogger.get_dataframe(data_store=data_store, fields=self.device.data_type._fields)
        df.drop(columns=['end_stop'], inplace=True)
        return df
    
    def atDisplacement(self, displacement: float, current_displacement: float|None = None) -> bool:
        """
        Check if the device is at the target displacement
        
        Args:
            displacement (float): Target displacement
            current_displacement (float|None): Current displacement. Defaults to None.
            
        Returns:
            bool: True if the device is at the target displacement
        """
        current_displacement = current_displacement or self.getDisplacement()
        if current_displacement is None:
            return False
        return current_displacement == displacement
    
    def getDisplacement(self) -> float|None:
        """
        Get displacement
        
        Returns:
            float: Displacement in mm
        """
        data = self.getData()
        if data is None:
            return None
        return data.displacement
    
    def zero(self, wait: float = 5.0):
        """
        Set current reading as baseline
        
        Args:
            wait (float, optional): Time to wait for the device to stabilize. Defaults to 5.0.
        """
        self.record_event.clear()
        self.buffer.clear()
        if not self.device.stream_event.is_set():
           self.device.startStream(buffer=self.buffer)
        while not len(self.buffer) == 100:
            time.sleep(0.1)
        time.sleep(wait)
        self.baseline = sum([d[0] for d,_ in self.buffer])/len(self.buffer)
        self.device.stopStream()
        self.buffer.clear()
        return

    # Actuation methods
    def home(self) -> bool:
        """
        Move the actuator to the home position
        
        Returns:
            bool: whether movement is successful
        """
        self.query('H 0')
        time.sleep(1)
        while not self.atDisplacement(self.home_displacement):
            time.sleep(0.1)
        while not self.atDisplacement(self.home_displacement):
            time.sleep(0.1)
        self.device.disconnect()
        time.sleep(2)
        self.device.connect()
        time.sleep(2)
        self.query('H 0')
        time.sleep(1)
        while not self.atDisplacement(self.home_displacement):
            time.sleep(0.1)
        self.displacement = self.home_displacement
        self.device.clearDeviceBuffer()
        return True
    
    def move(self, by: float, speed: float|None = None) -> bool:
        """
        Move the actuator to the target displacement and apply the target force
        
        Args:
            by (float): distance in mm
            speed (float, optional): movement speed. Defaults to 0.375.
            
        Returns:
            bool: whether movement is successful
        """
        speed = speed or self.max_speed
        return self.moveBy(by, speed=speed)
    
    def moveBy(self, by: float, speed: float|None = None) -> bool:
        """
        Move the actuator by desired distance

        Args:
            by (float): distance in mm
            speed (float, optional): movement speed. Defaults to 0.375.

        Returns:
            bool: whether movement is successful
        """
        speed = speed or self.max_speed
        new_displacement = self.displacement + by
        return self.moveTo(new_displacement, speed)
    
    def moveTo(self, to: float, speed: float|None = None) -> bool:
        """
        Move the actuator to desired displacement

        Args:
            to (float): displacement in mm
            speed (float, optional): movement speed. Defaults to 0.375.

        Returns:
            bool: whether movement is successful
        """
        assert self.limits[0] <= to <= self.limits[1], f"Target displacement out of range: {to}"
        speed = speed or self.max_speed
        to = round(to,2)
        rpm = int(speed * self._steps_per_second)
        self.query(f'G {to} {rpm}')
        
        success = True
        displacement = self.displacement
        while not self.atDisplacement(to, self.displacement):
            data = self.getData()
            if data is None:
                continue
            displacement = data.displacement
            self.displacement = displacement
            force = self._calculate_force(data.value)
            if force >= self.force_threshold:
                success = False 
                self._logger.info(f"[{displacement}] Force threshold reached: {force}")
                break
        self._logger.info(displacement)
        # self.device.write(f'G {displacement} {rpm}')
        if not success:
            time.sleep(0.1)
            # self.moveTo(displacement, speed)
            self.query(f'G {displacement} {rpm}')
            while not self.atDisplacement(displacement, self.displacement):
                time.sleep(0.1)
                data = self.getData()
                if data is None:
                    continue
                self.displacement = displacement
        self.displacement = self.getDisplacement()
        self.device.clearDeviceBuffer()
        return success
    
    def touch(self, 
        force_threshold: float = 0.1, 
        displacement_threshold: float|None = None, 
        speed: float|None = None, 
        from_top: bool = True
    ) -> bool:
        """
        Apply the target force
        
        Args:
            force_threshold (float): target force
            displacement_threshold (float): target displacement
            speed (float): movement speed
            from_top (bool): whether to move from the top or bottom
            
        Returns:
            bool: whether movement is successful (i.e. force threshold is not reached)
        """
        initial_force_threshold = self.force_threshold
        self.force_threshold = force_threshold
        to = min(self.limits) if from_top else max(self.limits)
        displacement_threshold = displacement_threshold or to
        success = self.moveTo(displacement_threshold, speed=speed)
        self.force_threshold = initial_force_threshold
        return not success
    
    def query(self, *args, **kwargs):
        if self.device.stream_event.is_set():
            data = args[0] if len(args) else kwargs.get('data', None)
            if data is None:
                return
            self.device.write(data)
            return 
        
        # self.device.clearDeviceBuffer()
        out:Data = self.device.query(*args, multi_out=False, format_out=OUT_FORMAT, data_type=Data, **kwargs)
        if out is None or len(out.data) == 0:
            return None
        if out.data[0] not in '-1234567890':
            return None
        return self.device.processOutput(out.data+'\n')
    
    def record(self, on: bool, show: bool = False, clear_cache: bool = False, *, callback: Callable|None = None, **kwargs):
        """
        Record data from the device
        
        Args:
            on (bool): whether to record data
            show (bool, optional): whether to show data. Defaults to False.
            clear_cache (bool, optional): whether to clear the cache. Defaults to False.
            callback (Callable|None, optional): callback function to process data. Defaults to None.
        """
        self.device.clearDeviceBuffer()
        return datalogger.record(
            on=on, show=show, clear_cache=clear_cache, data_store=self.records, 
            split_stream=False, device=self.device, event=self.record_event
        )
    
    def stream(self, on: bool, show: bool = False, *, callback: Callable|None = None, **kwargs):
        """
        Stream data from the device
        
        Args:
            on (bool): whether to stream data
            show (bool, optional): whether to show data. Defaults to False.
            callback (Callable|None, optional): callback function to process data. Defaults to None.
        """
        self.device.clearDeviceBuffer()
        return datalogger.stream(
            on=on, show=show, split_stream=False, data_store=self.buffer, device=self.device
        )
    
Parallel_ActuatedSensor = Ensemble.factory(ActuatedSensor)

class ForceDisplacement(Program):
    """
    Stress-Strain program
    """
    def __init__(self, instrument: ActuatedSensor|None = None, parameters: dict|None = None, verbose: bool = False):
        super().__init__(instrument=instrument, parameters=parameters, verbose=verbose)
        return
    
    def run(self,
        force_threshold: float = 10,
        displacement_threshold: float = -20,
        speed: float|None = None,
        stepped: bool = False,
        *,
        step_size: float = 0.1,
        step_interval: float = -5,
        pullback: float = 0,
        clear_cache: bool = True,
    ) -> pd.DataFrame:
        """
        Run the program
        
        Args:
            force_threshold (float): Force threshold
            displacement_threshold (float): Displacement threshold
            speed (float): Movement speed
            stepped (bool): Stepped movement
            step_size (float): Step size
            step_interval (float): Step interval
            pullback (float): Pullback distance
            clear_cache (bool): Clear data cache
            
        Returns:
            pd.DataFrame: Data as a DataFrame
        """
        assert isinstance(self.instrument, ActuatedSensor), "Ensure instrument is a (subclass of) StreamingDevice"
        self.instrument.device.stopStream()
        self.zero()
        if clear_cache:
            self.data.clear()
        self.instrument.device.startStream(buffer=self.data)
        if not stepped:
            self.instrument.touch(
                force_threshold=force_threshold, 
                displacement_threshold=displacement_threshold, 
                speed=speed
            )
        else:
            while not self.instrument.atDisplacement(displacement_threshold):
                self.instrument.moveBy(step_size, speed=speed)
                time.sleep(step_interval)
                data = self.instrument.getData()
                force = self._calculate_force(data.value)
                if force >= self.instrument.force_threshold:
                    self.instrument._logger.info(f"[{data.displacement}] Force threshold reached: {force}")
                    break
        self.instrument.device.stopStream()
        if pullback:
            self.instrument.moveBy(pullback, speed=speed)
        return self.data_df
