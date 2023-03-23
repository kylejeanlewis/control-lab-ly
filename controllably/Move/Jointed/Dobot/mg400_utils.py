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
from typing import Optional

# Local application imports
from .dobot_utils import Dobot
print(f"Import: OK <{__name__}>")

class MG400(Dobot):
    """
    MG400 class.

    Args:
        ip_address (str, optional): IP address of arm. Defaults to '192.168.2.8'.
        retract (bool, optional): whether to tuck arm before each movement. Defaults to True.
        home_coordinates (tuple, optional): position to home in arm coordinates. Defaults to (0,300,0).
        
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
    def __init__(self, 
        ip_address: str = '192.168.2.8', 
        safe_height: float = 75, 
        retract: bool = True, 
        home_coordinates: tuple[float] = (0,300,0), 
        **kwargs
    ):
        super().__init__(
            ip_address=ip_address, 
            safe_height=safe_height,
            retract=retract,
            home_coordinates=home_coordinates, 
            **kwargs
        )
        self._speed_angular_max = 300
        self.home()
        return
    
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
        
        # XY-plane
        j1 = round(math.degrees(math.atan(x/(y + 1E-6))), 3)
        if y < 0:
            j1 += (180 * math.copysign(1, x))
        if abs(j1) > 160:
            return False
        
        # Z-axis
        if not (-150 < z < 230):
            return False
        return not self.deck.is_excluded(self._transform_out(coordinates, tool_offset=True))
    
    def retractArm(self, target:Optional[tuple[float]] = None) -> bool:
        """
        Tuck in arm, rotate about base, then extend again.

        Args:
            target (tuple, optional): x,y,z coordinates of destination. Defaults to None.
        
        Returns:
            bool: whether movement is successful
        """
        return_values= []
        safe_radius = 225
        safe_height = self.heights.get('safe', 75)
        x,y,_ = self.coordinates
        if any((x,y)):
            w = ( (safe_radius**2)/(x**2 + y**2) )**0.5
            x,y = (x*w,y*w)
        else:
            x,y = (0,safe_radius)
        ret = self.moveCoordTo((x,y,safe_height), self.orientation)
        return_values.append(ret)

        if target is not None and len(target) == 3:
            x1,y1,_ = target
            if any((x1,y1)):
                w1 = ( (safe_radius**2)/(x1**2 + y1**2) )**0.5
                x1,y1 = (x1*w1,y1*w1)
            else:
                x1,y1 = (0,safe_radius)
            ret = self.moveCoordTo((x1,y1,75), self.orientation)
            return_values.append(ret)
        return all(return_values)
