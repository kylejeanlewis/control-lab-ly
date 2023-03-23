# %% -*- coding: utf-8 -*-
"""
Created: Tue 2022/11/01 17:13:35
@author: Chang Jie

Notes / actionables:
-
"""
# Standard library imports
from __future__ import annotations
import time
from typing import Optional

# Local application imports
from ...misc import Helper
from .cartesian_utils import Gantry
print(f"Import: OK <{__name__}>")

class Primitiv(Gantry):
    """
    Primitiv platform controls

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
        limits: tuple[tuple[float]] = ((-410,-290,-120), (0,0,0)), 
        safe_height: float = -80, 
        **kwargs
    ):
        super().__init__(port=port, limits=limits, safe_height=safe_height, **kwargs)
        return
    
    @Helper.safety_measures
    def home(self) -> bool:
        """
        Homing cycle for Primitiv platform
        """
        self._query("$H\n")
        self.coordinates = self.home_coordinates
        print("Homed")
        return True

    # Protected method(s)
    def _connect(self, port:str, baudrate:int = 115200, timeout:Optional[int] = None):
        """
        Connect to machine control unit

        Args:
            port (str): com port address
            baudrate (int): baudrate. Defaults to 115200.
            timeout (int, optional): timeout in seconds. Defaults to None.
            
        Returns:
            serial.Serial: serial connection to machine control unit if connection is successful, else None
        """
        super()._connect(port, baudrate, timeout)
        try:
            self.device.close()
        except Exception as e:
            if self.verbose:
                print(e)
        else:
            self.device.open()
            # Start grbl 
            self._write(bytes("\r\n\r\n", 'utf-8'))
            time.sleep(2)
            self.device.flushInput()
        return
