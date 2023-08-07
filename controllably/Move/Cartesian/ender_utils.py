# %% -*- coding: utf-8 -*-
"""
This module holds the class for movement tools based on Creality's Ender-3. (Marlin firmware)

Classes:
    Ender (Gantry)
"""
# Standard library imports
from __future__ import annotations
import time
from typing import Union

# Local application imports
from ...misc import Helper
from .cartesian_utils import Gantry
print(f"Import: OK <{__name__}>")

class Ender(Gantry):
    """
    Ender provides controls for the Creality Ender-3 platform

    ### Constructor
    Args:
        `port` (str): COM port address
        `limits` (tuple[tuple[float]], optional): lower and upper limits of gantry. Defaults to ((0,0,0), (240,235,210)).
        `safe_height` (float, optional): height at which obstacles can be avoided. Defaults to 30.
        `max_speed` (float, optional): maximum travel speed. Defaults to 180.
    
    ### Attributes
    - `temperature_range` (tuple): range of temperature that can be set for the platform bed
    
    ### Methods
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
        max_speed: float = 180, # [mm/s] (i.e. 10,800 mm/min)
        **kwargs
    ):
        """
        Instantiate the class

        Args:
            port (str): COM port address
            limits (tuple[tuple[float]], optional): lower and upper limits of gantry. Defaults to ((0,0,0), (240,235,210)).
            safe_height (float, optional): height at which obstacles can be avoided. Defaults to 30.
            max_speed (float, optional): maximum travel speed. Defaults to 180.
        """
        super().__init__(port=port, limits=limits, safe_height=safe_height, max_speed=max_speed, **kwargs)
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
        relevant = [s for s in settings if 'M201' in s][-1]
        accels = relevant.split('M201 ')[1].split(' ')
        xyz_max_accels = [float(s[1:]) for s in accels[:3]]
        return np.array(xyz_max_accels)
    
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
        # if len(position) == 0:
        #     return np.array([np.nan]*3)
        xyz_coordinates = relevant[-1].split("E")[0].split(" ")[:-1]
        x,y,z = [float(c[2:]) for c in xyz_coordinates]
        return np.array([x,y,z])
    
    def getMaxSpeed(self) -> np.ndarray:
        """
        Get maximum speeds (mm/s)

        Returns:
            np.ndarray: maximum speeds
        """
        settings = self.getSettings()
        relevant = [s for s in settings if 'M203' in s][-1]
        speeds = relevant.split('M203 ')[1].split(' ')
        xyz_max_speeds = [float(s[1:]) for s in speeds[:3]]
        self._speed_max = {k:v for k,v in zip(('x','y','z'), xyz_max_speeds)}
        return self.max_speed
    
    def getSettings(self) -> list[str] :
        """
        Get hardware settings

        Returns:
            list[str]: hardware settings
        """
        responses = self._query('M503\n')
        print(responses)
        return responses
    
    def getTemperature(self) -> Union[tuple, str]:
    def getTemperature(self) -> tuple[float]:
        """
        Retrieve set temperature and actual temperature from device
        
        Returns:
            tuple[float]: set temperature, current temperature
        """
        responses = self._query('M105')  # Use 'M155 S<seconds>' to auto-report temperatures in S-second intervals. S0 to disable.
        temperatures = [r for r in responses if '@' in r]
        bed_temperatures = temperatures[-1].split(':')[2].split(' ')[:2]
        temperature, set_temperature = bed_temperatures
        self.temperature = float(temperature)
        self.set_temperature = float(set_temperature[1:])
        
        ready = (abs(self.set_temperature - self.temperature)<=self.tolerance)
        self.setFlag(temperature_reached=ready)
        return self.set_temperature, self.temperature
    
    def holdTemperature(self, temperature:float, time_s:float):
        """
        Hold target temperature for desired duration

        Args:
            temperature (float): temperature in degree Celsius
            time_s (float): duration in seconds
        """
        self.setTemperature(temperature)
        print(f"Holding at {self.set_temperature}°C for {time_s} seconds")
        time.sleep(time_s)
        print(f"End of temperature hold")
        return

    @Helper.safety_measures
    def home(self) -> bool:
        """Make the robot go home"""
        self._query("G90\n")
        self._query(f"G0 Z{self.heights['safe']}\n")
        self._query("G90\n")
        self._query("G28\n")

        self._query("G90\n")
        self._query(f"G0 Z{self.heights['safe']}\n")
        self._query("G90\n")
        self._query("G1 F10800\n")
        
        self.coordinates = self.home_coordinates
        print("Homed")
        return True
    
    def isAtTemperature(self) -> bool:
        """
        Checks and returns whether target temperature has been reached

        Returns:
            bool: whether target temperature has been reached
        """
        return self.flags['temperature_reached']

    def setSpeed(self, speed: int, axis:str = 'x') -> tuple[bool, float]:
        """
        Set the speed of the robot

        Args:
            speed (int): speed in mm/s
            axis (str, optional): axis speed to be changed. Defaults to 'x'.
        
        Returns:
            tuple[bool, float]: whether speed has changed; prevailing speed
        """
        print(f'Speed: {speed} mm/s')
        speed_fraction = (speed/self._speed_max[axis])
        return self.setSpeedFraction(speed_fraction)
    
    def setSpeedFraction(self, speed_fraction: float) -> tuple[bool, float]:
        """
        Set the speed fraction of the robot

        Args:
            speed_fraction (float): speed fraction between 0 and 1
        
        Returns:
            tuple[bool, float]: whether speed has changed; prevailing speed fraction
        """
        print(f'Speed fraction: {speed_fraction}')
        prevailing_speed_fraction = self._speed_fraction
        self._speed_fraction = speed_fraction
        self._query(f"M220 S{int(speed_fraction*100)}")
        return True, self.max_speed*prevailing_speed_fraction
    
    def setTemperature(self, set_temperature: float, blocking:bool = True):
        """
        Set the temperature of the 3-D printer platform bed

        Args:
            set_temperature (float): set point for platform temperature
            blocking (bool, optional): whether to wait for temperature to reach set point. Defaults to True.
        """
        if set_temperature < self.temperature_range[0] or set_temperature > self.temperature_range[1]:
            print(f'Please select a temperature between {self.temperature_range[0]} and {self.temperature_range[1]}°C.')
            return False
        set_temperature = round( min(max(set_temperature,0), 110) )
        command = f'M190 R{set_temperature}\n' if blocking else f'M140 S{set_temperature}\n'
        
        print(f"New set temperature at {set_temperature}°C")
        if blocking:
            print(f"Waiting for temperature to reach {set_temperature}°C")
        try:
            self._query(command)
        except Exception as e:
            print('Unable to heat stage!')
            if self.verbose:
                print(e)
            return
        else:
            self.getTemperature()
        self.setFlag(temperature_reached=blocking)
        return

    def stop(self):
        """Halt all movement and print current coordinates"""
        self._query("M410")
        time.sleep(1)
        self.coordinates = self.getCoordinates()
        print(self.coordinates)
        return
