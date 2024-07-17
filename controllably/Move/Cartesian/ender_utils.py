# %% -*- coding: utf-8 -*-
"""
This module holds the class for movement tools based on Creality's Ender-3. (Marlin firmware)

Classes:
    Ender (Marlin)
    Marlin (Gantry)
"""
# Standard library imports
from __future__ import annotations
import logging
import numpy as np
import time

# Local application imports
from ...misc import Helper
from .cartesian_utils import Gantry

logger = logging.getLogger(__name__)
logger.debug(f"Import: OK <{__name__}>")

class Marlin(Gantry):
    """
    Marlin provides controls for the platforms using the Marlin firmware

    ### Constructor
    Args:
        `port` (str): COM port address
        `limits` (tuple[tuple[float]], optional): lower and upper limits of gantry. Defaults to ((0,0,0), (240,235,210)).
        `safe_height` (float, optional): height at which obstacles can be avoided. Defaults to 30.
    
    ### Attributes
    - `temperature_range` (tuple): range of temperature that can be set for the platform bed
    
    ### Methods
    - `getAcceleration`: get maximum acceleration rates (mm/s^2)
    - `getCoordinates`: get current coordinates from device
    - `getMaxSpeeds`:  get maximum speeds (mm/s)
    - `getSettings`: get hardware settings
    - `holdTemperature`: hold target temperature for desired duration
    - `home`: make the robot go home
    - `isAtTemperature`: checks and returns whether target temperature has been reached
    - `setTemperature`: set the temperature of the 3-D printer platform bed
    """
    
    _default_flags: dict[str, bool] = {
        'busy': False, 
        'connected': False, 
        'temperature_reached': False
    }
    temperature_range = (0,110)
    def __init__(self, 
        port: str, 
        limits: tuple[tuple[float]] = ((0,0,0), (240,235,210)), 
        safe_height: float = 30,
        **kwargs
    ):
        """
        Instantiate the class

        Args:
            port (str): COM port address
            limits (tuple[tuple[float]], optional): lower and upper limits of gantry. Defaults to ((0,0,0), (240,235,210)).
            safe_height (float, optional): height at which obstacles can be avoided. Defaults to 30.
        """
        super().__init__(port=port, limits=limits, safe_height=safe_height, **kwargs)
        self.home_coordinates = (0,0,self.heights['safe'])
        self.set_temperature = None
        self.temperature = None
        self.tolerance = 1.5
        return
    
    def getAcceleration(self) -> np.ndarray:
        """
        Get maximum acceleration rates (mm/s^2)

        Returns:
            np.ndarray: acceleration rates
        """
        settings = self.getSettings()
        if len(settings) == 0:
            return self.max_accels
        relevant = [s for s in settings if 'M201' in s]
        if len(relevant) == 0:
            time.sleep(5)
            settings = self.getSettings()
            relevant = [s for s in settings if 'M201' in s]
        if len(relevant) == 0:
            logger.warning('Unable to get maximum accelerations.')
            return self.max_accels
        accels_str_list = relevant[-1].split('M201 ')[1].split(' ')
        xyz_max_accels = [(a[0].lower(), float(a[1:])) for a in accels_str_list[:3]]
        self._accel_max = {k:v for k,v in xyz_max_accels}
        return self.max_accels
    
    def getCoordinates(self) -> np.ndarray:
        """
        Get current coordinates from device

        Returns:
            np.ndarray: current device coordinates
        """
        relevant = []
        while len(relevant) == 0:
            responses = self._query('M114')  # Use 'M154 S<seconds>' to auto-report temperatures in S-second intervals. S0 to disable.
            relevant = [r for r in responses if 'Count' in r]
            if not self.isConnected():
                return self.coordinates
        xyz_coordinates = relevant[-1].split("E")[0].split(" ")[:-1]
        x,y,z = [float(c[2:]) for c in xyz_coordinates]
        return np.array([x,y,z])
    
    def getMaxSpeeds(self) -> np.ndarray:
        """
        Get maximum speeds (mm/s)

        Returns:
            np.ndarray: maximum speeds
        """
        settings = self.getSettings()
        if len(settings) == 0:
            return self.max_speeds
        relevant = [s for s in settings if 'M203' in s]
        if len(relevant) == 0:
            time.sleep(5)
            settings = self.getSettings()
            relevant = [s for s in settings if 'M203' in s]
        if len(relevant) == 0:
            logger.warning('Unable to get maximum speeds.')
            return self.max_speeds
        speeds_str_list = relevant[-1].split('M203 ')[1].split(' ')
        xyz_max_speeds = [(s[0].lower(), float(s[1:])) for s in speeds_str_list[:3]]
        self._speed_max = {k:v for k,v in xyz_max_speeds}
        super().getMaxSpeeds()
        return self.max_speeds
    
    def getSettings(self) -> list[str] :
        """
        Get hardware settings

        Returns:
            list[str]: hardware settings
        """
        responses = self._query('M503\n')
        logger.info(responses)
        return responses
    
    def getStatus(self):
        ...
    
    def getTemperature(self) -> tuple[float]:
        """
        Retrieve set temperature and actual temperature from device
        
        Returns:
            tuple[float]: set temperature, current temperature
        """
        responses = self._query('M105')  # Use 'M155 S<seconds>' to auto-report temperatures in S-second intervals. S0 to disable.
        try:
            temperatures = [r for r in responses if '@' in r]
        except Exception as e:
            raise e
        else:
            bed_temperatures = temperatures[-1].split(':')[2].split(' ')[:2]
            temperature, set_temperature = bed_temperatures
            self.temperature = float(temperature)
            self.set_temperature = float(set_temperature[1:])
        
            ready = (abs(self.set_temperature - self.temperature)<=self.tolerance)
            self.setFlag(temperature_reached=ready)
            if ready:
                logger.info(bed_temperatures)
                logger.info(f"Temperature of {self.set_temperature}°C reached!")
        return self.set_temperature, self.temperature
    
    def holdTemperature(self, temperature:float, time_s:float):
        """
        Hold target temperature for desired duration

        Args:
            temperature (float): temperature in degree Celsius
            time_s (float): duration in seconds
        """
        self.setTemperature(temperature)
        logger.info(f"Holding at {self.set_temperature}°C for {time_s} seconds")
        time.sleep(time_s)
        logger.info(f"End of temperature hold")
        return

    @Helper.safety_measures
    def home(self) -> bool:
        """Make the robot go home"""
        self._query("G91")
        self._query(f"G0 Z{self.heights['safe']}")
        move_time = self._calculate_travel_time(
            self.heights['safe'], self.max_speeds[2]*self.speed_factor, 
            self.max_accels[2], self.max_accels[2]
        )
        logger.info(f'Move for {move_time}s...')
        time.sleep(move_time)
        
        # Homing cycle
        self._query("G90")
        # self._query("G28")
        self._write('G28')
        while True:
            responses = self._read()
            if not self.isConnected():
                break
            if len(responses) and responses[-1] != b'echo:busy: processing\n':
                break
        
        # Lift to safe height
        self._query("G90")
        self._query(f"G0 Z{self.heights['safe']}")
        logger.info(f'Move for {move_time}s...')
        time.sleep(move_time)
        
        self.coordinates = self.home_coordinates
        logger.info("Homed")
        return True
    
    def isAtTemperature(self) -> bool:
        """
        Checks and returns whether target temperature has been reached

        Returns:
            bool: whether target temperature has been reached
        """
        return self.flags['temperature_reached']
    
    def setTemperature(self, temperature: float, blocking:bool = True):
        """
        Set the temperature of the 3-D printer platform bed

        Args:
            temperature (float): set point for platform temperature
            blocking (bool, optional): whether to wait for temperature to reach set point. Defaults to True.
        """
        if temperature < self.temperature_range[0] or temperature > self.temperature_range[1]:
            logger.warning(f'Please select a temperature between {self.temperature_range[0]} and {self.temperature_range[1]}°C.')
            return False
        temperature = round( min(max(temperature,0), 110) )
        command = f'M190 S{temperature}\n'
        try:
            self._query(command)
        except Exception as e:
            logger.warning('Unable to heat stage!')
            logger.exception(e, exc_info=self.verbose)
            return
        else:
            while self.set_temperature != float(temperature):
                self.getTemperature()
        logger.info(f"New set temperature at {temperature}°C")
        
        if blocking:
            logger.info(f"Waiting for temperature to reach {self.set_temperature}°C")
        while not self.isAtTemperature():
            self.getTemperature()
            time.sleep(0.1)
            if not blocking:
                break
        self.setFlag(temperature_reached=blocking)
        return

    def stop(self):
        """Halt all movement and print current coordinates"""
        self._query("M410")
        time.sleep(1)
        self.coordinates = self.getCoordinates()
        logger.info(self.coordinates)
        return
    
    # Protected methods
    def _query(self, command:str) -> list[str]:
        """
        Write command to and read response from device

        Args:
            command (str): command string to send to device

        Returns:
            list[str]: list of response string(s) from device
        """
        command = command.replace('G1', 'G0')
        if command.startswith('F'):
            command = f'G0 {command}'
        return super()._query(command)


class Ender(Marlin):
    """
    Ender provides controls for the Creality Ender-3 platform

    ### Constructor
    Args:
        `port` (str): COM port address
        `limits` (tuple[tuple[float]], optional): lower and upper limits of gantry. Defaults to ((0,0,0), (240,235,210)).
        `safe_height` (float, optional): height at which obstacles can be avoided. Defaults to 30.
    
    ### Attributes
    - `temperature_range` (tuple): range of temperature that can be set for the platform bed
    
    ### Methods
    - `getSettings`: get hardware settings
    - `holdTemperature`: hold target temperature for desired duration
    - `home`: make the robot go home
    - `isAtTemperature`: checks and returns whether target temperature has been reached
    - `setTemperature`: set the temperature of the 3-D printer platform bed
    """
    
    def __init__(self, 
        port: str, 
        limits: tuple[tuple[float]] = ((0, 0, 0), (240, 235, 210)), 
        safe_height: float = 30,
        **kwargs
    ):
        super().__init__(port, limits, safe_height, **kwargs)
        