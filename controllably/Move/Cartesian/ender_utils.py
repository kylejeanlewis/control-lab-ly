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
    
    ### Methods
    - `heat`: heat the 3-D printer platform bed to temperature
    - `home`: make the robot go home
    """
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
        return

    def heat(self, bed_temperature: float) -> bool:
        """
        Heat the 3-D printer platform bed to temperature

        Args:
            bed_temperature (float): set point for platform temperature

        Returns:
            bool: whether setting bed temperature was successful
        """
        bed_temperature = round( min(max(bed_temperature,0), 110) )
        try:
            self.device.write(bytes(f'M140 S{bed_temperature}\n', 'utf-8'))
        except Exception as e:
            print('Unable to heat stage!')
            if self.verbose:
                print(e)
            return False
        return True

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
        self._query("G1 F10000\n")
        
        self.coordinates = self.home_coordinates
        print("Homed")
        return True
