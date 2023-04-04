# %% -*- coding: utf-8 -*-
"""

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
    MG400 provides methods to control Dobot's MG 400 arm

    ### Constructor
    Args:
        `ip_address` (str, optional): IP address of Dobot. Defaults to '192.168.2.8'.
        `safe_height` (Optional[float], optional): height at which obstacles can be avoided. Defaults to 75.
        `retract` (bool, optional): whether to retract arm before movement. Defaults to True.
        `home_coordinates` (tuple[float], optional): home coordinates for the robot. Defaults to (0,300,0).
    
    ### Methods
    - `isFeasible`: checks and returns whether the target coordinate is feasible
    - `retractArm`: tuck in arm, rotate about base, then extend again
    """
    
    def __init__(self, 
        ip_address: str = '192.168.2.8', 
        safe_height: float = 75, 
        retract: bool = True, 
        home_coordinates: tuple[float] = (0,300,0), 
        **kwargs
    ):
        """
        Instantiate the class

        Args:
            ip_address (str, optional): IP address of Dobot. Defaults to '192.168.2.8'.
            safe_height (Optional[float], optional): height at which obstacles can be avoided. Defaults to 75.
            retract (bool, optional): whether to retract arm before movement. Defaults to True.
            home_coordinates (tuple[float], optional): home coordinates for the robot. Defaults to (0,300,0).
        """
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
        Checks and returns whether the target coordinate is feasible

        Args:
            coordinates (tuple[float]): target coordinates
            transform_in (bool, optional): whether to convert to internal coordinates first. Defaults to False.
            tool_offset (bool, optional): whether to convert from tool tip coordinates first. Defaults to False.

        Returns:
            bool: whether the target coordinate is feasible
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
        Tuck in arm, rotate about base, then extend again

        Args:
            target (Optional[tuple[float]], optional): x,y,z coordinates of destination. Defaults to None.

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
