# -*- coding: utf-8 -*-
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
from types import SimpleNamespace
from typing import Sequence, final

# Third party imports
import numpy as np

# Local application imports
from ....core.position import Position, Deck, BoundingVolume
from .dobot_utils import Dobot

logger = logging.getLogger(__name__)
logger.debug(f"Import: OK <{__name__}>")

DEFAULT_SPEEDS = dict(j1=300, j2=300, j3=300, j4=300)

def within_volume(point: Sequence[float]) -> bool:
    assert len(point) == 3, f"Ensure point is a 3D coordinate"
    x,y,z = point
    # XY-plane
    j1 = round(math.degrees(math.atan(x/(y + 1E-6))), 3)
    if y < 0:
        j1 += (180 * math.copysign(1, x))
    if abs(j1) > 160:
        return False
    
    # Z-axis
    if not (-150 < z < 230):
        return False
    return True

@final
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
    
    _default_flags = SimpleNamespace(busy=False, connected=False, right_handed=False, stretched=False)
    _default_speeds = DEFAULT_SPEEDS
    def __init__(self, 
        host: str,
        joint_limits: Sequence[Sequence[float]]|None = None,
        right_handed: bool = True, 
        *,
        robot_position: Position = Position(),
        home_waypoints: Sequence[Position] = list(),
        home_position: Position = Position((0,300,0)),                # in terms of robot coordinate system
        tool_offset: Position = Position(),
        calibrated_offset: Position = Position(),
        scale: float = 1.0,
        deck: Deck|None = None,
        safe_height: float|None = 75,                                  # in terms of robot coordinate system
        saved_positions: dict = dict(),                                 # in terms of robot coordinate system
        speed_max: float|None = None,                                   # in mm/min
        movement_buffer: int|None = None,
        movement_timeout: int|None = None,
        verbose: bool = False, 
        simulation: bool = False,
        **kwargs
    ):
        """
        Instantiate the class

        Args:
            ip_address (str): IP address of Dobot
            right_handed (bool, optional): whether the robot is in right-handed mode (i.e elbow bends to the right). Defaults to True.
            safe_height (float, optional): height at which obstacles can be avoided. Defaults to 100.
            home_coordinates (tuple[float], optional): home coordinates for the robot. Defaults to (0,300,100).
        """
        workspace = BoundingVolume(dict(volume=within_volume))
        super().__init__(
            host=host, joint_limits=joint_limits, right_handed=right_handed,
            robot_position=robot_position, home_waypoints=home_waypoints, home_position=home_position,
            tool_offset=tool_offset, calibrated_offset=calibrated_offset, scale=scale,
            deck=deck, workspace=workspace, safe_height=safe_height, saved_positions=saved_positions,
            speed_max=speed_max, movement_buffer=movement_buffer, movement_timeout=movement_timeout,
            verbose=verbose, simulation=simulation,
            **kwargs
        )
        self._speed_max = max(self._default_speeds.values()) if speed_max is None else speed_max
        self.retractArm()
        self.home()
        return
    
    def retractArm(self, target:tuple[float]|None = None) -> bool:
        """
        Tuck in arm, rotate about base, then extend again

        Args:
            target (tuple[float]|None, optional): x,y,z coordinates of destination. Defaults to None.

        Returns:
            bool: whether movement is successful
        """
        safe_radius = 225
        x,y,_ = self.robot_position.coordinates
        if any((x,y)):
            w = ( (safe_radius**2)/(x**2 + y**2) )**0.5
            x,y = (x*w,y*w)
        else:
            x,y = (0,safe_radius)
        self.moveTo((x,y,self.safe_height))

        if target is not None and len(target) == 3:
            x1,y1,_ = target
            if any((x1,y1)):
                w1 = ( (safe_radius**2)/(x1**2 + y1**2) )**0.5
                x1,y1 = (x1*w1,y1*w1)
            else:
                x1,y1 = (0,safe_radius)
            self.moveTo((x1,y1,self.safe_height))
        return True
    
    # def _isFeasible(self, 
    #     coordinates: tuple[float], 
    #     transform_in: bool = False, 
    #     tool_offset: bool = False, 
    #     **kwargs
    # ) -> bool:
    #     """
    #     Checks and returns whether the target coordinate is feasible

    #     Args:
    #         coordinates (tuple[float]): target coordinates
    #         transform_in (bool, optional): whether to convert to internal coordinates first. Defaults to False.
    #         tool_offset (bool, optional): whether to convert from tool tip coordinates first. Defaults to False.

    #     Returns:
    #         bool: whether the target coordinate is feasible
    #     """
    #     if transform_in:
    #         coordinates = self._transform_in(coordinates=coordinates, tool_offset=tool_offset)
    #     x,y,z = coordinates
        
    #     # XY-plane
    #     j1 = round(math.degrees(math.atan(x/(y + 1E-6))), 3)
    #     if y < 0:
    #         j1 += (180 * math.copysign(1, x))
    #     if abs(j1) > 160:
    #         return False
        
    #     # Z-axis
    #     if not (-150 < z < 230):
    #         return False
    #     return not self.deck.isExcluded(self._transform_out(coordinates, tool_offset=True))
    
    # # Protected method(s)
    # def _get_move_wait_time(self, 
    #     distances: np.ndarray, 
    #     speeds: np.ndarray, 
    #     accels: np.ndarray|None = None,
    #     cartesian_to_angles: bool = False
    # ) -> float:
    #     """
    #     Get the amount of time to wait to complete movement

    #     Args:
    #         distances (np.ndarray): array of distances to travel
    #         speeds (np.ndarray): array of axis speeds
    #         accels (np.ndarray|None, optional): array of axis accelerations. Defaults to None.
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
