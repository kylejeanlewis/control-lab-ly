# %% -*- coding: utf-8 -*-
"""
This module holds the class for movement tools based on Creality's Ender-3.

Classes:
    Ender (Gantry)
"""
# Standard library imports
from __future__ import annotations

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
        return
    
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
        """
        Retrieve temperatures from device 
        Including the set temperature, hot temperature, cold temperature, and the power level
        
        Returns:
            Union[tuple, str]: response from device
        """
        # response = self._read()
        # now = datetime.now()
        # try:
        #     values = [float(v) for v in response.split(';')]
        #     self.set_temperature, self.temperature, self._cold_point, self._power = values
        # except ValueError:
        #     pass
        # else:
        #     response = tuple(values)
        #     ready = (abs(self.set_temperature - self.temperature)<=self.tolerance)
        #     if not ready:
        #         pass
        #     elif not self._stabilize_time:
        #         self._stabilize_time = time.perf_counter()
        #         print(response)
        #     elif self.flags['temperature_reached']:
        #         pass
        #     elif (self._power <= self.power_threshold) or (time.perf_counter()-self._stabilize_time >= self.stabilize_buffer_time):
        #         print(response)
        #         self.setFlag(temperature_reached=True)
        #         print(f"Temperature of {self.set_temperature}°C reached!")
        # return response
    
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

    def setTemperature(self, set_temperature: float):
        """
        Set the temperature of the 3-D printer platform bed

        Args:
            set_temperature (float): set point for platform temperature
        """
        if set_temperature < self.temperature_range[0] or set_temperature > self.temperature_range[1]:
            print(f'Please select a temperature between {self.temperature_range[0]} and {self.temperature_range[1]}°C.')
            return False
        set_temperature = round( min(max(set_temperature,0), 110) )
        try:
            self.device.write(bytes(f'M140 S{set_temperature}\n', 'utf-8'))
        except Exception as e:
            print('Unable to heat stage!')
            if self.verbose:
                print(e)
            return
        print(f"New set temperature at {set_temperature}°C")
        
        self._stabilize_time = None
        self.setFlag(temperature_reached=False)
        if blocking:
            print(f"Waiting for temperature to reach {self.set_temperature}°C")
        while not self.isAtTemperature():
            self.getTemperature()
            time.sleep(0.1)
            if not blocking:
                break
        return
