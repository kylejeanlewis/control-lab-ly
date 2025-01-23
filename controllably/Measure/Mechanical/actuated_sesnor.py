# -*- coding: utf-8 -*-
# Standard library imports
from __future__ import annotations
from datetime import datetime
import logging
import time
from typing import NamedTuple, Iterable

# Third party imports
import pandas as pd

# Local application imports
from ...core import datalogger
from ..measure import Program
from .load_cell import LoadCell

logger = logging.getLogger(__name__)
logger.debug(f"Import: OK <{__name__}>")

MAX_SPEED = 0.375 # mm/s (22.5mm/min)
READ_FORMAT = "{displacement},{end_stop},{value}\n"
MoveForceData = NamedTuple('MoveForceData', [('displacement', float),('value', int),('end_stop', bool)])

class ActuatedSensor(LoadCell):
    
    def __init__(self,
        port: str,
        limits: Iterable[float] = (-30.0, 0),
        force_threshold: float = 10,
        stabilize_timeout: float = 1, 
        force_tolerance: float = 0.01, 
        *, 
        home_displacement: float = -1.0,
        max_speed: float = MAX_SPEED,
        steps_per_second: int = 6400,
        calibration_factor: float = 1.0,
        correction_parameters: tuple[float] = (1.0,0.0),
        baudrate: int = 9600,
        verbose: bool = False, 
        **kwargs
    ):
        super().__init__(
            port=port, baudrate=baudrate, init_timeout=3, 
            data_type=MoveForceData, read_format=READ_FORMAT, 
            stabilize_timeout=stabilize_timeout, force_tolerance=force_tolerance,
            calibration_factor=calibration_factor, correction_parameters=correction_parameters,
            verbose=verbose, **kwargs
        )
        
        self.force_threshold = force_threshold
        self.home_displacement = home_displacement
        self.limits = (min(limits), max(limits))
        self.max_speed = max_speed
        self._steps_per_second = steps_per_second
        
        self.program = ForceDisplacement
        return
    
    def connect(self):
        super().connect()
        self.home()
        self.zero()
        return 
    
    def getData(self, *args, **kwargs) -> MoveForceData|None:
        """
        Get data from device
        """
        return super().getData(*args, **kwargs)
    
    def getDataframe(self, data_store: Iterable[NamedTuple, datetime]) -> pd.DataFrame:
        df = datalogger.get_dataframe(data_store=data_store, fields=self.device.data_type._fields)
        df.drop(columns=['end_stop'], inplace=True)
        return df
    
    def atDisplacement(self, displacement: float) -> bool:
        """
        Check if the device is at the target displacement
        """
        data = self.getDisplacement()
        if data is None:
            return False
        return data == displacement
    
    def getDisplacement(self) -> float|None:
        """
        Get displacement
        """
        data = self.getData()
        if data is None:
            return None
        return data.displacement
    
    def zero(self, wait: float = 5.0):
        """
        Set current reading as baseline
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
        """
        if not self.device.write('H 0\n'):
            return False
        time.sleep(1)
        while not self.atDisplacement(self.home_displacement):
            time.sleep(0.1)
        while not self.atDisplacement(self.home_displacement):
            time.sleep(0.1)
        self.device.disconnect()
        time.sleep(2)
        self.device.connect()
        time.sleep(2)
        if not self.device.write('H 0\n'):
            return False
        time.sleep(1)
        while not self.atDisplacement(self.home_displacement):
            time.sleep(0.1)
        return True
    
    def move(self, by: float, speed: float|None = None) -> bool:
        """
        Move the actuator to the target displacement and apply the target force
        """
        speed = speed or self.max_speed
        return self.moveBy(by, speed=speed)
    
    def moveBy(self, by: float, speed: float|None = None) -> bool:
        """
        Move the actuator by desired distance

        Args:
            distance (float): distance in mm
            speed (float, optional): movement speed. Defaults to 0.375.

        Returns:
            bool: whether movement is successful
        """
        speed = speed or self.max_speed
        new_displacement = self.getDisplacement() + by
        return self.moveTo(new_displacement, speed)
    
    def moveTo(self, to: float, speed: float|None = None) -> bool:
        """
        Move the actuator to desired displacement

        Args:
            displacement (float): displacement in mm
            speed (float, optional): movement speed. Defaults to 0.375.

        Returns:
            bool: whether movement is successful
        """
        assert self.limits[0] <= to <= self.limits[1], f"Target displacement out of range: {to}"
        speed = speed or self.max_speed
        to = round(to,2)
        rpm = int(speed * self._steps_per_second)
        self.device.write(f'G {to} {rpm}')
        
        success = True
        while not self.atDisplacement(to):
            data = self.getData()
            force = self._calculate_force(data.value)
            if force >= self.force_threshold:
                success = False 
                self._logger.info(f"[{data.displacement}] Force threshold reached: {force}")
                break
        self._logger.info(data.displacement)
        self.device.write(f'G {data.displacement} {rpm}')
        self.displacement = self.getDisplacement()
        return success
    
    def touch(self, 
        force_threshold: float = 0.1, 
        displacement_threshold: float|None = None, 
        speed: float|None = None, 
        from_top: bool = True
    ) -> bool:
        """
        Apply the target force
        """
        initial_force_threshold = self.force_threshold
        self.force_threshold = force_threshold
        to = self.limits[0] if from_top else self.limits[1]
        displacement_threshold = displacement_threshold or to
        success = self.moveTo(displacement_threshold, speed=speed)
        self.force_threshold = initial_force_threshold
        return not success
    

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
    ):
        """
        Run the program
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
