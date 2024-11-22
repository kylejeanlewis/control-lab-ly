# -*- coding: utf-8 -*-
"""
This module holds the base class for movement tools from Dobot.

Classes:
    Dobot (RobotArm)

Other types:
    Device (namedtuple)

Other constants and variables:
    MOVE_TIME_BUFFER_S (float) = 0.5
"""
# Standard library imports
from __future__ import annotations
import logging
from typing import Sequence

# Third party imports
import numpy as np

# Local application imports
from ....core.position import Position
from ..jointed_utils import RobotArm
from .dobot_device import DobotDevice

logger = logging.getLogger(__name__)
logger.debug(f"Import: OK <{__name__}>")

MOVEMENT_BUFFER = 0.5
MOVEMENT_TIMEOUT = 30


class Dobot(RobotArm):
    """
    Abstract Base Class (ABC) for Dobot objects. Dobot provides controls for articulated robots from Dobot.
    ABC cannot be instantiated, and must be subclassed with abstract methods implemented before use.
    
    ### Constructor
    Args:
        `ip_address` (str): IP address of Dobot
        `attachment_name` (str, optional): name of attachment. Defaults to None.
    
    ### Attributes
    - `attachment` (DobotAttachment): attached Dobot tool
    
    ### Properties
    - `dashboard` (dobot_api_dashboard): connection to status and signal control
    - `feedback` (dobot_api_feedback): connection to movement controls
    - `ip_address` (str): IP address of Dobot
    
    ### Methods
    #### Abstract
    - `isFeasible`: checks and returns whether the target coordinate is feasible
    #### Public
    - `calibrate`: calibrate the internal and external coordinate systems, then verify points
    - `disconnect`: disconnect from device
    - `getConfigSettings`: retrieve the robot's configuration
    - `moveBy`: relative Cartesian movement and tool orientation, using robot coordinates
    - `moveTo`: absolute Cartesian movement and tool orientation, using robot coordinates
    - `jointMoveBy`: relative joint movement
    - `jointMoveTo`: absolute joint movement
    - `reset`: reset the robot
    - `setSpeed`: set the speed of the robot
    - `shutdown`: shutdown procedure for tool
    - `stop`: halt robot movement
    - `toggleAttachment`: couple or remove Dobot attachment that interfaces with Dobot's digital output
    - `toggleCalibration`: enter or exit calibration mode, with a sharp point implement for alignment
    """
    
    def __init__(self, 
        host: str,
        *,
        device_type_name: str = 'DobotDevice',
        movement_buffer: int|None = None,
        movement_timeout: int|None = None,
        verbose: bool = False, 
        **kwargs
    ):
        """
        Instantiate the class

        Args:
            ip_address (str): IP address of Dobot
            attachment_name (str, optional): name of attachment. Defaults to None.
        """
        device_type = globals().get(device_type_name, DobotDevice)
        super().__init__(device_type=device_type, host=host, verbose=verbose, **kwargs)
        assert isinstance(self.device, DobotDevice), "Ensure device is of type `DobotDevice`"
        self.device: DobotDevice = self.device
        self.movement_buffer = movement_buffer if movement_buffer is not None else MOVEMENT_BUFFER
        self.movement_timeout = movement_timeout if movement_timeout is not None else MOVEMENT_TIMEOUT
        self.settings = dict()
        
        self.connect()
        return
    
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
        assert isinstance(by, (Sequence, Position, np.ndarray)), f"Ensure `by` is a Sequence or Position or np.ndarray object"
        if isinstance(by, (Sequence, np.ndarray)):
            assert len(by) == 3, f"Ensure `by` is a 3-element sequence for x,y,z"
        move_by = by if isinstance(by, Position) else Position(by)
        speed_factor = self.speed_factor if speed_factor is None else speed_factor
        self._logger.info(f"Move By | {move_by} at speed factor {speed_factor}")
        
        # Convert to robot coordinates
        if robot:
            move_by = move_by
        else:
            inv_tool_offset = self.tool_offset.invert()
            inv_calibrated_offset = self.calibrated_offset.invert()
            by_coordinates = inv_tool_offset.Rotation.apply(inv_calibrated_offset.Rotation.apply(move_by.coordinates))
            by_rotation = inv_tool_offset.Rotation * inv_calibrated_offset.Rotation * move_by.Rotation
            move_by = Position(by_coordinates, by_rotation)
        if not self.isFeasible(self.position.coordinates + move_by.coordinates, external=False, tool_offset=False):
            self._logger.warning(f"Target movement {move_by} is not feasible")
            return self.robot_position if robot else self.worktool_position
        
        # Implementation of relative movement
        self.device.RelMovL(*move_by.coordinates, move_by.Rotation.as_euler('xyz', degrees=True)[-1])
        ... # wait time
        
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
        assert isinstance(to, (Sequence, Position, np.ndarray)), f"Ensure `to` is a Sequence or Position or np.ndarray object"
        if isinstance(to, (Sequence, np.ndarray)):
            assert len(to) == 3, f"Ensure `to` is a 3-element sequence for x,y,z"
        move_to = to if isinstance(to, Position) else Position(to)
        speed_factor = self.speed_factor if speed_factor is None else speed_factor
        self._logger.info(f"Move To | {move_to} at speed factor {speed_factor}")
        
        # Convert to robot coordinates
        move_to = move_to if robot else self.transformToolToRobot(self.transformWorkToRobot(move_to))
        if not self.isFeasible(move_to.coordinates, external=False, tool_offset=False):
            self._logger.warning(f"Target position {move_to} is not feasible")
            return self.robot_position if robot else self.worktool_position
        
        # Implementation of absolute movement
        self.device.MovJ(*move_to.coordinates, move_to.Rotation.as_euler('xyz', degrees=True)[-1])
        ... # wait time
        
        # Update position
        self.updateRobotPosition(to=move_to)
        return self.robot_position if robot else self.worktool_position
    
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
        if not self.isFeasibleJoint(self.joint_position + joint_move_by):
            self._logger.warning(f"Target movement {joint_move_by} is not feasible")
            return self.joint_position
        
        # Implementation of relative movement
        self.device.RelMovJ(*joint_move_by[:3], joint_move_by[-1])
        ... # wait time
        
        # Update position
        self.updateJointPosition(by=joint_move_by)
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
            return self.joint_position
        
        # Implementation of absolute movement
        self.device.JointMovJ(*joint_move_to[:3], joint_move_to[-1])
        ... # wait time
        
        # Update position
        self.updateJointPosition(to=joint_move_to)
        return self.joint_position

    def reset(self):
        """Reset the robot"""
        return self.device.reset()
    
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
    
    def shutdown(self):
        """Shutdown procedure for tool"""
        self.device.ResetRobot()
        self.device.DisableRobot()
        return super().shutdown()
    
    def stop(self):
        """Halt robot movement"""
        self.device.ResetRobot()
        return
    