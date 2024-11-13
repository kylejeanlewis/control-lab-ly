# -*- coding: utf-8 -*-
"""
This module holds the base class for mover tools.

Classes:
    Mover (ABC)
"""
# Standard library imports
from __future__ import annotations
from abc import abstractmethod
from copy import deepcopy
import json
import logging
from types import SimpleNamespace
from typing import Sequence, Any

import math

# Third party imports
import numpy as np
from scipy.spatial.transform import Rotation

# Local application imports
from ..core.connection import DeviceFactory, Device
from ..core.position import Deck, Position, get_transform, BoundingBox

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.debug(f"Import: OK <{__name__}>")

class Mover:
    """
    Abstract Base Class (ABC) for Mover objects (i.e. tools that move objects in space).
    ABC cannot be instantiated, and must be subclassed with abstract methods implemented before use.
    
    ### Constructor
    Args:
        `coordinates` (tuple[float], optional): current coordinates of the robot. Defaults to (0,0,0).
        `deck` (Layout.Deck, optional): Deck object for workspace. Defaults to Layout.Deck().
        `home_coordinates` (tuple[float], optional): home coordinates for the robot. Defaults to (0,0,0).
        `home_orientation` (tuple[float], optional): home orientation for the robot. Defaults to (0,0,0).
        `implement_offset` (tuple[float], optional): transformation (translation) vector to get from end effector to tool tip. Defaults to (0,0,0).
        `orientate_matrix` (np.ndarray, optional): transformation (rotation) matrix to get from robot to workspace. Defaults to np.identity(3).
        `orientation` (tuple[float], optional): current orientation of the robot. Defaults to (0,0,0).
        `scale` (float, optional): factor to scale the basis vectors by. Defaults to 1.
        `speed_max` (dict[str, float], optional): dictionary of robot maximum speeds. Defaults to dict(general=1).
        `speed_factor` (float, optional): fraction of maximum speed to travel at. Defaults to 1.
        `translate_vector` (tuple[float], optional): transformation (translation) vector to get from robot to end effector. Defaults to (0,0,0).
        `verbose` (bool, optional): verbosity of class. Defaults to False.
    
    ### Attributes
    - `connection_details` (dict): dictionary of connection details (e.g. COM port / IP address)
    - `deck` (Layout.Deck): Deck object for workspace
    - `device` (Callable): device object that communicates with physical tool
    - `flags` (dict[str, bool]): keywords paired with boolean flags
    - `heights` (dict[str, float]): specified height names and values
    - `verbose` (bool): verbosity of class
    
    ### Properties
    - `coordinates` (np.ndarray): current coordinates of the robot
    - `home_coordinates` (np.ndarray): home coordinates for the robot
    - `home_orientation` (np.ndarray): home orientation for the robot
    - `implement_offset` (np.ndarray): transformation (translation) vector to get from end effector to tool tip
    - `max_speeds` (np.ndarray): maximum speed(s) of robot
    - `orientate_matrix` (np.ndarray): transformation (rotation) matrix to get from robot to workspace
    - `orientation` (np.ndarray): current orientation of the robot
    - `position` (tuple[np.ndarray]): 2-uple of (coordinates, orientation)
    - `scale` (float): factor to scale the basis vectors by
    - `speed` (float): travel speed of robot
    - `speed_factor` (float): fraction of maximum travel speed of robot
    - `tool_position` (tuple[np.ndarray]): 2-uple of tool tip (coordinates, orientation)
    - `translate_vector` (np.ndarray): transformation (translation) vector to get from robot to end effector
    - `user_position` (tuple[np.ndarray]): 2-uple of user-defined workspace (coordinates, orientation)
    - `workspace_position` (tuple[np.ndarray]): 2-uple of workspace (coordinates, orientation)
    
    ### Methods
    #### Abstract
    - `disconnect`: disconnect from device
    - `home`: make the robot go home
    - `isFeasible`: checks and returns whether the target coordinates is feasible
    - `moveBy`: move the robot by target direction
    - `moveTo`: move the robot to target position
    - `reset`: reset the robot
    - `setSpeed`: set the speed of the robot
    - `setSpeedFactor`: set the speed factor of the robot
    - `shutdown`: shutdown procedure for tool
    - `stop`: halt robot movement
    - `_connect`: connection procedure for tool
    #### Public
    - `calibrate`: calibrate the internal and external coordinate systems
    - `connect`: establish connection with device
    - `getConfigSettings`: retrieve the robot's configuration
    - `isBusy`: checks and returns whether the device is busy
    - `isConnected`: checks and returns whether the device is connected
    - `loadDeck`: load Labware objects onto the deck from file or dictionary
    - `move`: move the robot in a specific axis by a specific value
    - `resetFlags`: reset all flags to class attribute `_default_flags`
    - `safeMoveTo`: safe version of moveTo by moving in Z-axis first
    - `setFlag`: set flags by using keyword arguments
    - `setHeight`: set predefined heights using keyword arguments
    - `setImplementOffset`: set offset of attached implement, then home if desired
    - `updatePosition`: update attributes to current position
    """
    
    _default_flags: SimpleNamespace[str,bool] = SimpleNamespace(busy=False, verbose=False)
    def __init__(self,
        *,
        robot_position: Position = Position(),
        home_position: Position = Position(),               # in terms of robot coordinate system
        tool_offset: Position = Position(),
        calibrated_offset: Position = Position(),
        scale: float = 1.0,
        deck: Deck|None = None,
        workspace: BoundingBox|None = None,
        safe_height: float|None = None,                     # in terms of robot coordinate system
        speed_max: float = 600,                             # in mm/min
        verbose:bool = False, 
        **kwargs
    ):
        """
        Instantiate the class

        Args:
            verbose (bool, optional): verbosity of class. Defaults to False.
        """
        self.device: Device = kwargs.get('device', DeviceFactory.createDeviceFromDict(kwargs))
        self.flags: SimpleNamespace = deepcopy(self._default_flags)
        self.verbose = verbose
        
        # Category specific attributes
        self.deck: Deck = deck
        self.workspace: BoundingBox = workspace
        self.safe_height: float = safe_height if safe_height is not None else home_position.z
        self.saved_positions: dict = dict()
        
        self._robot_position = robot_position
        self._home_position = home_position
        self._tool_offset = tool_offset
        self._calibrated_offset = calibrated_offset
        self._scale = scale
        
        self._speed_factor = 1.0
        self._speed_max = speed_max
        return
    
    def __del__(self):
        self.shutdown()
        return
    
    @property
    def connection_details(self) -> dict:
        """Get connection details"""
        return self.device.connection_details
    
    @property
    def is_busy(self) -> bool:
        """Check and return whether the device is busy"""
        return self.flags.busy
    
    @property
    def is_connected(self) -> bool:
        """Get connection status"""
        return self.device.is_connected
    
    @property
    def verbose(self) -> bool:
        """Get verbosity of class"""
        return self.flags.verbose
    @verbose.setter
    def verbose(self, value:bool):
        """Set verbosity of class"""
        assert isinstance(value,bool), "Ensure assigned verbosity is boolean"
        self.flags.verbose = value
        self.device.verbose = value
        level = logging.INFO if value else logging.WARNING
        logger.setLevel(level)
        for handler in logger.handlers:
            if isinstance(handler, type(logging.StreamHandler())):
                handler.setLevel(level)
        return
    
    def connect(self):
        """Reconnect to device using existing connection details"""
        self.device.connect()
        return
    
    def disconnect(self):
        """Disconnect from device"""
        self.device.disconnect()
        return
    
    def resetFlags(self):
        """Reset all flags to class attribute `_default_flags`"""
        self.flags = deepcopy(self._default_flags)
        return
    
    def shutdown(self):
        """Shutdown procedure for tool"""
        self.disconnect()
        self.resetFlags()
        return

    # Category specific properties and methods
    @property
    def robot_position(self) -> Position:
        """Current position of the robot"""
        return self._robot_position
    
    @property
    def home_position(self) -> Position:
        """Home position of the robot"""
        return self._home_position
    
    @property
    def tool_offset(self) -> Position:
        """Tool offset from robot to end effector"""
        return self._tool_offset
    
    @property
    def calibrated_offset(self) -> Position:
        """Calibrated offset from robot to work position"""
        return self._calibrated_offset
    
    @property
    def tool_position(self) -> Position:
        """Robot position of the tool end effector"""
        return self.transformRobotToTool(self.robot_position, self.tool_offset)
    
    @property
    def work_position(self) -> Position:
        """Work position of the robot"""
        return self.transformRobotToWork(self.robot_position, self.calibrated_offset, self.scale)
    
    @property
    def worktool_position(self) -> Position:
        """Work position of the tool end effector"""
        return self.transformRobotToWork(self.tool_position, self.calibrated_offset, self.scale)
    
    @property
    def position(self) -> Position:
        """Work position of the tool end effector"""
        return self.worktool_position
    
    @property
    def scale(self) -> float:
        """Factor to scale the basis vectors by"""
        return self._scale
    
    @property
    def speed(self) -> float:
        """Travel speed of robot"""
        return self.speed_factor * self.speed_max
    
    @property
    def speed_factor(self) -> float:
        """Fraction of maximum travel speed of robot"""
        return self._speed_factor
    @speed_factor.setter
    def speed_factor(self, value: float):
        assert isinstance(value, float) and 0<value<=1, "Ensure assigned speed factor is a float between 0 and 1"
        self._speed_factor = value
        return
    
    @property
    def speed_max(self) -> dict[str, float]:
        """Maximum speed(s) of robot"""
        return self._speed_max
    @speed_max.setter
    def speed_max(self, value: float):
        """Set the speed of the robot"""
        assert isinstance(value, float) and value>0, "Ensure assigned speed is a positive float"
        self._speed_max = value
        return
    
    def halt(self) -> Position:
        raise NotImplementedError
    
    def home(self, axis: str|None = None) -> Position:
        raise NotImplementedError
    
    def isFeasible(self, coordinates: Sequence[float], external: bool = True, tool_offset:bool = True) -> bool:
        position = Position(coordinates)
        if external:
            ex_pos = position
            in_pos = self.transformWorkToRobot(ex_pos, self.calibrated_offset, self.scale)
            in_pos = self.transformToolToRobot(in_pos, self.tool_offset) if tool_offset else in_pos
        else:
            in_pos = position
            ex_pos = self.transformRobotToTool(in_pos, self.tool_offset) if tool_offset else in_pos
            ex_pos = self.transformRobotToWork(ex_pos, self.calibrated_offset, self.scale)
        within_range = True
        if isinstance(self.workspace, BoundingBox):
            within_range = self.workspace.contains(in_pos.coordinates)
        deck_safe = True
        if isinstance(self.deck, Deck):
            deck_safe = not self.deck.isExcluded(ex_pos.coordinates)
        return all([within_range, deck_safe])
    
    def loadDeck(self, deck: Deck):
        assert isinstance(deck, Deck), f"Ensure input is a Deck object"
        self.deck = deck
        deck_positions = deck.getAllPositions()
        deck_positions_namespace = json.loads(json.dumps(deck_positions), object_hook=lambda item: SimpleNamespace(**item))
        self.saved_positions['deck_positions_namespace'] = deck_positions_namespace
        try:
            self.setSafeHeight(height=self.safe_height)
        except AssertionError as e:
            logger.warning(f"Error setting safe height: {self.safe_height}")
            logger.warning(e)
        return
    
    def loadDeckFromDict(self, details:dict[str, Any]):
        deck = Deck.fromConfigs(details=details)
        return self.loadDeck(deck)
    
    def loadDeckFromFile(self, deck_file:str):
        deck = Deck.fromFile(deck_file=deck_file)
        return self.loadDeck(deck)
    
    def move(self,
        axis: str,
        by: float,
        speed_factor: float|None = None,
        *,
        jog: bool = False,
        rapid: bool = False
    ) -> Position:
        assert axis.lower() in 'xyzabc', f"Ensure axis is one of 'x,y,z,a,b,c'"
        default = dict(x=0, y=0, z=0, a=0, b=0, c=0)
        default.update({axis: by})
        vector = np.array([default[k] for k in 'xyz'])
        rotation = np.array([default[k] for k in 'abc'])
        move_position = Position(vector, Rotation.from_euler('zyx', rotation, degrees=True))
        return self.moveBy(by=move_position, speed_factor=speed_factor, jog=jog, rapid=rapid)
        
    def moveBy(self,
        by: Sequence[float]|Position|np.ndarray,
        speed_factor: float|None = None,
        *,
        jog: bool = False,
        rapid: bool = False,
        robot: bool = False
    ) -> Position:
        assert isinstance(by, (Sequence, Position, np.ndarray)), f"Ensure `by` is a Sequence or Position or np.ndarray object"
        if isinstance(by, (Sequence, np.ndarray)):
            assert len(by) == 3, f"Ensure `by` is a 3-element sequence for x,y,z"
        move_by = by if isinstance(by, Position) else Position(by)
        logger.debug(f"Moving by {move_by} at speed factor {speed_factor}")
        
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
            logger.warning(f"Target movement {move_by} is not feasible")
            return self.robot_position if robot else self.tool_position
        
        # Implementation of relative movement
        ...
        
        # Update position
        self.updateRobotPosition(by=move_by)
        raise NotImplementedError
        return self.robot_position if robot else self.tool_position

    def moveTo(self,
        to: Sequence[float]|Position|np.ndarray,
        speed_factor: float|None = None,
        *,
        jog: bool = False,
        rapid: bool = False,
        robot: bool = False
    ) -> Position:
        assert isinstance(to, (Sequence, Position, np.ndarray)), f"Ensure `to` is a Sequence or Position or np.ndarray object"
        if isinstance(to, (Sequence, np.ndarray)):
            assert len(to) == 3, f"Ensure `to` is a 3-element sequence for x,y,z"
        move_to = to if isinstance(to, Position) else Position(to)
        logger.debug(f"Moving to {move_to} at speed factor {speed_factor}")
        
        # Convert to robot coordinates
        move_to = move_to if robot else self.transformToolToRobot(self.transformWorkToRobot(move_to))
        if not self.isFeasible(move_to.coordinates, external=False, tool_offset=False):
            logger.warning(f"Target position {move_to} is not feasible")
            return self.robot_position if robot else self.tool_position
        
        # Implementation of absolute movement
        ...
        
        # Update position
        self.updateRobotPosition(to=move_to)
        raise NotImplementedError
        return self.robot_position if robot else self.tool_position
    
    def moveToSafeHeight(self,speed_factor: float|None = None) -> Position:
        # Move up to safe height
        current_position = self.robot_position
        safe_position = Position(current_position.coordinates[:2]+[self.safe_height], current_position.Rotation)
        return self.moveTo(safe_position, speed_factor)
    
    def moveRobotTo(self,
        to: Sequence[float]|Position,
        speed_factor: float|None = None,
        *,
        jog: bool = False
    ) -> Position:
        return self.moveTo(to=to, speed_factor=speed_factor, jog=jog, robot=True)
        
    def moveToolTo(self,
        to: Sequence[float]|Position,
        speed_factor: float|None = None,
        *,
        jog: bool = False
    ) -> Position:
        return self.moveTo(to=to, speed_factor=speed_factor, jog=jog, robot=False)
    
    def reset(self):
        raise NotImplementedError
    
    def rotate(self,
        axis: str,
        by: float,
        speed_factor: float|None = None,
        *,
        jog: bool = False
    ) -> Rotation:
        assert axis.lower() in 'abc', f"Ensure axis is one of 'a,b,c'"
        default = dict(a=0, b=0, c=0)
        default.update({axis: by})
        rotate_angles = np.array([default[k] for k in 'abc'])
        rotation = Rotation.from_euler('zyx', rotate_angles, degrees=True)
        return self.rotateBy(by=rotation, speed_factor=speed_factor, jog=jog)
        
    def rotateBy(self,
        by: Sequence[float]|Rotation|np.ndarray,
        speed_factor: float|None = None,
        *,
        jog: bool = False,
        robot: bool = False
    ) -> Rotation:
        assert isinstance(by, (Sequence, Rotation, np.ndarray)), f"Ensure `by` is a Sequence or Rotation or np.ndarray object"
        if isinstance(by, (Sequence, np.ndarray)):
            assert len(by) == 3, f"Ensure `by` is a 3-element sequence for c,b,a"
        rotate_by = by if isinstance(by, Rotation) else Rotation.from_euler('zyx', by, degrees=True)
        logger.debug(f"Rotating by {rotate_by} at speed factor {speed_factor}")
        
        # Convert to robot coordinates
        rotate_by = rotate_by               # not affected by robot or tool coordinates for rotation
        
        # Implementation of relative rotation
        ...
        
        # Update position
        self.updateRobotPosition(by=rotate_by)
        raise NotImplementedError
        return self.robot_position.Rotation if robot else self.tool_position.Rotation
        
    def rotateTo(self,
        to: Sequence[float]|Rotation|np.ndarray,
        speed_factor: float|None = None,
        *,
        jog: bool = False,
        robot: bool = False
    ) -> Rotation:
        assert isinstance(to, (Sequence, Rotation, np.ndarray)), f"Ensure `to` is a Sequence or Rotation or np.ndarray object"
        if isinstance(to, (Sequence, np.ndarray)):
            assert len(to) == 3, f"Ensure `to` is a 3-element sequence for c,b,a"
        rotate_to = to if isinstance(to, Rotation) else Rotation.from_euler('zyx', to, degrees=True)
        logger.debug(f"Rotating to {rotate_to} at speed factor {speed_factor}")
        
        # Convert to robot coordinates
        if robot:
            rotate_to = rotate_to
        else:
            rotate_to = self.tool_position.Rotation * self.calibrated_offset.Rotation * rotate_to
        
        # Implementation of absolute rotation
        ...
        
        # Update position
        self.updateRobotPosition(to=rotate_to)
        raise NotImplementedError
        return self.robot_position.Rotation if robot else self.tool_position.Rotation
        
    def rotateRobotTo(self,
        to: Sequence[float]|Rotation,
        speed_factor: float|None = None,
        *,
        jog: bool = False
    ) -> Rotation:
        return self.rotateTo(to=to, speed_factor=speed_factor, robot=True)
    
    def rotateToolTo(self,
        to: Sequence[float]|Rotation,
        speed_factor: float|None = None,
        *,
        jog: bool = False
    ) -> Rotation:
        return self.rotateTo(to=to, speed_factor=speed_factor, robot=False)
    
    def safeMoveTo(self,
        to: Sequence[float]|Position|np.ndarray,
        speed_factor_lateral: float|None = None,
        speed_factor_up: float|None = None,
        speed_factor_down: float|None = None,
        *,
        jog: bool = False,
        rotation_before_lateral: bool = False,
        robot: bool = False
    ) -> Position:
        assert isinstance(to, (Sequence, Position, np.ndarray)), f"Ensure `to` is a Sequence or Position or np.ndarray object"
        if isinstance(to, (Sequence, np.ndarray)):
            assert len(to) == 3, f"Ensure `to` is a 3-element sequence for x,y,z"
        speed_factor_lateral = self.speed_factor if speed_factor_lateral is None else speed_factor_lateral
        speed_factor_up = self.speed_factor if speed_factor_up is None else speed_factor_up
        speed_factor_down = self.speed_factor if speed_factor_down is None else speed_factor_down
        
        # Move up to safe height
        self.moveToSafeHeight(speed_factor=speed_factor_up)
        
        # Move laterally to safe height above target position
        if isinstance(to,Position) and rotation_before_lateral:
            self.rotateTo(to=to.Rotation, speed_factor=speed_factor_lateral, robot=robot)
        
        current_coordinates = self.robot_position.coordinates if robot else self.tool_position.coordinates
        target_coordinates = to.coordinates if isinstance(to,Position) else to
        safe_target_coordinates = np.array([*target_coordinates[:2], current_coordinates[2]])
        self.moveTo(to=safe_target_coordinates, speed_factor=speed_factor_lateral, robot=robot)
        
        if isinstance(to,Position) and not rotation_before_lateral:
            self.rotateTo(to=to.Rotation, speed_factor=speed_factor_lateral, robot=robot)
        
        # Move down to target position
        self.moveTo(to=to, speed_factor=speed_factor_down, robot=robot)
        return self.robot_position if robot else self.tool_position
    
    def setSafeHeight(self, height: float):
        if isinstance(self.workspace, BoundingBox):
            assert (*self.workspace.reference[:2],height) in self.workspace, f"Ensure safe height is within workspace"
        if isinstance(self.deck, Deck):
            deck_heights = {name: max(bounds.bounds[:,2]) for name,bounds in self.deck.exclusion_zone.items()}
            heights_list = [height for height in deck_heights.values()]
            assert height > max(set(heights_list)), f"Ensure safe height is above all deck heights: {deck_heights}"
        self.safe_height = height
        return
    
    def setSpeedFactor(self, 
        speed_factor: float, 
        persist: bool = True
    ) -> tuple[float]:
        raise NotImplementedError
        
    def setToolOffset(self,
        offset: Sequence[float]|Position
    ) -> Position:
        old_tool_offset = self.tool_offset
        self._tool_offset = Position(offset)
        return old_tool_offset
    
    def updateRobotPosition(self, by: Position|Rotation|None = None, to: Position|Rotation|None = None) -> Position:
        assert (by is None) != (to is None), f"Ensure input only for one of `by` or `to`"
        if isinstance(by, Position):
            self._robot_position.translate(by.coordinates).orientate(by.Rotation)
        elif isinstance(to, Position):
            self._robot_position = to
        elif isinstance(by, Rotation):
            self._robot_position.orientate(by)
        elif isinstance(to, Rotation):
            self._robot_position.Rotation = to
        else:
            raise ValueError(f"Ensure input is of type Position or Rotation")
        return self.robot_position
        
    @staticmethod
    def calibrate(
        internal_points: np.ndarray,
        external_points: np.ndarray
    ) -> tuple[Position,float]:
        return get_transform(internal_points, external_points)
    
    @staticmethod
    def transformRobotToWork(
        internal_position: Position,
        offset: Position,
        scale: float = 1.0
    ) -> Position:
        translate = offset.coordinates
        rotate = offset.Rotation
        scale = scale
        # Translate-Rotate-Scale
        coordinates = scale*rotate.apply(translate+internal_position.coordinates)
        rotation = rotate * internal_position.Rotation
        return Position(coordinates, rotation)
    
    @staticmethod
    def transformWorkToRobot(
        external_position: Position,
        offset: Position,
        scale: float = 1.0
    ) -> Position:
        inv_scale = 1 / scale
        inv_offset = offset.invert()
        inv_rotate = inv_offset.Rotation
        inv_translate = inv_offset.coordinates
        # Invert: Scale-Rotate-Translate
        coordinates = inv_translate+inv_rotate.apply(inv_scale*external_position.coordinates)
        rotation = inv_rotate * external_position.Rotation
        return Position(coordinates, rotation)
    
    @staticmethod
    def transformRobotToTool(
        internal_position: Position,
        offset: Position
    ) -> Position:
        coordinates = internal_position.coordinates + offset.coordinates
        rotation = internal_position.rotation + offset.rotation
        return Position(coordinates, Rotation.from_euler('zyx', rotation, degrees=True))
    
    @staticmethod
    def transformToolToRobot(
        external_position: Position,
        offset: Position
    ) -> Position:
        coordinates = external_position.coordinates - offset.coordinates
        rotation = external_position.rotation - offset.rotation
        return Position(coordinates, Rotation.from_euler('zyx', rotation, degrees=True))
    
    @staticmethod
    def _calculate_travel_time(
        distance: float, 
        speed: float, 
        acceleration: float|None = None,
        deceleration: float|None = None
    ) -> float:
        """
        Calculate the travel time of motion

        Args:
            distance (float): distance (linear or angular) travelled
            speed (float): speed (linear or angular) of motion
            acceleration (float|None, optional): acceleration from target speed. Defaults to None.
            deceleration (float|None, optional): deceleration from target speed. Defaults to None.

        Returns:
            float: travel time in seconds
        """
        travel_time = 0
        speed2 = speed*speed
        accel_distance = 0 if not acceleration else speed2 / (2*acceleration)
        decel_distance = 0 if not deceleration else speed2 / (2*deceleration)
        ramp_distance = accel_distance + decel_distance
        if ramp_distance <= distance:
            travel_time = (distance - ramp_distance) / speed
            accel_time = 0 if not acceleration else speed / acceleration
            decel_time = 0 if not deceleration else speed / deceleration
            travel_time += (accel_time + decel_time)
        else:
            time2 = (2*distance)* (acceleration + deceleration)/(acceleration*deceleration)
            travel_time = time2**0.5
        travel_time = 0.0 if np.isnan(travel_time) else travel_time
        return travel_time
    
    @classmethod
    def _get_move_wait_time(cls, 
        distances: np.ndarray, 
        speeds: np.ndarray, 
        accels: np.ndarray|None = None
    ) -> float:
        """
        Get the amount of time to wait to complete movement

        Args:
            distances (np.ndarray): array of distances to travel
            speeds (np.ndarray): array of axis speeds
            accels (np.ndarray|None, optional): array of axis accelerations. Defaults to None.

        Returns:
            float: wait time to complete travel
        """
        accels = np.zeros(len(speeds)) if accels is None else accels
        times = [cls._calculate_travel_time(d,s,a,a) for d,s,a in zip(distances, speeds, accels)]
        move_time = max(times[:2]) + times[2]
        logger.debug(f'distances: {distances}')
        logger.debug(f'speeds: {speeds}')
        logger.debug(f'accels: {accels}')
        logger.debug(f'times: {times}')
        return move_time
    

    
