# -*- coding: utf-8 -*-
"""
This module provides methods to control Dobot's MG400 robot arm

Attributes:
    DEFAULT_SPEEDS (dict): default speeds of the robot
    
## Classes:
    `MG400`: MG400 provides methods to control Dobot's MG400 robot arm

## Functions:
    `within_volume`: checks whether a point is within the robot's workspace

<i>Documentation last updated: 2025-02-22</i>
"""
# Standard library imports
from __future__ import annotations
import math
from types import SimpleNamespace
from typing import Sequence

# Third party imports
import numpy as np

# Local application imports
from ....core.position import Position, Deck, BoundingVolume
from . import Dobot

DEFAULT_SPEEDS = dict(max_speed_j1=300, max_speed_j2=300, max_speed_j3=300, max_speed_j4=300)

def within_volume(point: Sequence[float]) -> bool:
    """ 
    Check whether a point is within the robot's workspace
    
    Args:
        point (Sequence[float]): 3D coordinates of the point
        
    Returns:
        bool: whether the point is within the robot's workspace
    """
    assert len(point) == 3, "Ensure point is a 3D coordinate"
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

class MG400(Dobot):
    """
    MG400 provides methods to control Dobot's MG400 robot arm

    ### Constructor:
        `host` (str): IP address of Dobot
        `joint_limits` (Sequence[Sequence[float]]|None, optional): joint limits of the robot. Defaults to None.
        `robot_position` (Position, optional): current position of the robot. Defaults to Position().
        `home_waypoints` (Sequence[Position], optional): home waypoints for the robot. Defaults to list().
        `home_position` (Position, optional): home position of the robot in terms of robot coordinate system. Defaults to Position((0,300,0)).
        `tool_offset` (Position, optional): tool offset from robot to end effector. Defaults to Position().
        `calibrated_offset` (Position, optional): calibrated offset from robot to work position. Defaults to Position().
        `scale` (float, optional): factor to scale the basis vectors by. Defaults to 1.0.
        `deck` (Deck|None, optional): Deck object for workspace. Defaults to None.
        `safe_height` (float|None, optional): safe height in terms of robot coordinate system. Defaults to 75.
        `saved_positions` (dict, optional): dictionary of saved positions. Defaults to dict().
        `speed_max` (float|None, optional): maximum speed of robot in mm/min. Defaults to None.
        `movement_buffer` (int|None, optional): buffer time for movement. Defaults to None.
        `movement_timeout` (int|None, optional): timeout for movement. Defaults to None.
        `verbose` (bool, optional): whether to output logs. Defaults to False.
        `simulation` (bool, optional): whether to simulate the robot. Defaults to False.
    
    ### Attributes and properties:
        `movement_buffer` (int): buffer time for movement
        `movement_timeout` (int): timeout for movement
        `max_joint_accels` (np.ndarray): maximum joint accelerations of the robot
        `max_joint_speeds` (np.ndarray): maximum joint speeds of the robot
        `home_waypoints` (list[Position]): home waypoints for the robot
        `joint_limits` (np.ndarray): joint limits for the robot
        `joint_position` (np.ndarray): current joint angles
        `connection_details` (dict): connection details for the device
        `device` (Device): device object that communicates with physical tool
        `flags` (SimpleNamespace[str, bool]): flags for the class
        `is_busy` (bool): whether the device is busy
        `is_connected` (bool): whether the device is connected
        `verbose` (bool): verbosity of class
        `deck` (Deck): Deck object for workspace
        `workspace` (BoundingVolume): workspace bounding box
        `safe_height` (float): safe height in terms of robot coordinate system
        `saved_positions` (dict): dictionary of saved positions
        `current_zone_waypoints` (tuple[str, list[Position]]): current zone entry waypoints
        `speed` (float): travel speed of robot
        `speed_factor` (float): fraction of maximum travel speed of robot
        `speed_max` (float): maximum speed of robot in mm/min
        `robot_position` (Position): current position of the robot
        `home_position` (Position): home position of the robot in terms of robot coordinate system
        `tool_offset` (Position): tool offset from robot to end effector
        `calibrated_offset` (Position): calibrated offset from robot to work position
        `scale` (float): factor to scale the basis vectors by
        `tool_position` (Position): robot position of the tool end effector
        `work_position` (Position): work position of the robot
        `worktool_position` (Position): work position of the tool end effector
        `position` (Position): work position of the tool end effector; alias for `worktool_position`
    
    ### Methods:
        `retractArm`: retract arm, rotate about base, then extend again
        `isFeasibleJoint`: checks and returns whether the target joint angles are feasible
        `jointMoveBy`: move the robot by target joint angles
        `jointMoveTo`: move the robot to target joint position
        `updateJointPosition`: update the joint position based on relative or absolute movement
        `connect`: connect to the device
        `disconnect`: disconnect from the device
        `resetFlags`: reset all flags to class attribute `_default_flags`
        `shutdown`: shutdown procedure for tool
        `enterZone`: enter a zone on the deck
        `exitZone`: exit the current zone on the deck
        `halt`: halt robot movement
        `home`: make the robot go home
        `isFeasible`: checks and returns whether the target coordinates is feasible and sets the handedness of the robot if necessary
        `loadDeck`: load `Deck` layout object to mover
        `loadDeckFromDict`: load `Deck` layout object from dictionary
        `loadDeckFromFile`: load `Deck` layout object from file
        `move`: move the robot in a specific axis by a specific value
        `moveBy`: move the robot by target direction
        `moveTo`: move the robot to target position
        `moveToSafeHeight`: move the robot to safe height
        `moveRobotTo`: move the robot to target position
        `moveToolTo`: move the tool end effector to target position
        `reset`: reset the robot
        `rotate`: rotate the robot in a specific axis by a specific value
        `rotateBy`: rotate the robot by target rotation
        `rotateTo`: rotate the robot to target orientation
        `rotateRobotTo`: rotate the robot to target orientation
        `rotateToolTo`: rotate the tool end effector to target orientation
        `safeMoveTo`: safe version of moveTo by moving to safe height first
        `setSafeHeight`: set safe height for robot
        `setSpeedFactor`: set the speed factor of the robot
        `setToolOffset`: set the tool offset of the robot
        `showWorkspace`: show the workspace of the robot
        `updateRobotPosition`: update the robot position
        `transformRobotToTool`: transform robot coordinates to tool coordinates
        `transformRobotToWork`: transform robot coordinates to work coordinates
        `transformToolToRobot`: transform tool coordinates to robot coordinates
        `transformWorkToRobot`: transform work coordinates to robot coordinates
        `calibrate`: calibrate the internal and external coordinate systems
    """
    
    _default_flags = SimpleNamespace(busy=False, connected=False, right_handed=False, stretched=False)
    _default_speeds = DEFAULT_SPEEDS
    def __init__(self, 
        host: str,
        joint_limits: Sequence[Sequence[float]]|None = None,
        *,
        robot_position: Position = Position(),
        home_waypoints: Sequence[Position]|None = None,
        home_position: Position = Position((0,300,0)),                # in terms of robot coordinate system
        tool_offset: Position = Position(),
        calibrated_offset: Position = Position(),
        scale: float = 1.0,
        deck: Deck|None = None,
        safe_height: float|None = 75,                                  # in terms of robot coordinate system
        saved_positions: dict|None = None,                                 # in terms of robot coordinate system
        speed_max: float|None = None,                                   # in mm/min
        movement_buffer: int|None = None,
        movement_timeout: int|None = None,
        verbose: bool = False, 
        simulation: bool = False,
        **kwargs
    ):
        """
        Initialize MG400 class
        
        Args:
            host (str): IP address of Dobot
            joint_limits (Sequence[Sequence[float]]|None, optional): joint limits of the robot. Defaults to None.
            robot_position (Position, optional): current position of the robot. Defaults to Position().
            home_waypoints (Sequence[Position], optional): home waypoints for the robot. Defaults to list().
            home_position (Position, optional): home position of the robot in terms of robot coordinate system. Defaults to Position((0,300,0)).
            tool_offset (Position, optional): tool offset from robot to end effector. Defaults to Position().
            calibrated_offset (Position, optional): calibrated offset from robot to work position. Defaults to Position().
            scale (float, optional): factor to scale the basis vectors by. Defaults to 1.0.
            deck (Deck|None, optional): Deck object for workspace. Defaults to None.
            safe_height (float|None, optional): safe height in terms of robot coordinate system. Defaults to 75.
            saved_positions (dict, optional): dictionary of saved positions. Defaults to dict().
            speed_max (float|None, optional): maximum speed of robot in mm/min. Defaults to None.
            movement_buffer (int|None, optional): buffer time for movement. Defaults to None.
            movement_timeout (int|None, optional): timeout for movement. Defaults to None.
            verbose (bool, optional): whether to output logs. Defaults to False.
            simulation (bool, optional): whether to simulate the robot. Defaults to False.
        """
        home_waypoints = list() if home_waypoints is None else home_waypoints
        saved_positions = saved_positions or dict()
        workspace = BoundingVolume(parametric_function=dict(volume=within_volume))
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
        self.retractArm()
        self.home()
        return
    
    def retractArm(self, target:Sequence[float]|None = None) -> Position:
        """
        Retract arm, rotate about base, then extend again

        Args:
            target (tuple[float]|None, optional): x,y,z coordinates of destination. Defaults to None.

        Returns:
            Position: current position of the robot
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
        return self.robot_position
    
    # Protected method(s)
    def _convert_cartesian_to_angles(self, src_point:np.ndarray, dst_point: np.ndarray) -> np.ndarray:
        """
        Convert travel between two points into relevant rotation angles and/or distances

        Args:
            src_point (np.ndarray): (x,y,z) coordinates, orientation of starting point
            dst_point (np.ndarray): (x,y,z) coordinates, orientation of ending point

        Returns:
            np.ndarray: relevant rotation angles (in degrees) and/or distances (in mm)
        """
        assert len(src_point) == 3 and len(dst_point) == 3, "Ensure both points are 3D coordinates"
        assert isinstance(src_point, np.ndarray) and isinstance(dst_point, np.ndarray), "Ensure both points are numpy arrays"
        distances = abs(dst_point - src_point)
        dx,dy,dz = distances[:3]
        j1_angle = abs( math.degrees(math.atan2(dy, dx)) )                    # joint 1
        j2_angle = math.degrees(math.atan2(dz, np.linalg.norm([dx,dy])))      # joint 2
        return np.array((j1_angle, j2_angle, dz))
