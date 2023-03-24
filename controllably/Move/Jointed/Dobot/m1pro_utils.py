# %% -*- coding: utf-8 -*-
"""
Created: Tue 2022/11/01 17:13:35
@author: Chang Jie

Notes / actionables:
- 
"""
# Standard library imports
from __future__ import annotations
import math
import numpy as np
import time

# Local application imports
from .dobot_utils import Dobot
print(f"Import: OK <{__name__}>")

class M1Pro(Dobot):
    """
    M1 Pro class.
    
    Args:
        ip_address (str, optional): IP address of arm. Defaults to '192.168.2.21'.
        retract (bool, optional): whether to tuck arm before each movement. Defaults to False.
        handedness (str, optional): handedness of robot (i.e. left or right). Defaults to 'left'.
        home_coordinates (tuple, optional): position to home in arm coordinates. Defaults to (0,300,100).
        
    Kwargs:
        attachment (str, optional): Dobot attachment. Defaults to None.
        home_orientation (tuple, optional): orientation to home. Defaults to (0,0,0).
        orientate_matrix (numpy.matrix, optional): matrix to transform arm axes to workspace axes. Defaults to np.identity(3).
        translate_vector (numpy.ndarray, optional): vector to transform arm position to workspace position. Defaults to (0,0,0).
        implement_offset (tuple, optional): implement offset vector pointing from end of effector to tool tip. Defaults to (0,0,0).
        scale (int, optional): scale factor to transform arm scale to workspace scale. Defaults to 1.
        verbose (bool, optional): whether to print outputs. Defaults to False.
        safe_height (float, optional): safe height. Defaults to None.
    """
    _default_flags = {
        'busy': False,
        'connected': False,
        'retract': False, 
        'right_handed': None
    }
    def __init__(self, 
        ip_address: str = '192.168.2.21', 
        right_handed: bool = True, 
        safe_height: float = 100,
        home_coordinates: tuple[float] = (0,300,100), 
        **kwargs
    ):
        super().__init__(
            ip_address=ip_address, 
            safe_height=safe_height,
            home_coordinates=home_coordinates, 
            **kwargs
        )
        self._speed_angular_max = 180
        self.setHandedness(right_hand=right_handed, stretch=False)
        self.home()
        return
    
    def home(self, safe:bool = True, tool_offset:bool = False) -> bool:
        """
        Return the robot to home

        Args:
            tool_offset (bool, optional): whether to consider the offset of the tooltip. Defaults to False.
        
        Returns:
            bool: whether movement is successful
        """
        return super().home(safe=safe, tool_offset=tool_offset)
    
    def isFeasible(self, 
        coordinates: tuple[float], 
        transform_in: bool = False, 
        tool_offset: bool = False, 
        **kwargs
    ) -> bool:
        """
        Checks if specified coordinates is a feasible position for robot to access.

        Args:
            coordinates (tuple): x,y,z coordinates
            transform (bool, optional): whether to transform the coordinates. Defaults to False.
            tool_offset (bool, optional): whether to consider tooltip offset. Defaults to False.

        Returns:
            bool: whether coordinates is a feasible position
        """
        if transform_in:
            coordinates = self._transform_in(coordinates=coordinates, tool_offset=tool_offset)
        x,y,z = coordinates
        
        # Z-axis
        if not (5 < z < 245):
            return False
        # XY-plane
        if x >= 0:
            r = (x**2 + y**2)**0.5
            if not (153 <= r <= 400):
                return False
        elif abs(y) < 230/2:
            return False
        elif (x**2 + (abs(y)-200)**2)**0.5 > 200:
            return False
        
        # Space constraints
        # if x > 344: # front edge
        #     return False
        # if x < 76 and abs(y) < 150: # elevated structure
        #     return False
        
        grad = abs(y/(x+1E-6))
        if grad > 0.75 or x < 0:
            right_hand = (y>0)
            self.setHandedness(right_hand=right_hand, stretch=True) 
        return not self.deck.is_excluded(self._transform_out(coordinates, tool_offset=True))
    
    def moveCoordBy(self, 
        vector: tuple[float] = (0,0,0), 
        angles: tuple[float] = (0,0,0)
    ) -> bool:
        """
        Relative Cartesian movement and tool orientation, using robot coordinates.

        Args:
            vector (tuple, optional): x,y,z displacement vector. Defaults to None.
            angles (tuple, optional): a,b,c rotation angles in degrees. Defaults to None.
        """
        if vector is None:
            vector = (0,0,0)
        if angles is None:
            angles = (0,0,0)
        coordinates, orientation = self.position
        new_coordinates = np.array(coordinates) + np.array(vector)
        new_orientation = np.array(orientation) + np.array(angles)
        return self.moveCoordTo(new_coordinates, new_orientation)
    
    def setHandedness(self, right_hand:bool, stretch:bool = False) -> bool:
        """
        Set handedness of robot arm

        Args:
            hand (str): handedness
            stretch (bool, optional): whether to stretch the arm. Defaults to False.

        Raises:
            Exception: The parameter 'hand' has to be either 'left' or 'right'
        """
        set_value = None
        if not right_hand and self.flags['right_handed'] != False:  # Set to left-handed: 0
            set_value = 0
        elif right_hand and self.flags['right_handed'] != True:     # Set to right-handed: 1
            set_value = 1
        else:
            return False
        
        try:
            self.dashboard.SetArmOrientation(set_value,1,1,1)
        except (AttributeError, OSError):
            if self.verbose:
                print("Not connected to arm!")
        else:
            time.sleep(2)
            if stretch:
                self.stretchArm()
                time.sleep(1)
        self.setFlag(right_handed=bool(set_value))
        return True
            
    def stretchArm(self) -> bool:
        """
        Stretch arm to switch handedness
        
        Returns:
            bool: whether movement is successful
        """
        _,y,z = self.coordinates
        y = 240 * math.copysign(1, y)
        return self.moveCoordTo(coordinates=(320,y,z))
   