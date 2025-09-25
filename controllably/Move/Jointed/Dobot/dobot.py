# -*- coding: utf-8 -*-
"""
This module provides utility functions for Dobot's robot arms

Attributes:
    MOVEMENT_BUFFER (float): buffer time for movement
    MOVEMENT_TIMEOUT (float): timeout for movement
    
## Classes:
    `Dobot`: Dobot provides methods to control Dobot's robot arms

<i>Documentation last updated: 2025-02-22</i>
"""
# Standard library imports
from __future__ import annotations
from copy import deepcopy
import time
from typing import Sequence

# Third party imports
import numpy as np
from scipy.spatial.transform import Rotation

# Local application imports
from ....core.position import Position
from .. import RobotArm
from .dobot_api import DobotDevice

MOVEMENT_BUFFER = 1
MOVEMENT_TIMEOUT = 30

class Dobot(RobotArm):
    """
    Dobot provides methods to control Dobot's robot arms
    
    ### Constructor:
        `host` (str): IP address of Dobot
        `joint_limits` (Optional[Sequence[Sequence[float]]], optional): joint limits of the robot. Defaults to None.
        `home_waypoints` (Sequence[Position], optional): home waypoints for the robot. Defaults to [].
        `movement_buffer` (Optional[int], optional): buffer time for movement. Defaults to None.
        `movement_timeout` (Optional[int], optional): timeout for movement. Defaults to None.
        `verbose` (bool, optional): whether to output logs. Defaults to False.
        
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
        host: str,
        joint_limits: Sequence[Sequence[float]]|None = None,
        *,
        home_waypoints: Sequence[Position]|None = None,
        movement_buffer: int|None = None,
        movement_timeout: int|None = None,
        verbose: bool = False, 
        **kwargs
    ):
        """
        Initialize Dobot class
        
        Args:
            host (str): IP address of Dobot
            joint_limits (Optional[Sequence[Sequence[float]]], optional): joint limits of the robot. Defaults to None.
            home_waypoints (Sequence[Position], optional): home waypoints for the robot. Defaults to [].
            movement_buffer (Optional[int], optional): buffer time for movement. Defaults to None.
            movement_timeout (Optional[int], optional): timeout for movement. Defaults to None.
            verbose (bool, optional): whether to output logs. Defaults to False.
        """
        home_waypoints = list() if home_waypoints is None else home_waypoints
        super().__init__(
            device_type=DobotDevice, host=host, verbose=verbose, 
            home_waypoints=home_waypoints, joint_limits=joint_limits,
            movement_buffer=movement_buffer, movement_timeout=movement_timeout,
            **kwargs
        )
        assert isinstance(self.device, DobotDevice), "Ensure device is of type `DobotDevice`"
        self.device: DobotDevice = self.device
        self.movement_buffer = movement_buffer if movement_buffer is not None else MOVEMENT_BUFFER
        self.movement_timeout = movement_timeout if movement_timeout is not None else MOVEMENT_TIMEOUT
        self.settings = dict()
        
        self.connect()
        return
    
    # Properties
    @property
    def max_joint_accels(self) -> np.ndarray:
        """Maximum joint accelerations of the robot"""
        accel_j1 = self.settings.get('max_accel_j1', 0)
        accel_j2 = self.settings.get('max_accel_j2', 0)
        accel_j3 = self.settings.get('max_accel_j3', 0)
        accel_j4 = self.settings.get('max_accel_j4', 0)
        accel_j5 = self.settings.get('max_accel_j5', 0)
        accel_j6 = self.settings.get('max_accel_j6', 0)
        return np.array([accel_j1, accel_j2, accel_j3, accel_j4, accel_j5, accel_j6])
    
    @property
    def max_joint_speeds(self) -> np.ndarray:
        """Maximum joint speeds of the robot"""
        speed_j1 = self.settings.get('max_speed_j1', 0)
        speed_j2 = self.settings.get('max_speed_j2', 0)
        speed_j3 = self.settings.get('max_speed_j3', 0)
        speed_j4 = self.settings.get('max_speed_j4', 0)
        speed_j5 = self.settings.get('max_speed_j5', 0)
        speed_j6 = self.settings.get('max_speed_j6', 0)
        return np.array([speed_j1, speed_j2, speed_j3, speed_j4, speed_j5, speed_j6])
    
    def home(self, axis = None):
        self.updateJointPosition()
        self.updateRobotPosition()
        return super().home(axis)
    
    def moveBy(self,
        by: Sequence[float]|Position|np.ndarray,
        speed_factor: float|None = None,
        *,
        jog: bool = False,
        rapid: bool = False,
        robot: bool = False
    ) -> Position:
        """
        Move the robot by target direction

        Args:
            by (Sequence[float] | Position | np.ndarray): target direction
            speed_factor (float, optional): fraction of maximum speed to travel at. Defaults to None.
            jog (bool, optional): whether to jog the robot. Defaults to False.
            rapid (bool, optional): whether to move rapidly. Defaults to False.
            robot (bool, optional): whether to move the robot. Defaults to False.
            
        Returns:
            Position: new tool/robot position
        """
        assert isinstance(by, (Sequence, Position, np.ndarray)), "Ensure `by` is a Sequence or Position or np.ndarray object"
        if isinstance(by, (Sequence, np.ndarray)):
            if len(by) == 6:
                by = Position(by[:3], Rotation.from_euler('zyx', by[3:], degrees=True))
            else:
                assert len(by) == 3, "Ensure `by` is a 3-element sequence for x,y,z"
        # if isinstance(by, (Sequence, np.ndarray)):
        #     assert len(by) == 3, f"Ensure `by` is a 3-element sequence for x,y,z"
        move_by = by if isinstance(by, Position) else Position(by)
        speed_factor = self.speed_factor if speed_factor is None else speed_factor
        self._logger.info(f"Move By | {move_by} at speed factor {speed_factor}")
        
        # Convert to robot coordinates
        if robot:
            move_by = move_by
        else:
            inv_calibrated_offset = self.calibrated_offset.invert()
            by_coordinates = inv_calibrated_offset.Rotation.apply(move_by.coordinates)
            by_rotation = move_by.Rotation
            move_by = Position(by_coordinates, by_rotation)
        if not self.isFeasible(self.robot_position.coordinates + move_by.coordinates, external=False, tool_offset=False):
            self._logger.warning(f"Target movement {move_by} is not feasible")
            return self.robot_position if robot else self.worktool_position
        
        # Implementation of relative movement   
        current_position = deepcopy(self.robot_position)
        move_to = move_by.apply(current_position)
        return self.moveTo(move_to, speed_factor=speed_factor, jog=jog, rapid=rapid, robot=True)
        self.device.RelMovL(*move_by.coordinates, move_by.Rotation.as_euler('zyx', degrees=True)[0]) #BUG
        
        # Adding time delays to coincide with movement
        if not jog:
            speed_factor = self.speed_factor if speed_factor is None else speed_factor
            current_position = deepcopy(self.robot_position)
            move_to = move_by.apply(current_position)
            angular_distances = self._convert_cartesian_to_angles(self.robot_position.coordinates, move_to.coordinates)
            speeds = speed_factor*self.max_joint_speeds
            accels = self.max_joint_accels
            move_time = self._get_move_wait_time([*angular_distances,0,0,0], speeds, accels)
            time.sleep(move_time+self.movement_buffer)
        
        # Update position
        self.updateRobotPosition(by=move_by)
        return self.robot_position if robot else self.worktool_position

    def moveTo(self,
        to: Sequence[float]|Position|np.ndarray,
        speed_factor: float|None = None,
        *,
        jog: bool = False,
        rapid: bool = False,
        robot: bool = False
    ) -> Position:
        """ 
        Move the robot to target position
        
        Args:
            to (Sequence[float] | Position | np.ndarray): target position
            speed_factor (float, optional): fraction of maximum speed to travel at. Defaults to None.
            jog (bool, optional): whether to jog the robot. Defaults to False.
            rapid (bool, optional): whether to move rapidly. Defaults to False.
            robot (bool, optional): whether to move the robot. Defaults to False.
            
        Returns:
            Position: new tool/robot position
        """
        assert isinstance(to, (Sequence, Position, np.ndarray)), "Ensure `to` is a Sequence or Position or np.ndarray object"
        if isinstance(to, (Sequence, np.ndarray)):
            if len(to) == 6:
                to = Position(to[:3], Rotation.from_euler('zyx', to[3:], degrees=True))
            else:
                assert len(to) == 3, "Ensure `to` is a 3-element sequence for x,y,z"
        # if isinstance(to, (Sequence, np.ndarray)):
        #     assert len(to) == 3, f"Ensure `to` is a 3-element sequence for x,y,z"
        current_Rotation = self.robot_position.Rotation if robot else self.worktool_position.Rotation
        move_to = to if isinstance(to, Position) else Position(to, current_Rotation)
        speed_factor = self.speed_factor if speed_factor is None else speed_factor
        self._logger.info(f"Move To | {move_to} at speed factor {speed_factor}")
        
        # Convert to robot coordinates
        move_to = move_to if robot else self.transformToolToRobot(self.transformWorkToRobot(move_to, self.calibrated_offset), self.tool_offset)
        if not self.isFeasible(move_to.coordinates, external=False, tool_offset=False):
            self._logger.warning(f"Target position {move_to} is not feasible")
            return self.robot_position if robot else self.worktool_position
        
        # Implementation of absolute movement
        self.device.MovJ(*move_to.coordinates, move_to.Rotation.as_euler('zyx', degrees=True)[0])
        
        # Adding time delays to coincide with movement
        if not jog:
            speed_factor = self.speed_factor if speed_factor is None else speed_factor
            angular_distances = self._convert_cartesian_to_angles(self.robot_position.coordinates, move_to.coordinates)
            speeds = speed_factor*self.max_joint_speeds
            accels = self.max_joint_accels
            move_time = self._get_move_wait_time([*angular_distances,0,0,0], speeds, accels)
            time.sleep(move_time+self.movement_buffer)
        
        # Update position
        self.updateRobotPosition(to=move_to)
        return self.robot_position if robot else self.worktool_position
    
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
        return True #BUG
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
        Move the robot by target direction

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
        self.device.RelMovJ(*joint_move_by[:4])
        
        # Adding time delays to coincide with movement
        if not jog:
            speed_factor = self.speed_factor if speed_factor is None else speed_factor
            angular_distances = abs(joint_move_by)
            speeds = speed_factor*self.max_joint_speeds
            accels = self.max_joint_accels
            move_time = self._get_move_wait_time(angular_distances, speeds, accels)
            time.sleep(move_time+self.movement_buffer)
        
        # Update position
        self.updateJointPosition(by=joint_move_by)
        self.updateRobotPosition()
        return self.joint_position

    def jointMoveTo(self,
        to: Sequence[float]|np.ndarray,
        speed_factor: float|None = None,
        *,
        jog: bool = False,
        rapid: bool = False,
        robot: bool = True
    ) -> np.ndarray:
        """
        Move the robot by target direction

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
        self.device.JointMovJ(*joint_move_to[:4])
        
        # Adding time delays to coincide with movement
        if not jog:
            speed_factor = self.speed_factor if speed_factor is None else speed_factor
            angular_distances = abs(joint_move_to - self.joint_position)
            speeds = speed_factor*self.max_joint_speeds
            accels = self.max_joint_accels
            move_time = self._get_move_wait_time(angular_distances, speeds, accels)
            time.sleep(move_time+self.movement_buffer)
        
        # Update position
        self.updateJointPosition(to=joint_move_to)
        self.updateRobotPosition()
        return self.joint_position
    
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
        # joint_position = [*self.joint_position[:3],*rotate_to.as_euler('zyx', degrees=True)]
        # self.jointMoveTo(joint_position, speed_factor=speed_factor, jog=jog, robot=True)
        self.device.MovJ(*self.robot_position.coordinates, rotate_to.as_euler('zyx', degrees=True)[0])
        time.sleep(2/self.speed_factor)
        # rotate_by = rotate_to * self.robot_position.Rotation.inv()
        # self.rotateBy(rotate_by, speed_factor=speed_factor, jog=jog, robot=True)

        # Update position
        # self.updateJointPosition(to=joint_position)
        self.updateRobotPosition(to=rotate_to)
        return self.robot_position.Rotation if robot else self.worktool_position.Rotation

    def reset(self):
        """Reset the robot"""
        self.device.reset()
        self.updateJointPosition()
        self.updateRobotPosition()
        return 
    
    def setSpeedFactor(self, speed_factor:float|None = None, *, persist:bool = True):
        """
        Set the speed factor of the robot
        
        Args:
            speed_factor (float, optional): speed factor. Defaults to None.
            persist (bool, optional): persist speed factor. Defaults to True.
        """
        speed_factor = self.speed_factor if speed_factor is None else speed_factor
        assert isinstance(speed_factor, float), "Ensure speed factor is a float"
        assert (0.0 <= speed_factor <= 1.0), "Ensure speed factor is between 0.0 and 1.0"
        self.device.SpeedFactor(int(100*max(0.01,min(1,speed_factor))))
        if persist:
            self.speed_factor = speed_factor
        return
    
    # Overwritten methods
    def connect(self):
        """Connect to the device"""
        self.device.connect()
        self.setSpeedFactor(1.0)
        return
    
    def halt(self):
        """Halt robot movement"""
        self.device.ResetRobot()
        return
    
    def shutdown(self):
        """Shutdown procedure for tool"""
        self.device.ResetRobot()
        self.device.DisableRobot()
        return super().shutdown()
    
    def updateJointPosition(self, by: Sequence[float]|Rotation|np.ndarray|None = None, to: Sequence[float]|Rotation|np.ndarray|None = None):
        try:
            while True:
                time.sleep(0.1)
                joint_position_str = self.device.GetAngle()
                joint_position = [float(a) for a in joint_position_str[1:-1].split(',')]
                if any(joint_position) or self.flags.simulation:
                    break
            assert len(joint_position) == 6, "Unable to read output from device properly"
            return super().updateJointPosition(to=joint_position)
        except ValueError:
            pass
        return super().updateJointPosition(by=by, to=to)
    
    def updateRobotPosition(self, by: Position|Rotation|None = None, to: Position|Rotation|None = None) -> Position:
        try:
            while True:
                time.sleep(0.1)
                robot_position_str = self.device.GetPose()
                robot_position = [float(a) for a in robot_position_str[1:-1].split(',')]
                if any(robot_position) or self.flags.simulation:
                    break
            assert len(robot_position) == 6, "Unable to read output from device properly"
            current_position = Position(robot_position[:3], Rotation.from_euler('zyx',robot_position[-3:], degrees=True))
            return super().updateRobotPosition(to=current_position)
        except ValueError:
            pass
        return super().updateRobotPosition(by=by, to=to)
    
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
        raise NotImplementedError
    
    def _get_move_wait_time(self, distances, speeds, accels = None):
        accels = np.zeros([None]*len(speeds)) if accels is None else accels
        times = [self._calculate_travel_time(d,s,a,a) for d,s,a in zip(distances, speeds, accels)]
        move_time = (sum(times[:2]) + times[2])*1.5
        self._logger.debug(f'{move_time=} | {times=} | {distances=} | {speeds=} | {accels=}')
        return move_time if (0<move_time<np.inf) else 0
    