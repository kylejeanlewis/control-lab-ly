# -*- coding: utf-8 -*-
"""
This module holds the class for the M1Pro from Dobot.

Classes:
    M1Pro (Dobot)
"""
# Standard library imports
from __future__ import annotations
import logging
import math
import time
from types import SimpleNamespace
from typing import Sequence, final

# Third-party imports
import numpy as np

# Local application imports
from ....core.position import Position, Deck, BoundingVolume
from .dobot_utils import Dobot

logger = logging.getLogger(__name__)
logger.debug(f"Import: OK <{__name__}>")

DEFAULT_SPEEDS = dict(max_speed_j1=180, max_speed_j2=180, max_speed_j3=1000, max_speed_j4=1000)

def within_volume(point: Sequence[float]) -> bool:
    assert len(point) == 3, f"Ensure point is a 3D coordinate"
    x,y,z = point
    # Z-axis
    if not (5 <= z <= 245):
        return False
    # XY-plane
    if x >= 0:                                  # main working space
        r = (x**2 + y**2)**0.5
        if not (153 <= r <= 400):
            return False
    elif abs(y) < 230/2:                        # behind the robot
        return False
    elif (x**2 + (abs(y)-200)**2)**0.5 > 200:
        return False
    return True

@final
class M1Pro(Dobot):
    """
    M1Pro provides methods to control Dobot's M1 Pro arm
    
    ### Constructor
    Args:
        `ip_address` (str): IP address of Dobot
        `right_handed` (bool, optional): whether the robot is in right-handed mode (i.e elbow bends to the right). Defaults to True.
        `safe_height` (float, optional): height at which obstacles can be avoided. Defaults to 100.
        `home_coordinates` (tuple[float], optional): home coordinates for the robot. Defaults to (0,300,100).
    
    ### Methods
    - `home`: make the robot go home
    - `isFeasible`: checks and returns whether the target coordinate is feasible
    - `moveBy`: relative Cartesian movement and tool orientation, using robot coordinates
    - `retractArm`: tuck in arm, rotate about base, then extend again (NOTE: not implemented)
    - `setHandedness`: set the handedness of the robot
    - `stretchArm`: extend the arm to full reach
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
        home_position: Position = Position((0,300,100)),                # in terms of robot coordinate system
        tool_offset: Position = Position(),
        calibrated_offset: Position = Position(),
        scale: float = 1.0,
        deck: Deck|None = None,
        safe_height: float|None = 100,                                  # in terms of robot coordinate system
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
            host=host, joint_limits=joint_limits,
            robot_position=robot_position, home_waypoints=home_waypoints, home_position=home_position,
            tool_offset=tool_offset, calibrated_offset=calibrated_offset, scale=scale,
            deck=deck, workspace=workspace, safe_height=safe_height, saved_positions=saved_positions,
            speed_max=speed_max, movement_buffer=movement_buffer, movement_timeout=movement_timeout,
            verbose=verbose, simulation=simulation,
            **kwargs
        )
        self._speed_max = max(self._default_speeds.values()) if speed_max is None else speed_max
        self.settings.update(self._default_speeds)
        self.setHandedness(right_handed=right_handed, stretch=False)
        self.home()
        return
    
    def isFeasible(self, coordinates: Sequence[float]|np.ndarray, external: bool = True, tool_offset:bool = True) -> bool:
        """
        Checks and returns whether the target coordinate is feasible

        Args:
            coordinates (tuple[float]): target coordinates
            transform_in (bool, optional): whether to convert to internal coordinates first. Defaults to False.
            tool_offset (bool, optional): whether to convert from tool tip coordinates first. Defaults to False.

        Returns:
            bool: whether the target coordinate is feasible
        """
        feasible = super().isFeasible(coordinates=coordinates, external=external, tool_offset=tool_offset)
        if not feasible:
            return False
        position = Position(coordinates)
        in_pos = position
        if external:
            in_pos = self.transformWorkToRobot(position, self.calibrated_offset, self.scale)
            in_pos = self.transformToolToRobot(in_pos, self.tool_offset) if tool_offset else in_pos
        x,y,_ = position.coordinates
        
        grad = abs(y/(x+1E-6))
        gradient_threshold = 0.25
        if grad > gradient_threshold or x < 0:
            right_handed = (y>0)
            self.setHandedness(right_handed=right_handed, stretch=True) 
        return feasible

    def setHandedness(self, right_handed:bool, stretch:bool = False) -> bool:
        """
        Set the handedness of the robot

        Args:
            right_handed (bool): whether to select right-handedness
            stretch (bool, optional): whether to stretch the arm. Defaults to False.

        Returns:
            bool: whether movement is successful
        """
        if right_handed == self.flags.right_handed:
            return False
        
        self.device.SetArmOrientation(right_handed)
        time.sleep(2)
        self._move_time_buffer = 2/self.speed_factor + self._default_move_time_buffer
        if stretch:
            self.stretchArm()
            self._move_time_buffer = 1/self.speed_factor + self._default_move_time_buffer
        self.flags.right_handed = right_handed
        return True
            
    def stretchArm(self) -> bool:
        """
        Extend the arm to full reach
        
        Returns:
            bool: whether movement is successful
        """
        if self.flags.stretched:
            return False
        x,y,z = self.robot_position.coordinates
        y_stretch = math.copysign(240, y)
        self.moveToSafeHeight()
        self.moveTo((320,y_stretch,self.safe_height))
        self.moveTo((x,y,self.safe_height))
        self.moveTo((x,y,z))
        self.flags.stretched = True
        return True
   
    # Protected method(s)
    def _convert_cartesian_to_angles(self, src_point:np.ndarray, dst_point: np.ndarray) -> np.ndarray:
        """
        Convert travel between two points into relevant rotation angles and/or distances

        Args:
            src_point (np.ndarray): (x,y,z) coordinates, orientation of starting point
            dst_point (np.ndarray): (x,y,z) coordinates, orientation of ending point

        Returns:
            float: relevant rotation angles (in degrees) and/or distances (in mm)
        """
        assert len(src_point) == 3 and len(dst_point) == 3, f"Ensure both points are 3D coordinates"
        assert isinstance(src_point, np.ndarray) and isinstance(dst_point, np.ndarray), f"Ensure both points are numpy arrays"
        right_handed = 2*(int(self.flags.right_handed)-0.5) # 1 if right-handed; -1 if left-handed
        x1,y1,z1 = src_point
        x2,y2,z2 = dst_point
        r1 = (x1**2 + y1**2)**0.5
        r2 = (x2**2 + y2**2)**0.5
        
        theta1 = math.degrees(math.atan2(y1, x1))
        theta2 = math.degrees(math.atan2(y2, x2))
        phi1 = math.degrees(math.acos(r1/400)) * (-right_handed)
        phi2 = math.degrees(math.acos(r2/400)) * (-right_handed)
        
        src_j1_angle = theta1 + phi1
        dst_j1_angle = theta2 + phi2
        j1_angle = abs(dst_j1_angle - src_j1_angle)
        
        src_j2_angle = 2*phi1 * right_handed
        dst_j2_angle = 2*phi2 * right_handed
        j2_angle = abs(dst_j2_angle - src_j2_angle)
        
        z_travel = abs(z2 - z1)
        return np.array((j1_angle, j2_angle, z_travel))
