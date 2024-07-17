# %% -*- coding: utf-8 -*-
"""
This module holds the class for the MG400 from Dobot.

Classes:
    MG400 (Dobot)

Other constants and variables:
    SAFE_HEIGHT (float) = 75
"""
# Standard library imports
from __future__ import annotations
import logging
import math
import numpy as np
from typing import Optional

# Local application imports
from .dobot_utils import Dobot

logger = logging.getLogger(__name__)
logger.debug(f"Import: OK <{__name__}>")

SAFE_HEIGHT = 75

class MG400(Dobot):
    """
    MG400 provides methods to control Dobot's MG 400 arm

    ### Constructor
    Args:
        `ip_address` (str): IP address of Dobot
        `safe_height` (Optional[float], optional): height at which obstacles can be avoided. Defaults to SAFE_HEIGHT.
        `retract` (bool, optional): whether to retract arm before movement. Defaults to True.
        `home_coordinates` (tuple[float], optional): home coordinates for the robot. Defaults to (0,300,0).
    
    ### Methods
    - `isFeasible`: checks and returns whether the target coordinate is feasible
    - `retractArm`: tuck in arm, rotate about base, then extend again
    """
    
    def __init__(self, 
        ip_address: str, 
        safe_height: float = SAFE_HEIGHT, 
        retract: bool = True, 
        home_coordinates: tuple[float] = (0,300,0), 
        **kwargs
    ):
        """
        Instantiate the class

        Args:
            ip_address (str): IP address of Dobot
            safe_height (Optional[float], optional): height at which obstacles can be avoided. Defaults to SAFE_HEIGHT.
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
        self._speed_max = dict(j1=300, j2=300, j3=300, j4=300)
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
        return not self.deck.isExcluded(self._transform_out(coordinates, tool_offset=True))
    
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
        safe_height = self.heights.get('safe', SAFE_HEIGHT)
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
            ret = self.moveCoordTo((x1,y1,SAFE_HEIGHT), self.orientation)
            return_values.append(ret)
        return all(return_values)
    
    # # Protected method(s)
    # def _get_move_wait_time(self, 
    #     distances: np.ndarray, 
    #     speeds: np.ndarray, 
    #     accels: Optional[np.ndarray] = None,
    #     cartesian_to_angles: bool = False
    # ) -> float:
    #     """
    #     Get the amount of time to wait to complete movement

    #     Args:
    #         distances (np.ndarray): array of distances to travel
    #         speeds (np.ndarray): array of axis speeds
    #         accels (Optional[np.ndarray], optional): array of axis accelerations. Defaults to None.
    #         cartesian_to_angles (bool, optional): whether from coordinates to joint rotations angles. Defaults to False.

    #     Returns:
    #         float: wait time to complete travel
    #     """
    #     if cartesian_to_angles is None:
    #         return super()._get_move_wait_time(distances=distances, speeds=speeds, accels=accels)
        
    #     dx,dy,dz = distances[:3]
    #     rotation_1 = abs( math.degrees(math.atan2(dy, dx)) )                    # joint 1
    #     # rotation_2 = math.degrees(math.atan2(dz, np.linalg.norm([dx,dy])))      # joint 2
        
    #     distances = np.array([rotation_1, *distances[3:]])
    #     speeds = np.array([speeds[0], *speeds[3:]])
    #     accels = np.zeros(len(speeds)) if accels is None else accels
        
    #     times = [self._calculate_travel_time(d,s,a,a) for d,s,a in zip(distances, speeds, accels)]
    #     move_time = max(times[1:]) + times[0]
    #     if self.verbose:
    #         print(distances)
    #         print(speeds)
    #         print(accels)
    #         print(times)
    #     return move_time
