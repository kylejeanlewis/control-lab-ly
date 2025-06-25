# -*- coding: utf-8 -*-
"""
This module provides methods to control Dobot's M1Pro robot arm

Attributes:
    DEFAULT_SPEEDS (dict): default speeds of the robot
    
## Classes:
    `M1Pro`: M1Pro provides methods to control Dobot's M1Pro robot arm
    
## Functions:
    `within_volume`: check if a point is within the robot's workspace

<i>Documentation last updated: 2025-02-22</i>
"""
# Standard library imports
from __future__ import annotations
import math
import time
from types import SimpleNamespace
from typing import Sequence

# Third-party imports
import numpy as np

# Local application imports
from ....core.position import Position, Deck, BoundingVolume
from . import Dobot

DEFAULT_SPEEDS = dict(max_speed_j1=180, max_speed_j2=180, max_speed_j3=1000, max_speed_j4=1000)

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

class M1Pro(Dobot):
    """
    M1Pro provides methods to control Dobot's M1Pro robot arm
    
    ### Constructor:
        `host` (str): IP address of Dobot
        `joint_limits` (Sequence[Sequence[float]]|None, optional): joint limits of the robot. Defaults to None.
        `right_handed` (bool, optional): whether the robot is in right-handed mode (i.e elbow bends to the right). Defaults to True.
        `robot_position` (Position, optional): current position of the robot. Defaults to Position().
        `home_waypoints` (Sequence[Position], optional): home waypoints for the robot. Defaults to list().
        `home_position` (Position, optional): home position of the robot in terms of robot coordinate system. Defaults to Position((300,0,240)).
        `tool_offset` (Position, optional): tool offset from robot to end effector. Defaults to Position().
        `calibrated_offset` (Position, optional): calibrated offset from robot to work position. Defaults to Position().
        `scale` (float, optional): factor to scale the basis vectors by. Defaults to 1.0.
        `deck` (Deck|None, optional): Deck object for workspace. Defaults to None.
        `safe_height` (float|None, optional): safe height in terms of robot coordinate system. Defaults to 240.
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
        `setHandedness`: set the handedness of the robot
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
    
    _default_flags = SimpleNamespace(busy=False, connected=False, right_handed=False)
    _default_speeds = DEFAULT_SPEEDS
    def __init__(self, 
        host: str,
        joint_limits: Sequence[Sequence[float]]|None = None,
        right_handed: bool = True, 
        *,
        robot_position: Position = Position(),
        home_waypoints: Sequence[Position]|None = None,
        home_position: Position = Position((300,0,240)),                # in terms of robot coordinate system
        tool_offset: Position = Position(),
        calibrated_offset: Position = Position(),
        scale: float = 1.0,
        deck: Deck|None = None,
        safe_height: float|None = 240,                                  # in terms of robot coordinate system
        saved_positions: dict|None = None,                                 # in terms of robot coordinate system
        speed_max: float|None = None,                                   # in mm/min
        movement_buffer: int|None = None,
        movement_timeout: int|None = None,
        verbose: bool = False, 
        simulation: bool = False,
        **kwargs
    ):
        """
        Initialize M1Pro class
        
        Args:
            host (str): IP address of Dobot
            joint_limits (Sequence[Sequence[float]]|None, optional): joint limits of the robot. Defaults to None.
            right_handed (bool, optional): whether the robot is in right-handed mode (i.e elbow bends to the right). Defaults to True.
            robot_position (Position, optional): current position of the robot. Defaults to Position().
            home_waypoints (Sequence[Position], optional): home waypoints for the robot. Defaults to list().
            home_position (Position, optional): home position of the robot in terms of robot coordinate system. Defaults to Position((300,0,240)).
            tool_offset (Position, optional): tool offset from robot to end effector. Defaults to Position().
            calibrated_offset (Position, optional): calibrated offset from robot to work position. Defaults to Position().
            scale (float, optional): factor to scale the basis vectors by. Defaults to 1.0.
            deck (Deck|None, optional): Deck object for workspace. Defaults to None.
            safe_height (float|None, optional): safe height in terms of robot coordinate system. Defaults to 240.
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
        self.setHandedness(right_handed=right_handed, stretch=False)
        self.home()
        return
    
    def isFeasible(self, coordinates: Sequence[float]|np.ndarray, external: bool = True, tool_offset:bool = True) -> bool:
        """
        Checks and returns whether the target coordinates is feasible. Also sets the handedness of the robot if necessary.
        
        Args:
            coordinates (Sequence[float]|np.ndarray): target coordinates
            external (bool, optional): whether the target coordinates are in external coordinates. Defaults to True.
            tool_offset (bool, optional): whether to consider the tool offset. Defaults to True.
            
        Returns:
            bool: whether the target coordinates are feasible
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
            # stretch = (self.robot_position.y/y) > 0
            self.setHandedness(right_handed=right_handed, stretch=False) 
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
        self.flags.right_handed = right_handed
        if stretch:
            self.stretchArm()
        return True
            
    def stretchArm(self) -> bool:
        """
        Extend the arm to full reach
        
        Returns:
            bool: whether movement is successful
        """
        x,y,z = self.robot_position.coordinates
        y_stretch = math.copysign(240, y)
        self.moveToSafeHeight()
        self.moveTo((320,y_stretch,self.safe_height))
        self.moveTo((x,y,self.safe_height))
        self.moveTo((x,y,z))
        return True
   
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
        right_handed = 2*(int(self.flags.right_handed)-0.5) # 1 if right-handed; -1 if left-handed
        x1,y1,z1 = src_point
        x2,y2,z2 = dst_point
        r1 = (x1**2 + y1**2)**0.5
        r2 = (x2**2 + y2**2)**0.5
        
        assert r1<=400, f"Check values for {r1=}, {x1=}, {y1=}"
        assert r2<=400, f"Check values for {r2=}, {x2=}, {y2=}"
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
