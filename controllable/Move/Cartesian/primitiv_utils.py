# %% -*- coding: utf-8 -*-
"""
Created: Tue 2022/11/01 17:13:35
@author: Chang Jie

Notes / actionables:
-
"""
# Standard library imports
import time

# Local application imports
from .cartesian_utils import Gantry
print(f"Import: OK <{__name__}>")

class Primitiv(Gantry):
    """
    Primitiv platform controls

    Args:
        port (str): com port address
        limits (list, optional): lower and upper bounds of movement. Defaults to [(0,0,0), (0,0,0)].
        safe_height (float, optional): safe height. Defaults to None.
        move_speed (float, optional): movement speed. Defaults to 0.
    
    Kwargs:
        home_coordinates (tuple, optional): position to home in arm coordinates. Defaults to (0,0,0).
        home_orientation (tuple, optional): orientation to home. Defaults to (0,0,0).
        orientate_matrix (numpy.matrix, optional): matrix to transform arm axes to workspace axes. Defaults to np.identity(3).
        translate_vector (numpy.ndarray, optional): vector to transform arm position to workspace position. Defaults to np.zeros(3).
        implement_offset (tuple, optional): implement offset vector pointing from end of effector to tool tip. Defaults to (0,0,0).
        scale (int, optional): scale factor to transform arm scale to workspace scale. Defaults to 1.
        verbose (bool, optional): whether to print outputs. Defaults to False.
    """
    def __init__(self, port:str, limits=[(-410,-290,-120), (0,0,0)], safe_height=-80, **kwargs):
        super().__init__(port=port, limits=limits, safe_height=safe_height, **kwargs)
        self.selected_position = ''
        return
    
    def _connect(self, port:str):
        """
        Connect to machine control unit

        Args:
            port (str): com port address
            
        Returns:
            serial.Serial: serial connection to machine control unit if connection is successful, else None
        """
        device = super()._connect(port, 115200, timeout=1)
        try:
            device.close()
            device.open()

            # Start grbl 
            device.write(bytes("\r\n\r\n", 'utf-8'))
            time.sleep(2)
            device.flushInput()
        except Exception as e:
            if self.verbose:
                print(e)
        return device
    
    def home(self):
        """
        Homing cycle for Primitiv platform
        """
        try:
            self.device.write(bytes("$H\n", 'utf-8'))
            print(self.device.readline())
        except Exception as e:
            if self.verbose:
                print(e)
        
        self.coordinates = (0,0,0)
        return
