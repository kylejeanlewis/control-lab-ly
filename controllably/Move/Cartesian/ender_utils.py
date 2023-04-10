# %% -*- coding: utf-8 -*-
"""

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
    - `setTemperature`: set the temperature of the 3-D printer platform bed
    - `home`: make the robot go home
    """
    
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

    def setTemperature(self, set_point: float) -> bool:
        """
        Set the temperature of the 3-D printer platform bed

        Args:
            set_point (float): set point for platform temperature

        Returns:
            bool: whether setting bed temperature was successful
        """
        if set_point < self.temperature_range[0] or set_point > self.temperature_range[1]:
            print(f'Please select a temperature between {self.temperature_range[0]} and {self.temperature_range[1]}°C.')
            return False
        set_point = round( min(max(set_point,0), 110) )
        try:
            print(f"New set temperature at {set_point}°C")
            self.device.write(bytes(f'M140 S{set_point}\n', 'utf-8'))
        except Exception as e:
            print('Unable to heat stage!')
            if self.verbose:
                print(e)
            return False
        return True
