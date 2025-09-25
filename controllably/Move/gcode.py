# -*- coding: utf-8 -*-
"""
This module provides utilities for G-code based devices.

Attributes:
    MOVEMENT_BUFFER (int): buffer time after movement
    MOVEMENT_TIMEOUT (int): timeout for movement
    
## Classes:
    `GCodeDevice`: Protocol for G-code devices
    `GCode`: Interface to control a G-code based device.

<i>Documentation last updated: 2025-02-22</i>
"""
# Standard library imports
from __future__ import annotations
import time
from typing import Sequence, Protocol, Any

# Third-party imports
import numpy as np
from scipy.spatial.transform import Rotation

# Local application imports
from ..core.position import Position
from . import Mover
from .grbl_api import GRBL
from .marlin_api import Marlin

MOVEMENT_BUFFER = 0
MOVEMENT_TIMEOUT = 30

class GCodeDevice(Protocol):
    connection_details: dict
    is_connected: bool
    verbose: bool
    def clear(self):...
    def connect(self):...
    def disconnect(self):...
    def query(self, data:Any, multi_out:bool = True, **kwargs) -> list[str]|None:...
    def read(self) -> str:...
    def readAll(self) -> list[str]:...
    def write(self, data:str) -> bool:...
    def getSettings(self) -> dict[str, int|float|str]:...
    def halt(self) -> Position:...
    def home(self, axis:str|None = None, **kwargs) -> bool:...
    def setSpeedFactor(self, speed_factor:float|int, **kwargs):...
    

