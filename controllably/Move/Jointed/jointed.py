# -*- coding: utf-8 -*-
"""
This module provides the base class for jointed robot arms.

## Classes:
    `RobotArm`: RobotArm provides methods to control a robot arm

<i>Documentation last updated: 2025-02-22</i>
"""
# Standard library imports
from __future__ import annotations
from typing import Sequence

# Third party imports 
import numpy as np
from scipy.spatial.transform import Rotation

# Local application imports
from ...core.position import Position
from .. import Mover

class RobotArm(Mover):
    """
    RobotArm provides methods to control a robot arm
    
    ### Constructor:
        `home_waypoints` (Sequence[Position], optional): home waypoints for the robot. Defaults to list().
        `joint_limits` (Sequence[Sequence[float]], optional): joint limits for the robot. Defaults to None.
    
    ### Attributes and properties:
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
        `isFeasible`: checks and returns whether the target coordinates is feasible
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
    
    def __init__(self,
        *args,
        home_waypoints: Sequence[Position]|None = None,
        joint_limits: Sequence[Sequence[float]]|None = None,
        **kwargs
    ):
        """
        Initialize RobotArm class

        Args:
            home_waypoints (Sequence[Position], optional): home waypoints for the robot. Defaults to list().
            joint_limits (Sequence[Sequence[float]], optional): joint limits for the robot. Defaults to None.
        """
        home_waypoints = list() if home_waypoints is None else home_waypoints
        super().__init__(*args, **kwargs)
        self.joint_limits = np.array([[-180]*6, [180]*6]) if joint_limits is None else np.array(joint_limits)
        self._joint_position = np.zeros(6)
        
        self.home_waypoints: list[Position] = home_waypoints
        return
    
    @property
    def joint_position(self) -> np.ndarray:
        """Current joint angles"""
        return self._joint_position
    @joint_position.setter
    def joint_position(self, value: Sequence[float]|np.ndarray):
        assert isinstance(value, (Sequence, np.ndarray)), "Ensure `value` is a Sequence or np.ndarray object"
        assert len(value) == 6, "Ensure `value` is a 6-element sequence for j1~j6"
        self._joint_position = np.array(value)
        return
    
    def home(self, axis: str|None = None) -> bool:
        """
        Make the robot go home
        
        Args:
            axis (str, optional): axis to home. Defaults to None.
            
        Returns:
            bool: whether the robot successfully homed
        """
        self.moveToSafeHeight()
        if isinstance(axis,str) and axis.lower() == 'z':
            return True
        for waypoint in self.home_waypoints:
            self.moveTo(waypoint, robot=True)
        self.moveTo(self.home_position, robot=True)
        return True
    
    def isFeasibleJoint(self, joint_position: Sequence[float]|np.ndarray) -> bool:
        """
        Checks and returns whether the target joint angles are feasible
        
        Args:
            joint_position (Sequence[float]|np.ndarray): target joint angles
            
        Returns:
            bool: whether the target coordinates are feasible
        """
        assert isinstance(joint_position, (Sequence, np.ndarray)), "Ensure `joint_position` is a Sequence or np.ndarray object"
        assert len(joint_position) == 6, "Ensure `joint_position` is a 6-element sequence for j1~j6"
        
        feasible = all([(self.joint_limits[0][i] <= angle <= self.joint_limits[1][i]) for i, angle in enumerate(joint_position)])
        if not feasible:
            self._logger.error(f"Target set of joints {joint_position} is not feasible")
            raise RuntimeError(f"Target set of joints {joint_position} is not feasible")
        return feasible
    
    def jointMoveBy(self, 
        by: Sequence[float]|np.ndarray, 
        speed_factor: float|None = None,
        *,
        jog: bool = False,
        rapid: bool = False,
        robot: bool = True
    ) -> np.ndarray:
        """
        Move the robot by target joint angles

        Args:
            by (Sequence[float] | np.ndarray): target joint angles to move by
            speed_factor (float, optional): fraction of maximum speed to travel at. Defaults to None.
            jog (bool, optional): whether to jog the robot. Defaults to False.
            rapid (bool, optional): whether to move rapidly. Defaults to False.
            robot (bool, optional): whether to move the robot. Defaults to True.
            
        Returns:
            np.ndarray: new robot joint position
        """
        assert isinstance(by, (Sequence, np.ndarray)), "Ensure `by` is a Sequence or np.ndarray object"
        assert len(by) == 6, "Ensure `by` is a 6-element sequence for j1~j6"
        assert robot, "Ensure `robot` is True for joint movement"
        joint_move_by = np.array(by)
        speed_factor = self.speed_factor if speed_factor is None else speed_factor
        self._logger.info(f"Joint Move By | {joint_move_by} at speed factor {speed_factor}")
        
        # Convert to robot coordinates
        if not self.isFeasibleJoint(self.joint_position + joint_move_by):
            self._logger.warning(f"Target movement {joint_move_by} is not feasible")
            return self.joint_position
        
        # Implementation of relative movement
        ...
        
        # Update position
        self.updateJointPosition(by=joint_move_by)
        self.updateRobotPosition()
        raise NotImplementedError
        return self.joint_position

    def jointMoveTo(self,
        to: Sequence[float]|np.ndarray,
        speed_factor: float|None = None,
        *,
        jog: bool = False,
        rapid: bool = False,
        robot: bool = True
    ) -> Position:
        """
        Move the robot to target joint position

        Args:
            to (Sequence[float] | np.ndarray): target joint positions
            speed_factor (float, optional): fraction of maximum speed to travel at. Defaults to None.
            jog (bool, optional): whether to jog the robot. Defaults to False.
            rapid (bool, optional): whether to move rapidly. Defaults to False.
            robot (bool, optional): whether to move the robot. Defaults to True.
            
        Returns:
            np.ndarray: new robot joint position
        """
        assert isinstance(to, (Sequence, np.ndarray)), "Ensure `to` is a Sequence or np.ndarray object"
        assert len(to) == 6, "Ensure `to` is a 6-element sequence for j1~j6"
        assert robot, "Ensure `robot` is True for joint movement"
        joint_move_to = np.array(to)
        speed_factor = self.speed_factor if speed_factor is None else speed_factor
        self._logger.info(f"Joint Move To | {joint_move_to} at speed factor {speed_factor}")
        
        # Convert to robot coordinates
        if not self.isFeasibleJoint(joint_move_to):
            self._logger.warning(f"Target position {joint_move_to} is not feasible")
            return self.joint_position
        
        # Implementation of absolute movement
        ...
        
        # Update position
        self.updateJointPosition(to=joint_move_to)
        self.updateRobotPosition()
        raise NotImplementedError
        return self.joint_position
    
    def rotateBy(self,
        by: Sequence[float]|Rotation|np.ndarray,
        speed_factor: float|None = None,
        *,
        jog: bool = False,
        robot: bool = True
    ) -> Rotation:
        """
        Rotate the robot by target rotation
        
        Args:
            by (Sequence[float] | Rotation | np.ndarray): target rotation
            speed_factor (float, optional): fraction of maximum speed to rotate at. Defaults to None.
            jog (bool, optional): whether to jog the robot. Defaults to False.
            robot (bool, optional): whether to rotate the robot. Defaults to False.
            
        Returns:
            Rotation: new tool/robot orientation
        """
        assert isinstance(by, (Sequence, Rotation, np.ndarray)), "Ensure `by` is a Sequence or Rotation or np.ndarray object"
        if isinstance(by, (Sequence, np.ndarray)):
            assert len(by) == 3, "Ensure `by` is a 3-element sequence for c,b,a"
        rotate_by = by if isinstance(by, Rotation) else Rotation.from_euler('zyx', by, degrees=True)
        speed_factor = self.speed_factor if speed_factor is None else speed_factor
        self._logger.info(f"Rotate By | {rotate_by.as_euler('zyx', degrees=True)} at speed factor {speed_factor}")
        
        # Convert to robot coordinates
        rotate_by = rotate_by               # not affected by robot or tool coordinates for rotation
        
        # Implementation of relative rotation
        joint_position = [0,0,0,*rotate_by.as_euler('zyx', degrees=True)]
        self.jointMoveBy(joint_position, speed_factor=speed_factor, jog=jog, robot=True)
        
        # Update position
        # self.updateJointPosition(by=rotate_by)
        return self.robot_position.Rotation if robot else self.worktool_position.Rotation
        
    def rotateTo(self,
        to: Sequence[float]|Rotation|np.ndarray,
        speed_factor: float|None = None,
        *,
        jog: bool = False,
        robot: bool = False
    ) -> Rotation:
        """
        Rotate the robot to target orientation
        
        Args:
            to (Sequence[float] | Rotation | np.ndarray): target orientation
            speed_factor (float, optional): fraction of maximum speed to rotate at. Defaults to None.
            jog (bool, optional): whether to jog the robot. Defaults to False.
            robot (bool, optional): whether to rotate the robot. Defaults to False.
            
        Returns:
            Rotation: new tool/robot orientation
        """
        assert isinstance(to, (Sequence, Rotation, np.ndarray)), "Ensure `to` is a Sequence or Rotation or np.ndarray object"
        if isinstance(to, (Sequence, np.ndarray)):
            assert len(to) == 3, "Ensure `to` is a 3-element sequence for c,b,a"
        rotate_to = to if isinstance(to, Rotation) else Rotation.from_euler('zyx', to, degrees=True)
        speed_factor = self.speed_factor if speed_factor is None else speed_factor
        self._logger.info(f"Rotate To | {rotate_to.as_euler('zyx', degrees=True)} at speed factor {speed_factor}")
        
        # Convert to robot coordinates
        if robot:
            rotate_to = rotate_to
        else:
            rotate_to = self.tool_offset.invert().Rotation * self.calibrated_offset.invert().Rotation * rotate_to
        
        # Implementation of absolute rotation
        joint_position = [*self.joint_position[:3],*rotate_to.as_euler('zyx', degrees=True)]
        self.jointMoveTo(joint_position, speed_factor=speed_factor, jog=jog, robot=True)
        
        # Update position
        # self.updateJointPosition(to=joint_position)
        return self.robot_position.Rotation if robot else self.worktool_position.Rotation

    def updateJointPosition(self, by: Sequence[float]|Rotation|np.ndarray|None = None, to: Sequence[float]|Rotation|np.ndarray|None = None):
        """
        Update the joint position based on relative or absolute movement
        
        Args:
            by (Sequence[float] | Rotation | np.ndarray | None, optional): relative movement. Defaults to None.
            to (Sequence[float] | Rotation | np.ndarray | None, optional): absolute movement. Defaults to None.
        """
        assert (by is None) != (to is None), "Ensure input only for one of `by` or `to`"
        if by is not None:
            if isinstance(by, (Sequence, np.ndarray)):
                assert len(by) == 6, "Ensure `by` is a 6-element sequence for j1~j6"
                self.joint_position += np.array(by)
            elif isinstance(by, Rotation):
                self.joint_position += np.array([0,0,0,*by.as_euler('zyx', degrees=True)])
        elif to is not None:
            if isinstance(to, (Sequence, np.ndarray)):
                assert len(to) == 6, "Ensure `to` is a 6-element sequence for j1~j6"
                self.joint_position = np.array(to)
            elif isinstance(to, Rotation):
                self.joint_position = np.array([*self.joint_position[:3],*to.as_euler('zyx', degrees=True)])
        return
    
    def updateRobotPosition(self, by: Position|Rotation|None = None, to: Position|Rotation|None = None):
        self.updateJointPosition()
        return super().updateRobotPosition(by=by, to=to)
    