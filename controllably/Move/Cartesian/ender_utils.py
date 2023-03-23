# %% -*- coding: utf-8 -*-
"""
Created: Tue 2022/11/01 17:13:35
@author: Chang Jie

Notes / actionables:
-
"""
# Standard library imports
from __future__ import annotations

# Local application imports
from ...misc import Helper
from .cartesian_utils import Gantry
print(f"Import: OK <{__name__}>")

class Ender(Gantry):
    """
    Ender platform controls

    Args:
        port (str): com port address
        limits (list, optional): lower and upper bounds of movement. Defaults to [(0,0,0), (0,0,0)].
        safe_height (float, optional): safe height. Defaults to None.
    
    Kwargs:
        max_speed (float, optional): maximum movement speed. Defaults to 250.
        home_coordinates (tuple, optional): position to home in arm coordinates. Defaults to (0,0,0).
        home_orientation (tuple, optional): orientation to home. Defaults to (0,0,0).
        orientate_matrix (numpy.matrix, optional): matrix to transform arm axes to workspace axes. Defaults to np.identity(3).
        translate_vector (numpy.ndarray, optional): vector to transform arm position to workspace position. Defaults to (0,0,0).
        implement_offset (tuple, optional): implement offset vector pointing from end of effector to tool tip. Defaults to (0,0,0).
        scale (int, optional): scale factor to transform arm scale to workspace scale. Defaults to 1.
        verbose (bool, optional): whether to print outputs. Defaults to False.
    """
    def __init__(self, 
        port: str, 
        limits: tuple[tuple[float]] = ((0,0,0), (240,235,210)), 
        safe_height: float = 30, 
        **kwargs
    ):
        super().__init__(port=port, limits=limits, safe_height=safe_height, **kwargs)
        self.home_coordinates = (0,0,self.heights['safe'])
        return

    def heat(self, bed_temperature: float) -> bool:
        """
        Heat bed to temperature

        Args:
            bed_temperature (int, or float): temperature of platform

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
        """
        Homing cycle for Ender platform
        """
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