class GCode(Mover):
    """
    GCode provides an interface to control a G-code based device.
    Refer to https://reprap.org/wiki/G-code for more information on G-code commands.
    
    ### Constructor:
        `port` (str): serial port address
        `device_type_name` (str, optional): name of the device type. Defaults to 'GRBL'.
        `baudrate` (int, optional): baudrate of the device. Defaults to 115200.
        `movement_buffer` (int, optional): buffer time after movement. Defaults to None.
        `movement_timeout` (int, optional): timeout for movement. Defaults to None.
        `verbose` (bool, optional): verbosity of class. Defaults to False.
        
    ### Attributes and properties:
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
        `max_accels` (np.ndarray): maximum accelerations of the robot
        `max_speeds` (np.ndarray): maximum speeds of the robot
        
    ### Methods:
        `query`: query the device
        `toggleCoolantValve`: toggle the coolant valve
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
        `rotateBy`: rotate the robot by target direction
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
        port: str,
        *,
        device_type_name: str = 'GRBL',
        baudrate: int = 115200,
        movement_buffer: int|None = None,
        movement_timeout: int|None = None,
        verbose: bool = False,
        **kwargs
    ):
        """
        Initialize GCode class
        
        Args:
            port (str): serial port address
            device_type_name (str, optional): name of the device type. Defaults to 'GRBL'.
            baudrate (int, optional): baudrate of the device. Defaults to 115200.
            movement_buffer (int, optional): buffer time after movement. Defaults to None.
            movement_timeout (int, optional): timeout for movement. Defaults to None.
            verbose (bool, optional): verbosity of class. Defaults to False.
        """
        device_type = globals().get(device_type_name, GRBL)
        super().__init__(device_type=device_type, port=port, baudrate=baudrate, verbose=verbose, **kwargs)
        assert isinstance(self.device, (GRBL,Marlin)), "Ensure device is of type `GRBL` or `Marlin`"
        self.device: GRBL|Marlin = self.device
        self.movement_buffer = movement_buffer if movement_buffer is not None else MOVEMENT_BUFFER
        self.movement_timeout = movement_timeout if movement_timeout is not None else MOVEMENT_TIMEOUT
        self.settings = dict()
        return
    
    # Properties
    @property
    def max_accels(self) -> np.ndarray:
        """Maximum accelerations of the robot"""
        accel_x = self.settings.get('max_accel_x', 0)
        accel_y = self.settings.get('max_accel_y', 0)
        accel_z = self.settings.get('max_accel_z', 0)
        return np.array([accel_x, accel_y, accel_z])
    
    @property
    def max_speeds(self) -> np.ndarray:
        """Maximum speeds of the robot"""
        speed_x = self.settings.get('max_speed_x', 0)
        speed_y = self.settings.get('max_speed_y', 0)
        speed_z = self.settings.get('max_speed_z', 0)
        return np.array([speed_x, speed_y, speed_z])
    
    def halt(self) -> Position:
        """Halt robot movement"""
        position = self.device.halt()
        self.updateRobotPosition(to=position)
        self._logger.warning(f"Halted at {position} | To cancel movement, reset robot and re-home")
        return position
    
    def home(self, axis: str|None = None, *, timeout:int|None = None) -> bool:
        """ 
        Make the robot go home
        
        Args:
            axis (str, optional): axis to home. Defaults to None.
            timeout (int, optional): timeout for movement. Defaults to None.
            
        Returns:
            bool: whether the robot successfully homed
        """
        timeout = self.movement_timeout if timeout is None else timeout
        self.moveToSafeHeight()
        success = self.device.home(axis=axis, timeout=timeout)
        time.sleep(self.movement_buffer)
        if not success:
            return success
        if axis is None:
            xyz = (0,0,0)
        else:
            xyz = [(coord if axis.upper()!=ax else 0) for coord,ax in zip(self.robot_position.coordinates,'XYZ')]
        self.updateRobotPosition(to=Position(xyz))
        if any(self.home_position.coordinates):
            self.moveTo(self.home_position, self.speed_factor, robot=True)
        self.updateRobotPosition(to=self.home_position)
        self._logger.info(f"Home | {axis=}")
        return success
        
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
            by (Sequence[float]|Position|np.ndarray): target direction
            speed_factor (float, optional): speed factor. Defaults to None.
            jog (bool, optional): jog movement. Defaults to False.
            rapid (bool, optional): rapid movement. Defaults to False.
            robot (bool, optional): robot coordinates. Defaults to False.
            
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
        
        # current_position = self.robot_position if robot else self.worktool_position
        # return self.moveTo(move_by.apply(current_position), speed_factor, jog=jog, rapid=rapid, robot=robot)
        
        # Implementation of relative movement
        mode = 'G0' if rapid else 'G1'
        command = f'{mode} X{move_by.x:.2f} Y{move_by.y:.2f} Z{move_by.z:.2f}'
        command_xy = f'{mode} X{move_by.x:.2f} Y{move_by.y:.2f}'
        command_z = f'{mode} Z{move_by.z:.2f}'
        commands = (command_z, command_xy) if (move_by.z > 0) else (command_xy, command_z)
        self.setSpeedFactor(speed_factor, persist=False)
        data = 'G91'
        try:    # NOTE: temporary for transition to new SerialDevice
            data = self.device.processInput(data)
        except Exception:
            pass
        self.device.write(data)
        for command in commands:
            self.query(command, jog=jog, wait=True)
        data = 'G90'
        try:    # NOTE: temporary for transition to new SerialDevice
            data = self.device.processInput(data)
        except Exception:
            pass
        self.device.write(data)
        self.setSpeedFactor(self.speed_factor, persist=False)
        self.device.clearDeviceBuffer()
        
        # Adding time delays to coincide with movement
        if not jog:
            speed_factor = self.speed_factor if speed_factor is None else speed_factor
            distances = abs(move_by.coordinates)
            speeds = speed_factor*self.max_speeds
            accels = self.max_accels
            move_time = self._get_move_wait_time(distances, speeds, accels)
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
            to (Sequence[float]|Position|np.ndarray): target position
            speed_factor (float, optional): speed factor. Defaults to None.
            jog (bool, optional): jog movement. Defaults to False.
            rapid (bool, optional): rapid movement. Defaults to False.
            robot (bool, optional): robot coordinates. Defaults to False.
            
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
        mode = 'G0' if rapid else 'G1'
        command = f'{mode} X{move_to.x:.2f} Y{move_to.y:.2f} Z{move_to.z:.2f}'
        command_xy = f'{mode} X{move_to.x:.2f} Y{move_to.y:.2f}'
        command_z = f'{mode} Z{move_to.z:.2f}'
        commands = (command_z, command_xy) if (self.robot_position.z < move_to.z) else (command_xy, command_z)
        self.setSpeedFactor(speed_factor, persist=False)
        data = 'G90'
        try:    # NOTE: temporary for transition to new SerialDevice
            data = self.device.processInput(data)
        except Exception:
            pass
        self.device.write(data)
        for command in commands:
            self.query(command, jog=jog, wait=True)
        self.setSpeedFactor(self.speed_factor, persist=False)
        self.device.clearDeviceBuffer()
        
        # Adding time delays to coincide with movement
        if not jog:
            speed_factor = self.speed_factor if speed_factor is None else speed_factor
            distances = abs(move_to.coordinates - self.robot_position.coordinates)
            speeds = speed_factor*self.max_speeds
            accels = self.max_accels
            move_time = self._get_move_wait_time(distances, speeds, accels)
            time.sleep(move_time+self.movement_buffer)
        
        # Update position
        self.updateRobotPosition(to=move_to)
        return self.robot_position if robot else self.worktool_position
    
    def query(self, data:Any, multi_out:bool = True, *, timeout:int|float = 1, jog:bool = False, wait:bool = False) -> Any:
        """
        Query the device
        
        Args:
            data (Any): data to query
            multi_out (bool, optional): lines of data. Defaults to True.
            timeout (int, optional): timeout for movement. Defaults to None.
            jog (bool, optional): jog movement. Defaults to False.
            wait (bool, optional): wait for movement. Defaults to False.
            
        Returns:
            Any: response from device
        """
        if jog:
            # assert isinstance(self.device, GRBL), "Ensure device is of type `GRBL` to perform jog movements"
            data = f'{data} F{int(self.speed*60)}'         # Convert speed from mm/s to mm/min
            return self.device.query(data, multi_out=False, jog=jog, wait=wait)
        return self.device.query(data, multi_out=multi_out, timeout=timeout, jog=jog, wait=wait)
    
    def reset(self):
        """Reset the robot"""
        self.disconnect()
        self.connect()
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
        self.device.setSpeedFactor(speed_factor, speed_max=self.speed_max)
        if persist:
            self.speed_factor = speed_factor
        return
    
    def toggleCoolantValve(self, on:bool):
        """
        Toggle the coolant valve
        
        Args:
            on (bool): whether to turn the coolant valve on
        """
        command = 'M8' if on else 'M9'
        self.query(command, multi_out=False)
        return
    
    # Overwritten methods
    def connect(self):
        """Connect to the device"""
        self.device.connect()
        self.setSpeedFactor(1.0)
        self.settings = self.device.getSettings()
        return