class _Mover:
    
    _default_heights: dict[str, float] = {}
    _default_move_time_buffer: float = 0
    _place: str = '.'.join(__name__.split('.')[1:-1])
    def __init__(self, 
        coordinates: tuple[float] = (0,0,0),
        # deck: Layout.Deck = Layout.Deck(),
        home_coordinates: tuple[float] = (0,0,0),
        home_orientation: tuple[float] = (0,0,0),
        implement_offset: tuple[float] = (0,0,0),
        orientate_matrix: np.ndarray = np.identity(3),
        orientation: tuple[float] = (0,0,0),
        scale: float = 1.0,
        speed_max: dict[str, float] = dict(general=20),
        speed_factor: float = 1.0,
        translate_vector: tuple[float] = (0,0,0),
        verbose: bool = False,
        **kwargs
    ):
        """
        Instantiate the class

        Args:
            coordinates (tuple[float], optional): current coordinates of the robot. Defaults to (0,0,0).
            deck (Layout.Deck, optional): Deck object for workspace. Defaults to Layout.Deck().
            home_coordinates (tuple[float], optional): home coordinates for the robot. Defaults to (0,0,0).
            home_orientation (tuple[float], optional): home_orientation for the robot. Defaults to (0,0,0).
            implement_offset (tuple[float], optional): transformation (translation) vector to get from end effector to tool tip. Defaults to (0,0,0).
            orientate_matrix (np.ndarray, optional): transformation (rotation) matrix to get from robot to workspace. Defaults to np.identity(3).
            orientation (tuple[float], optional): current orientation of the robot. Defaults to (0,0,0).
            scale (float, optional): factor to scale the basis vectors by. Defaults to 1.0.
            speed_max (dict[str, float], optional): dictionary of robot maximum speeds. Defaults to dict(general=1).
            speed_factor (float, optional): fraction of maximum speed to travel at. Defaults to 1.0.
            translate_vector (tuple[float], optional): transformation (translation) vector to get from robot to end effector. Defaults to (0,0,0).
            verbose (bool, optional): verbosity of class. Defaults to False.
        """
        # self.deck = deck
        self._coordinates = coordinates
        self._orientation = orientation
        self._home_coordinates = home_coordinates
        self._home_orientation = home_orientation
        self._orientate_matrix = orientate_matrix
        self._translate_vector = translate_vector
        self._implement_offset = implement_offset
        self._scale = scale
        self._speed_max = speed_max
        self._speed_factor = speed_factor
        self._move_time_buffer = self._default_move_time_buffer
        
        self.connection_details = {}
        self.device = None
        self.flags = self._default_flags.copy()
        self.heights = self._default_heights.copy()
        self.max_feedrate = 100
        self.verbose = verbose
        return
    
    def __del__(self):
        self.shutdown()
        return
    
    @abstractmethod
    def disconnect(self):
        """Disconnect from device"""
        self.setFlag(connected=False)
        return
        
    @abstractmethod
    def home(self) -> bool:
        """Make the robot go home"""

    @abstractmethod
    def isFeasible(self, 
        coordinates: tuple[float], 
        transform_in: bool = False, 
        tool_offset: bool = False, 
        **kwargs
    ) -> bool:
        """
        Checks and returns whether the target coordinates is feasible

        Args:
            coordinates (tuple[float]): target coordinates
            transform_in (bool, optional): whether to convert to internal coordinates first. Defaults to False.
            tool_offset (bool, optional): whether to convert from tool tip coordinates first. Defaults to False.

        Returns:
            bool: whether the target coordinate is feasible
        """
        return not self.deck.isExcluded(self._transform_out(coordinates, tool_offset=True))
    
    @abstractmethod
    def moveBy(self, 
        vector: tuple[float] = (0,0,0), 
        angles: tuple[float] = (0,0,0), 
        speed_factor: float|None = None,
        **kwargs
    ) -> bool:
        """
        Move the robot by target direction

        Args:
            vector (tuple[float], optional): x,y,z vector to move in. Defaults to (0,0,0).
            angles (tuple[float], optional): a,b,c angles to move in. Defaults to (0,0,0).
            speed_factor (float|None, optional): speed factor of travel. Defaults to None.

        Returns:
            bool: whether the movement is successful
        """
        vector = np.array(vector)
        angles = np.array(angles)
        user_position = self.user_position
        new_coordinates = np.round( user_position[0] + np.array(vector) , 2)
        new_orientation = np.round( user_position[1] + np.array(angles) , 2)
        return self.moveTo(coordinates=new_coordinates, orientation=new_orientation, tool_offset=False, speed_factor=speed_factor, **kwargs)
 
    @abstractmethod
    def moveTo(self, 
        coordinates: tuple[float]|None = None, 
        orientation: tuple[float]|None = None, 
        tool_offset: bool = False, 
        speed_factor: float|None = None,
        **kwargs
    ) -> bool:
        """
        Move the robot to target position

        Args:
            coordinates (tuple[float]|None, optional): x,y,z coordinates to move to. Defaults to None.
            orientation (tuple[float]|None, optional): a,b,c orientation to move to. Defaults to None.
            tool_offset (bool, optional): whether to consider tooltip offset. Defaults to False.
            speed_factor (float|None, optional): speed factor of travel. Defaults to None.

        Returns:
            bool: whether movement is successful
        """
        if coordinates is None:
            coordinates = self.tool_position if tool_offset else self.user_position
        if orientation is None:
            orientation = self.orientation
        coordinates = self._transform_in(coordinates=coordinates, tool_offset=tool_offset)
        coordinates = np.array(coordinates)
        orientation = np.array(orientation)
        
        if not self.isFeasible(coordinates):
            return False
        self.coordinates = coordinates
        self.orientation = orientation
        speed_factor = self.speed_factor if speed_factor is None else speed_factor
        speed_change, prevailing_speed_factor = False, self.speed_factor
        if self.speed_factor != speed_factor:
            speed_change, prevailing_speed_factor = self.setSpeedFactor(speed_factor)
        if speed_change:
            self.setSpeedFactor(prevailing_speed_factor)
        return True
 
    @abstractmethod
    def reset(self):
        """Reset the robot"""
    
    @abstractmethod
    def setSpeed(self, speed:float) -> tuple[bool, float]:
        """
        Set the speed of the robot

        Args:
            speed (float): rate value (value range: 1~100)
            
        Returns:
            tuple[bool, float]: whether speed has changed; prevailing speed
        """
        
    @abstractmethod
    def setSpeedFactor(self, speed_factor:float) -> tuple[bool, float]:
        """
        Set the speed factor of the robot

        Args:
            speed_factor (float): speed ratio of max speed (value range: 0 to 1)
            
        Returns:
            tuple[bool, float]: whether speed has changed; prevailing speed factor
        """
    
    @abstractmethod
    def shutdown(self):
        """Shutdown procedure for tool"""
        self.disconnect()
        self.resetFlags()
        return
    
    @abstractmethod
    def stop(self):
        """Halt robot movement"""
 
    @abstractmethod
    def _connect(self, *args, **kwargs):
        """Connection procedure for tool"""
        self.connection_details = {}
        self.device = None
        self.setFlag(connected=True)
        return
 
    # Properties
    @property
    def coordinates(self) -> np.ndarray:
        """Current coordinates of the robot"""
        return np.array(self._coordinates)
    @coordinates.setter
    def coordinates(self, value):
        if len(value) != 3:
            raise Exception('Please input x,y,z coordinates')
        self._coordinates = tuple(value)
        return
    
    @property
    def home_coordinates(self) -> np.ndarray:
        """Home coordinates for the robot"""
        return np.array(self._home_coordinates)
    @home_coordinates.setter
    def home_coordinates(self, value):
        if len(value) != 3:
            raise Exception('Please input x,y,z coordinates')
        self._home_coordinates = tuple(value)
        return
    
    @property
    def home_orientation(self) -> np.ndarray:
        """Home orientation for the robot"""
        return np.array(self._home_orientation)
    @home_orientation.setter
    def home_orientation(self, value):
        if len(value) != 3:
            raise Exception('Please input a,b,c angles')
        self._home_orientation = tuple(value)
        return

    @property
    def implement_offset(self) -> np.ndarray:
        """Transformation (translation) vector to get from end effector to tool tip"""
        return np.array(self._implement_offset)
    @implement_offset.setter
    def implement_offset(self, value):
        if len(value) != 3:
            raise Exception('Please input x,y,z offset')
        self._implement_offset = tuple(value)
        return
    
    @property
    def max_speeds(self) -> np.ndarray:
        """Maximum speed(s) of robot"""
        speeds = [self._speed_max.get('general', 1)] * 6
        movement_L = ('x','y','z','a','b','c')
        movement_J = ('j1','j2','j3','j4','j5','j6')
        for s in self._speed_max:
            if type(s) is not str:
                break
            if s.lower() in movement_L:
                speeds = [self._speed_max.get(axis, np.nan) for axis in movement_L]
                break
            if s.lower() in movement_J:
                speeds = [self._speed_max.get(axis, np.nan) for axis in movement_J]
                break
        return np.array(speeds)
    
    @property
    def orientate_matrix(self) -> np.ndarray:
        """Transformation (rotation) matrix to get from robot to workspace"""
        return self._orientate_matrix
    @orientate_matrix.setter
    def orientate_matrix(self, value):
        if len(value) != 3 or any([len(row)!=3 for row in value]):
            raise Exception('Please input 3x3 matrix')
        self._orientate_matrix = np.array(value)
        return
    
    @property
    def orientation(self) -> np.ndarray:
        """Current orientation of the robot"""
        return np.array(self._orientation)
    @orientation.setter
    def orientation(self, value):
        if len(value) != 3:
            raise Exception('Please input a,b,c angles')
        self._orientation = tuple(value)
        return
    
    @property
    def position(self) -> tuple[np.ndarray]:
        """2-uple of (coordinates, orientation)"""
        return self.coordinates, self.orientation
    
    @property
    def scale(self) -> float:
        """Factor to scale the basis vectors by"""
        return self._scale
    @scale.setter
    def scale(self, value):
        if value <= 0:
            raise Exception('Please input a positive scale factor')
        self._scale = float(value)
        return
    
    @property
    def speed(self) -> float:
        """Travel speed of robot"""
        return self._speed_factor * self.max_feedrate
    
    @property
    def speed_factor(self) -> float:
        """Fraction of maximum travel speed of robot"""
        return self._speed_factor
 
    @property
    def tool_position(self) -> tuple[np.ndarray]:
        """2-uple of tool tip (coordinates, orientation)"""
        coordinates = self._transform_out(coordinates=self.coordinates, tool_offset=True)
        return np.array(coordinates), self.orientation
 
    @property
    def translate_vector(self) -> np.ndarray:
        """Transformation (translation) vector to get from robot to end effector"""
        return np.array(self._translate_vector)
    @translate_vector.setter
    def translate_vector(self, value):
        if len(value) != 3:
            raise Exception('Please input x,y,z vector')
        self._translate_vector = tuple(value)
        return
    
    @property
    def user_position(self) -> tuple[np.ndarray]:
        """2-uple of user-defined workspace (coordinates, orientation)"""
        coordinates = self._transform_out(coordinates=self.coordinates, tool_offset=False)
        return np.array(coordinates), self.orientation
    
    @property
    def workspace_position(self) -> tuple[np.ndarray]:
        """2-uple of workspace (coordinates, orientation). Alias for `user_position`"""
        return self.user_position
 
    def calibrate(self, 
        external_pt1: np.ndarray, 
        internal_pt1: np.ndarray, 
        external_pt2: np.ndarray, 
        internal_pt2: np.ndarray
    ):
        """
        Calibrate the internal and external coordinate systems

        Args:
            external_pt1 (np.ndarray): x,y,z coordinates of physical point 1
            internal_pt1 (np.ndarray): x,y,z coordinates of robot point 1
            external_pt2 (np.ndarray): x,y,z coordinates of physical point 2
            internal_pt2 (np.ndarray): x,y,z coordinates of robot point 2
        """
        external_pt1 = np.array(external_pt1)
        external_pt2 = np.array(external_pt2)
        internal_pt1 = np.array(internal_pt1)
        internal_pt2 = np.array(internal_pt2)
        
        space_vector = external_pt2 - external_pt1
        robot_vector = internal_pt2 - internal_pt1
        space_mag = np.linalg.norm(space_vector)
        robot_mag = np.linalg.norm(robot_vector)

        space_unit_vector = space_vector / space_mag
        robot_unit_vector = robot_vector / robot_mag
        dot_product = np.dot(robot_unit_vector, space_unit_vector)
        cross_product = np.cross(robot_unit_vector, space_unit_vector)

        cos_theta = dot_product
        sin_theta = math.copysign(np.linalg.norm(cross_product), cross_product[2])
        # rot_angle = math.acos(cos_theta) if sin_theta>0 else 2*math.pi - math.acos(cos_theta)
        rot_matrix = np.array([[cos_theta,-sin_theta,0],[sin_theta,cos_theta,0],[0,0,1]])
        
        self.orientate_matrix = rot_matrix
        self.translate_vector = np.matmul( self.orientate_matrix.T, external_pt2) - internal_pt2 - self.implement_offset
        self.scale = 1 # (space_mag / robot_mag)
        
        print(f'Orientate matrix:\n{self.orientate_matrix}')
        print(f'Translate vector: {self.translate_vector}')
        print(f'Scale factor: {self.scale}\n')
        return
    
    def connect(self):
        """Establish connection with device"""
        return self._connect(**self.connection_details)
    
    def getConfigSettings(self, attributes:list[str]) -> dict:
        """
        Retrieve the robot's configuration
        
        Args:
            attributes (list[str]): list of attributes to retrieve values from
        
        Returns:
            dict: dictionary of robot class and configuration
        """
        _class = str(type(self)).split("'")[1].split('.')[1]
        # settings = {k: v for k,v in self.__dict__.items() if k in attributes}
        settings = {key: self.__dict__.get(key) for key in attributes}
        for k,v in settings.items():
            if type(v) == tuple:
                settings[k] = {"tuple": list(v)}
            elif type(v) == np.ndarray:
                settings[k] = {"array": v.tolist()}
        return {"class": _class, "settings": settings}

    def isBusy(self) -> bool:
        """
        Checks and returns whether the device is busy
        
        Returns:
            bool: whether the device is busy
        """
        return self.flags.get('busy', False)
    
    def isConnected(self) -> bool:
        """
        Checks and returns whether the device is connected

        Returns:
            bool: whether the device is connected
        """
        if not self.flags.get('connected', False):
            print(f"{self.__class__} is not connected. Details: {self.connection_details}")
        return self.flags.get('connected', False)
 
    def loadDeck(self, layout_file:str|None = None, layout_dict:dict|None = None, **kwargs):
        """
        Load Labware objects onto the deck from file or dictionary
        
        Args:
            layout_file (str|None, optional): filename of layout .json file. Defaults to None.
            layout_dict (dict|None, optional): dictionary of layout. Defaults to None.
        """
        self.deck.loadLayout(layout_file=layout_file, layout_dict=layout_dict, **kwargs)
        return
    
    def move(self, axis:str, value:float, speed_factor:float|None = None, **kwargs) -> bool:
        """
        Move the robot in a specific axis by a specific value

        Args:
            axis (str): axis to move in (x,y,z,a,b,c,j1,j2,j3,j4,j5,j6)
            value (float): value to move by, in mm (translation) or degree (rotation)
            speed (float|None, optional): speed factor of travel. Defaults to None.

        Returns:
            bool: whether movement is successful
        """
        axis = axis.lower()
        movement_L = ('x','y','z','a','b','c')
        movement_J = ('j1','j2','j3','j4','j5','j6')
        success = False
        speed_factor = self.speed_factor if speed_factor is None else speed_factor
        speed_factor = 1 if speed_factor == 0 else speed_factor
        if axis in movement_L:
            values = {m:0 for m in movement_L}
            values[axis] = value
            vector = (values['x'], values['y'], values['z'])
            angles = (values['a'], values['b'], values['c'])
            success = self.moveBy(vector=vector, angles=angles, speed_factor=speed_factor, **kwargs)
        elif axis in movement_J:
            values = {m:0 for m in movement_J}
            values[axis] = value
            angles1 = (values['j1'], values['j2'], values['j3'])
            angles2 = (values['j4'], values['j5'], values['j6'])
            angles = angles1 + angles2
            success = self.moveBy(angles=angles, speed_factor=speed_factor, **kwargs)
        return success
              
    def resetFlags(self):
        """Reset all flags to class attribute `_default_flags`"""
        self.flags = self._default_flags.copy()
        return
    
    def safeMoveTo(self, 
        coordinates: tuple[float]|None = None, 
        orientation: tuple[float]|None = None, 
        tool_offset: bool = True, 
        travel_speed_ratio: float|None = None,
        ascent_speed_ratio: float|None = None, 
        descent_speed_ratio: float|None = None, 
        **kwargs
    ) -> bool:
        """
        Safe version of moveTo by moving in Z-axis first

        Args:
            coordinates (tuple[float]|None, optional): x,y,z coordinates to move to. Defaults to None.
            orientation (tuple[float]|None, optional): a,b,c orientation to move to. Defaults to None.
            tool_offset (bool, optional): whether to consider tooltip offset. Defaults to True.
            travel_speed_ratio (float|None, optional): speed ratio of lateral travel. Defaults to None.
            ascent_speed_ratio (float|None, optional): speed ratio of ascent. Defaults to None.
            descent_speed_ratio (float|None, optional): speed ratio of descent. Defaults to None.
            
        Returns:
            bool: whether movement is successful
        """
        ascent_speed_ratio = self.speed_factor if ascent_speed_ratio is None else ascent_speed_ratio
        descent_speed_ratio = self.speed_factor if descent_speed_ratio is None else descent_speed_ratio
        travel_speed_ratio = self.speed_factor if travel_speed_ratio is None else travel_speed_ratio
        success = []
        if coordinates is None:
            coordinates = self.tool_position if tool_offset else self.user_position
        if orientation is None:
            orientation = self.orientation
        coordinates = np.array(coordinates)
        orientation = np.array(orientation)
        
        # Move to safe height
        safe_height = self.home_coordinates[2] if 'safe' not in self.heights else self.heights['safe']
        ret = self.move('z', max(0, safe_height-self.coordinates[2]), speed_factor=ascent_speed_ratio)
        success.append(ret)
        
        # Move to correct XY-position
        intermediate_position = self.tool_position if tool_offset else self.user_position
        ret = self.moveTo(
            coordinates = [*coordinates[:2],float(intermediate_position[0][2])], 
            orientation = orientation, 
            tool_offset = tool_offset,
            speed_factor = travel_speed_ratio
        )
        success.append(ret)
        
        # Move down to target height
        ret = self.moveTo(
            coordinates = coordinates,
            orientation = orientation, 
            tool_offset = tool_offset,
            speed_factor = descent_speed_ratio
        )
        success.append(ret)
        return all(success)
        
    def setFlag(self, **kwargs):
        """
        Set flags by using keyword arguments

        Kwargs:
            key, value: (flag name, boolean) pairs
        """
        if not all([type(v)==bool for v in kwargs.values()]):
            print(kwargs)
            # raise ValueError("Ensure all assigned flag values are boolean.")
        self.flags.update(kwargs)
        return
    
    def setHeight(self, overwrite:bool = False, **kwargs):
        """
        Set predefined heights using keyword arguments

        Args:
            overwrite (bool, optional): whether to overwrite existing height. Defaults to False.
        
        Kwargs:
            key, value: (height name, float value) pairs
        
        Raises:
            ValueError: Ensure all assigned height values are floating point numbers.
        """
        for k,v in kwargs.items():
            kwargs[k] = float(v) if type(v) is int else v
        if not all([type(v)==float for v in kwargs.values()]):
            raise ValueError("Ensure all assigned height values are floating point numbers.")
        for key, value in kwargs.items():
            if key not in self.heights or overwrite:
                self.heights[key] = value
            elif not overwrite:
                print(f"Previously saved height '{key}': {self.heights[key]}\n")
                print(f"New height received: {value}")
                if input('Overwrite? [y/n]').lower() == 'n':
                    continue
                self.heights[key] = value
        return
    
    def setImplementOffset(self, implement_offset:tuple[float], home:bool = True):
        """
        Set offset of attached implement, then home if desired

        Args:
            implement_offset (tuple[float]): x,y,z offset of implement (i.e. vector pointing from end effector to tool tip)
            home (bool, optional): whether to home after setting implement offset. Defaults to True.
        """
        self.implement_offset = implement_offset
        if home:
            self.home()
        return
    
    def updatePosition(self, 
        coordinates: tuple[float]|None = None, 
        orientation: tuple[float]|None = None, 
        vector: tuple = (0,0,0), 
        angles: tuple = (0,0,0)
    ):
        """
        Update atributes to current position

        Args:
            coordinates (tuple[float]|None, optional): x,y,z coordinates. Defaults to None.
            orientation (tuple[float]|None, optional): a,b,c angles. Defaults to None.
            vector (tuple, optional): x,y,z vector. Defaults to (0,0,0).
            angles (tuple, optional): a,b,c angles. Defaults to (0,0,0).
        """
        if coordinates is not None:
            self.coordinates = coordinates
        else:
            self.coordinates = self.coordinates + np.array(vector)
            
        if orientation is not None:
            self.orientation = orientation
        else:
            self.orientation = self.orientation + np.array(angles)
        
        print(f'{self.coordinates}, {self.orientation}')
        return

    # Protected method(s)
    def _calculate_travel_time(self, 
        distance: float, 
        speed: float, 
        acceleration: float|None = None,
        deceleration: float|None = None
    ) -> float:
        """
        Calculate the travel time of motion

        Args:
            distance (float): distance (linear or angular) travelled
            speed (float): speed (linear or angular) of motion
            acceleration (float|None, optional): acceleration from target speed. Defaults to None.
            deceleration (float|None, optional): deceleration from target speed. Defaults to None.

        Returns:
            float: travel time in seconds
        """
        travel_time = 0
        speed2 = speed*speed
        accel_distance = 0 if not acceleration else speed2 / (2*acceleration)
        decel_distance = 0 if not deceleration else speed2 / (2*deceleration)
        ramp_distance = accel_distance + decel_distance
        if ramp_distance <= distance:
            travel_time = (distance - ramp_distance) / speed
            accel_time = 0 if not acceleration else speed / acceleration
            decel_time = 0 if not deceleration else speed / deceleration
            travel_time += (accel_time + decel_time)
            # print('more time')
        else:
            time2 = (2*distance)* (acceleration + deceleration)/(acceleration*deceleration)
            travel_time = time2**0.5
            # print('less time')
        travel_time = 0.0 if np.isnan(travel_time) else travel_time
        return travel_time
    
    def _diagnostic(self):
        """Run diagnostic test"""
        self.home()
        return
    
    def _get_move_wait_time(self, 
        distances: np.ndarray, 
        speeds: np.ndarray, 
        accels: np.ndarray|None = None
    ) -> float:
        """
        Get the amount of time to wait to complete movement

        Args:
            distances (np.ndarray): array of distances to travel
            speeds (np.ndarray): array of axis speeds
            accels (np.ndarray|None, optional): array of axis accelerations. Defaults to None.

        Returns:
            float: wait time to complete travel
        """
        accels = np.zeros(len(speeds)) if accels is None else accels
        times = [self._calculate_travel_time(d,s,a,a) for d,s,a in zip(distances, speeds, accels)]
        move_time = max(times[:2]) + times[2]
        if self.verbose:
            print(f'distances: {distances}')
            print(f'speeds: {speeds}')
            print(f'accels: {accels}')
            print(f'times: {times}')
        return move_time

    def _transform_in(self, 
        coordinates: tuple|None = None, 
        vector: tuple|None = None, 
        stretch: bool = False, 
        tool_offset: bool = False
    ) -> tuple[float]:
        """
        Order of transformations (scale, rotate, translate)

        Args:
            coordinates (tuple[float]|None, optional): position coordinates. Defaults to None.
            vector (tuple[float]|None, optional): vector. Defaults to None.
            stretch (bool, optional): whether to scale. Defaults to False.
            tool_offset (bool, optional): whether to consider tooltip offset. Defaults to False.

        Raises:
            RuntimeError: Only one of 'coordinates' or 'vector' can be passed
            
        Returns:
            tuple[float]: converted robot vector
        """
        to_be_transformed = None
        if coordinates is None and vector is not None:
            translate = np.zeros(3)
            to_be_transformed = vector
        elif coordinates is not None and vector is None:
            translate = (-1*self.translate_vector)
            translate = translate - self.implement_offset if tool_offset else translate
            to_be_transformed = coordinates
        else:
            raise RuntimeError("Input only either 'coordinates' or 'vector'.")
        scale = (1/self.scale) if stretch else 1
        return tuple( translate + np.matmul(self.orientate_matrix.T, scale * np.array(to_be_transformed)) )

    def _transform_out(self, 
        coordinates: tuple|None = None, 
        vector: tuple|None = None, 
        stretch: bool = False, 
        tool_offset: bool = False
    ) -> tuple[float]:
        """
        Order of transformations (translate, rotate, scale)

        Args:
            coordinates (tuple, optional): position coordinates. Defaults to None.
            vector (tuple, optional): vector. Defaults to None.
            stretch (bool, optional): whether to scale. Defaults to True.
            tool_offset (bool, optional): whether to consider tooltip offset. Defaults to False.

        Raises:
            RuntimeError: Only one of 'coordinates' or 'vector' can be passed
            
        Returns:
            tuple[float]: converted workspace vector
        """
        to_be_transformed = None
        if coordinates is None and vector is not None:
            translate = np.zeros(3)
            to_be_transformed = vector
        elif coordinates is not None and vector is None:
            translate = self.translate_vector
            translate = translate + self.implement_offset if tool_offset else translate
            to_be_transformed = coordinates
        else:
            raise RuntimeError("Input only either 'coordinates' or 'vector'.")
        scale = self.scale if stretch else 1
        return tuple( scale * np.matmul(self.orientate_matrix, translate + np.array(to_be_transformed)) )


    ### NOTE: DEPRECATE
    def getPosition(self):
        """
        Get robot coordinates and orientation.
        
        TO BE DEPRECATED: Use `position` attribute instead.
        
        Returns:
            tuple, tuple: x,y,z coordinates; a,b,c angles
        """
        print("`getPosition()` to be deprecated. Use `position` attribute instead.")
        return self.position
    
    def getToolPosition(self):
        """
        Retrieve coordinates of tool tip/end of implement.
        
        TO BE DEPRECATED: Use `tool_position` attribute instead.

        Returns:
            tuple, tuple: x,y,z coordinates; a,b,c angles
        """
        print("`getToolPosition()` to be deprecated. Use `tool_position` attribute instead.")
        return self.tool_position
    
    def getUserPosition(self):
        """
        Retrieve user-defined workspace coordinates.
        
        TO BE DEPRECATED: Use `user_position` attribute instead.

        Returns:
            tuple, tuple: x,y,z coordinates; a,b,c angles
        """
        print("`getUserPosition()` to be deprecated. Use `user_position` attribute instead.")
        return self.user_position
    
    def getWorkspacePosition(self):
        """
        Alias for getUserPosition.
        
        TO BE DEPRECATED: Use `workspace_position` attribute instead.

        Returns:
            tuple, tuple: x,y,z coordinates; a,b,c angles
        """
        print("`getWorkspacePosition()` to be deprecated. Use `workspace_position` attribute instead.")
        return self.workspace_position
