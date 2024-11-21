# -*- coding: utf-8 -*-
"""
This module holds the base class for jointed mover tools.

Classes:
    RobotArm (Mover)
"""
# Standard library imports
from __future__ import annotations
import logging
from typing import Sequence

# Third party imports 
import numpy as np
from scipy.spatial.transform import Rotation

# Local application imports
from ...core.position import Position
from ..move_utils import Mover

logger = logging.getLogger(__name__)
logger.debug(f"Import: OK <{__name__}>")

class RobotArm(Mover):
    """
    Abstract Base Class (ABC) for Robot Arm objects. RobotArm provides controls for jointed robots with articulated arms.
    ABC cannot be instantiated, and must be subclassed with abstract methods implemented before use.
    
    ### Constructor
    Args:
        `safe_height` (float|None, optional): height at which obstacles can be avoided. Defaults to None.
        `retract` (bool, optional): whether to retract arm before movement. Defaults to False.

    ### Methods
    #### Abstract
    - `disconnect`: disconnect from device
    - `isFeasible`: checks and returns whether the target coordinate is feasible
    - `moveCoordBy`: relative Cartesian movement and tool orientation, using robot coordinates
    - `moveCoordTo`: absolute Cartesian movement and tool orientation, using robot coordinates
    - `jointMoveBy`: relative joint movement
    - `jointMoveTo`: absolute joint movement
    - `reset`: reset the robot
    - `retractArm`: tuck in arm, rotate about base, then extend again
    - `setSpeed`: set the speed of the robot
    - `shutdown`: shutdown procedure for tool
    - `_connect`: connection procedure for tool
    #### Public
    - `home`: make the robot go home
    - `moveBy`: move the robot by target direction, by specified vector and angles
    - `moveTo`: move the robot to target position, using workspace coordinates
    - `rotateBy`: relative end effector rotation
    - `rotateTo`: absolute end effector rotation
    """
    
    _place: str = '.'.join(__name__.split('.')[1:-1])
    def __init__(self, **kwargs):
        """
        Instantiate the class

        Args:
            safe_height (float|None, optional): height at which obstacles can be avoided. Defaults to None.
            retract (bool, optional): whether to retract arm before movement. Defaults to False.
        """
        super().__init__(**kwargs)
        self.joint_limits = np.array([[-180]*6, [180]*6])
        self._joint_angles = np.zeros(6)
        return
    
    @property
    def joint_angles(self) -> np.ndarray:
        """Current joint angles"""
        return self._joint_angles
    @joint_angles.setter
    def joint_angles(self, value: Sequence[float]|np.ndarray):
        assert isinstance(value, (Sequence, np.ndarray)), f"Ensure `value` is a Sequence or np.ndarray object"
        assert len(value) == 6, f"Ensure `value` is a 6-element sequence for j1~j6"
        self._joint_angles = np.array(value)
        return
    
    def isFeasibleJoint(self, joint_angles: Sequence[float]|np.ndarray) -> bool:
        """
        Check if the target joint angles are feasible
        
        Args:
            joint_angles (tuple[float]): j1~j6 orientation angles in degrees
            
        Returns:
            bool: whether the target position is feasible
        """
        assert isinstance(joint_angles, (Sequence, np.ndarray)), "Ensure `joint_angles` is a Sequence or np.ndarray object"
        assert len(joint_angles) == 6, "Ensure `joint_angles` is a 6-element sequence for j1~j6"
        
        feasible = all([(self.joint_limits[0][i] <= angle <= self.joint_limits[1][i]) for i, angle in enumerate(joint_angles)])
        if not feasible:
            self._logger.error(f"Target set of joints {joint_angles} is not feasible")
            raise RuntimeError(f"Target set of joints {joint_angles} is not feasible")
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
        Relative joint movement

        Args:
            relative_angles (tuple[float]): j1~j6 rotation angles in degrees

        Raises:
            ValueError: Length of input needs to be 6.

        Returns:
            bool: whether movement is successful
        """
        assert isinstance(by, (Sequence, np.ndarray)), "Ensure `by` is a Sequence or np.ndarray object"
        assert len(by) == 6, "Ensure `by` is a 6-element sequence for j1~j6"
        assert robot, "Ensure `robot` is True for joint movement"
        joint_move_by = np.array(by)
        speed_factor = self.speed_factor if speed_factor is None else speed_factor
        self._logger.info(f"Joint Move By | {joint_move_by} at speed factor {speed_factor}")
        
        # Convert to robot coordinates
        if not self.isFeasibleJoint(self.joint_angles + joint_move_by):
            self._logger.warning(f"Target movement {joint_move_by} is not feasible")
            return self.joint_angles
        
        # Implementation of relative movement
        ...
        
        # Update position
        self.updateJointPosition(by=joint_move_by)
        raise NotImplementedError
        return self.joint_angles

    def jointMoveTo(self,
        to: Sequence[float]|np.ndarray,
        speed_factor: float|None = None,
        *,
        jog: bool = False,
        rapid: bool = False,
        robot: bool = True
    ) -> Position:
        """
        Absolute joint movement

        Args:
            absolute_angles (tuple[float]): j1~j6 orientation angles in degrees

        Raises:
            ValueError: Length of input needs to be 6.

        Returns:
            bool: whether movement is successful
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
            return self.joint_angles
        
        # Implementation of absolute movement
        ...
        
        # Update position
        self.updateJointPosition(to=joint_move_to)
        raise NotImplementedError
        return self.joint_angles
      

    def home(self, safe:bool = True, tool_offset:bool = True) -> bool:
        """
        Make the robot go home

        Args:
            safe (bool, optional): whether to use `safeMoveTo()`. Defaults to True.
            tool_offset (bool, optional): whether to consider tooltip offset. Defaults to True.
        
        Returns:
            bool: whether movement is successful
        """
        success= []
        ret = False
        coordinates = self.home_coordinates - self.implement_offset if tool_offset else self.home_coordinates
        
        # Tuck arm in to avoid collision
        if self.flags.get('retract', False):
            ret = self.retractArm(coordinates)
            success.append(ret)
        
        # Go to home position
        if safe:
            coordinates = self._transform_out(coordinates=coordinates, tool_offset=tool_offset)
            ret = self.safeMoveTo(coordinates=coordinates, orientation=self.home_orientation, tool_offset=tool_offset)
        else:
            ret = self.moveCoordTo(coordinates, self.home_orientation)
        success.append(ret)
        print("Homed")
        return all(success)
    
    def rotateBy(self,
        by: Sequence[float]|Rotation|np.ndarray,
        speed_factor: float|None = None,
        *,
        jog: bool = False,
        robot: bool = True
    ) -> Rotation:
        """
        Rotate the robot by target direction
        
        Args:
            by (Sequence[float] | Rotation | np.ndarray): target direction
            speed_factor (float, optional): fraction of maximum speed to rotate at. Defaults to None.
            jog (bool, optional): whether to jog the robot. Defaults to False.
            robot (bool, optional): whether to rotate the robot. Defaults to False.
            
        Returns:
            Rotation: new tool/robot orientation
        """
        assert isinstance(by, (Sequence, Rotation, np.ndarray)), f"Ensure `by` is a Sequence or Rotation or np.ndarray object"
        if isinstance(by, (Sequence, np.ndarray)):
            assert len(by) == 3, f"Ensure `by` is a 3-element sequence for c,b,a"
        rotate_by = by if isinstance(by, Rotation) else Rotation.from_euler('zyx', by, degrees=True)
        speed_factor = self.speed_factor if speed_factor is None else speed_factor
        self._logger.info(f"Rotate By | {rotate_by} at speed factor {speed_factor}")
        
        # Convert to robot coordinates
        rotate_by = rotate_by               # not affected by robot or tool coordinates for rotation
        
        # Implementation of relative rotation
        current_orientation = self.robot_position.Rotation if robot else self.tool_position.Rotation
        new_orientation = rotate_by * current_orientation
        return self.rotateTo(new_orientation, speed_factor=speed_factor, jog=jog, robot=robot)
        ...
        
        # Update position
        self.updateJointPosition(by=rotate_by)
        raise NotImplementedError
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
        assert isinstance(to, (Sequence, Rotation, np.ndarray)), f"Ensure `to` is a Sequence or Rotation or np.ndarray object"
        if isinstance(to, (Sequence, np.ndarray)):
            assert len(to) == 3, f"Ensure `to` is a 3-element sequence for c,b,a"
        rotate_to = to if isinstance(to, Rotation) else Rotation.from_euler('zyx', to, degrees=True)
        speed_factor = self.speed_factor if speed_factor is None else speed_factor
        self._logger.info(f"Rotate To | {rotate_to} at speed factor {speed_factor}")
        
        # Convert to robot coordinates
        if robot:
            rotate_to = rotate_to
        else:
            rotate_to = self.tool_offset.invert().Rotation * self.calibrated_offset.invert().Rotation * rotate_to
        
        # Implementation of absolute rotation
        joint_angles = [0,0,0,*rotate_to.as_euler('xyz', degrees=True)]
        self.jointMoveTo(joint_angles, speed_factor=speed_factor, jog=jog, robot=True)
        
        # Update position
        # self.updateJointPosition(to=joint_angles)
        return self.robot_position.Rotation if robot else self.worktool_position.Rotation
