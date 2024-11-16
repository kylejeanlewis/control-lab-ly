# -*- coding: utf-8 -*-
"""
This module holds the base class for cartesian mover tools.

## Classes:
    `Gantry`: Gantry provides controls for a general cartesian robot.

<i>Documentation last updated: 2024-11-14</i>
"""
# Standard library imports
from __future__ import annotations
import logging
from typing import final, Sequence

# Third party imports
import numpy as np

# Local application imports
from ...core.position import BoundingBox, Position, Deck
from ..gcode_utils import GCode

logger = logging.getLogger("controllably.Move")
logger.debug(f"Import: OK <{__name__}>")

@final
class Gantry(GCode):
    """
    Gantry provides controls for a general cartesian robot.
    
    ### Constructor
        `port` (str): serial port address
        `limits` (Sequence[Sequence[float]], optional): lower and upper limits of gantry, in terms of robot coordinate system. Defaults to ((0, 0, 0), (0, 0, 0)).
        `robot_position` (Position, optional): current position of the robot. Defaults to Position().
        `home_position` (Position, optional): home position of the robot in terms of robot coordinate system. Defaults to Position().
        `tool_offset` (Position, optional): tool offset from robot to end effector. Defaults to Position().
        `calibrated_offset` (Position, optional): calibrated offset from robot to work position. Defaults to Position().
        `scale` (float, optional): factor to scale the basis vectors by. Defaults to 1.0.
        `deck` (Deck, optional): Deck object for workspace. Defaults to None.
        `workspace` (BoundingBox, optional): workspace bounding box. Defaults to None.
        `safe_height` (float, optional): safe height in terms of robot coordinate system. Defaults to None.
        `saved_positions` (dict, optional): dictionary of saved positions. Defaults to dict().
        `speed_max` (float, optional): maximum speed of robot in mm/min. Defaults to 600.
        `device_type_name` (str, optional): name of the device type. Defaults to 'GRBL'.
        `baudrate` (int, optional): baudrate. Defaults to 115200.
        `movement_buffer` (Optional[int], optional): buffer for movement. Defaults to None.
        `movement_timeout` (Optional[int], optional): timeout for movement. Defaults to None.
        `verbose` (bool, optional): verbosity of class. Defaults to False.
        `simulation` (bool, optional): whether to simulate. Defaults to False.
        
    ### Attributes and properties
        `limits` (np.ndarray): lower and upper limits of gantry
        `movement_buffer` (int): buffer time after movement
        `movement_timeout` (int): timeout for movement
        `connection_details` (dict): connection details for the device
        `device` (Device): device object that communicates with physical tool
        `flags` (SimpleNamespace[str, bool]): flags for the class
        `is_busy` (bool): whether the device is busy
        `is_connected` (bool): whether the device is connected
        `verbose` (bool): verbosity of class
        `deck` (Deck): Deck object for workspace
        `workspace` (BoundingBox): workspace bounding box
        `safe_height` (float): safe height in terms of robot coordinate system
        `saved_positions` (dict): dictionary of saved positions
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
        
    ### Methods
        `query`: query the device
        `toggleCoolantValve`: toggle the coolant valve
        `connect`: connect to the device
        `disconnect`: disconnect from the device
        `resetFlags`: reset all flags to class attribute `_default_flags`
        `shutdown`: shutdown procedure for tool
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
        `rotateBy`: rotate the robot by target direction
        `rotateTo`: rotate the robot to target orientation
        `rotateRobotTo`: rotate the robot to target orientation
        `rotateToolTo`: rotate the tool end effector to target orientation
        `safeMoveTo`: safe version of moveTo by moving to safe height first
        `setSafeHeight`: set safe height for robot
        `setSpeedFactor`: set the speed factor of the robot
        `setToolOffset`: set the tool offset of the robot
        `updateRobotPosition`: update the robot position
        `transformRobotToTool`: transform robot coordinates to tool coordinates
        `transformRobotToWork`: transform robot coordinates to work coordinates
        `transformToolToRobot`: transform tool coordinates to robot coordinates
        `transformWorkToRobot`: transform work coordinates to robot coordinates
        `calibrate`: calibrate the internal and external coordinate systems
    """
    
    def __init__(self, 
        port: str,
        limits: Sequence[Sequence[float]] = ((0, 0, 0), (0, 0, 0)),     # in terms of robot coordinate system
        *, 
        robot_position: Position = Position(),
        home_position: Position = Position(),                           # in terms of robot coordinate system
        tool_offset: Position = Position(),
        calibrated_offset: Position = Position(),
        scale: float = 1.0,
        deck: Deck|None = None,
        safe_height: float|None = None,                                 # in terms of robot coordinate system
        saved_positions: dict = dict(),                     # in terms of robot coordinate system
        speed_max: float|None = None,                                   # in mm/min
        device_type_name: str = 'GRBL',
        baudrate: int = 115200, 
        movement_buffer: int|None = None,
        movement_timeout: int|None = None,
        verbose: bool = False, 
        simulation: bool = False,
        **kwargs
    ):
        workspace = BoundingBox(buffer=limits)
        _speed_max = speed_max if speed_max is not None else 600
        super().__init__(
            port=port, baudrate=baudrate, 
            robot_position=robot_position, home_position=home_position,
            tool_offset=tool_offset, calibrated_offset=calibrated_offset, scale=scale, 
            deck=deck, workspace=workspace, safe_height=safe_height, saved_positions=saved_positions,
            speed_max=_speed_max, device_type_name=device_type_name, movement_buffer=movement_buffer, 
            movement_timeout=movement_timeout, verbose=verbose, simulation=simulation,
            **kwargs
        )
        
        self.connect()
        self.home()
        
        settings = self.settings
        # Set limits if none provided
        if not any([any(l) for l in limits]):
            coordinates = self.device._home_offset
            device_limits = np.array([settings.get('limit_x',0),settings.get('limit_y',0),settings.get('limit_z',0)])
            device_limits = device_limits * (coordinates/abs(coordinates)) if any(coordinates) else device_limits
            limits = np.array([coordinates-self.device._home_offset,device_limits])
            limits = np.array([limits.min(axis=0),limits.max(axis=0)])
            self.workspace = BoundingBox(buffer=limits)
        
        # Set maximum speed if none provided
        if speed_max is None:
            speed_max = max([settings.get('max_speed_x',0),settings.get('max_speed_y',0),settings.get('max_speed_z',0)])
            self._speed_max = 600 if speed_max <= 0 else speed_max
        return
    
    @property
    def limits(self) -> np.ndarray:
        """Lower and upper limits of gantry"""
        return self.workspace.buffer
