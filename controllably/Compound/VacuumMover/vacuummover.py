# -*- coding: utf-8 -*-
"""
This module provides a class for controlling a vacuum system integrated with a gantry movement system.
## Classes:
    `VacuumGantry`: A class that combines vacuum control with gantry movement capabilities.

<i>Documentation last updated: 2025-06-11</i>
"""
# Standard library imports
from __future__ import annotations
from types import SimpleNamespace
from typing import Sequence

# Local application imports
from ...Make.Vacuum import VacuumMixin
from ...Move.Cartesian import Gantry
from ...core.position import Position, Deck

class VacuumGantry(VacuumMixin, Gantry):
    """ 
    VacuumGantry class combines vacuum control with gantry movement capabilities.
    This class inherits from `VacuumMixin` for vacuum control and `Gantry` for movement control.
    
    ### Constructor:
        `port` (str): Serial port to connect to the gantry
        `limits` (Sequence[Sequence[float]]): movement limits in robot coordinate system. Defaults to ((0,0,0),(0,0,0)).
        `vacuum_on_delay` (float): delay in seconds to turn on the vacuum. Defaults to 3.
        `vacuum_off_delay` (float): delay in seconds to turn off the vacuum. Defaults to 3.
        `robot_position` (Position): initial position of the robot. Defaults to Position().
        `home_position` (Position): home position of the robot in robot coordinate system. Defaults to Position().
        `tool_offset` (Position): tool offset in robot coordinate system. Defaults to Position().
        `calibrated_offset` (Position): calibrated offset in robot coordinate system. Defaults to Position().
        `scale` (float): scale factor for movement. Defaults to 1.0.
        `deck` (Deck|None): deck object for the gantry. Defaults to None.
        `safe_height` (float|None): safe height for movement in robot coordinate system. Defaults to None.
        `speed_max` (float|None): maximum speed for movement in mm/min. Defaults to None.
        `device_type_name` (str): type of device, defaults to 'GRBL'.
        `baudrate` (int): baud rate for serial communication. Defaults to 115200.
        `movement_buffer` (int|None): buffer size for movement commands. Defaults to None.
        `movement_timeout` (int|None): timeout for movement commands in seconds. Defaults to None.
        `verbose` (bool): whether to print verbose output. Defaults to False.
        `simulation` (bool): whether to run in simulation mode. Defaults to False.
        
    ### Attributes:
        `vacuum_delays` (dict): dictionary containing delays for vacuum on and off operations.
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
        `toggleVacuum(on:bool)`: Toggle the vacuum on or off
        `evacuate()`: Turn on the vacuum for a specified delay
        `vent()`: Turn off the vacuum for a specified delay
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
        `transferLabware`: transfer labware from one slot to another
        `updateRobotPosition`: update the robot position
        `transformRobotToTool`: transform robot coordinates to tool coordinates
        `transformRobotToWork`: transform robot coordinates to work coordinates
        `transformToolToRobot`: transform tool coordinates to robot coordinates
        `transformWorkToRobot`: transform work coordinates to robot coordinates
        `calibrate`: calibrate the internal and external coordinate systems
    """
    
    _default_flags = SimpleNamespace(busy=False, verbose=False, vented=True)
    def __init__(self, 
        port: str,
        limits: Sequence[Sequence[float]] = ((0,0,0),(0,0,0)),          # in terms of robot coordinate system
        vacuum_on_delay: float = 3,
        vacuum_off_delay: float = 3,
        *, 
        robot_position: Position = Position(),
        home_position: Position = Position(),                           # in terms of robot coordinate system
        tool_offset: Position = Position(),
        calibrated_offset: Position = Position(),
        scale: float = 1.0,
        deck: Deck|None = None,
        safe_height: float|None = None,                                 # in terms of robot coordinate system
        speed_max: float|None = None,                                   # in mm/min
        device_type_name: str = 'GRBL',
        baudrate: int = 115200, 
        movement_buffer: int|None = None,
        movement_timeout: int|None = None,
        verbose: bool = False, 
        simulation: bool = False,
        **kwargs
    ):
        super().__init__(
            port=port, baudrate=baudrate, limits=limits,
            robot_position=robot_position, home_position=home_position,
            tool_offset=tool_offset, calibrated_offset=calibrated_offset, scale=scale, 
            deck=deck, safe_height=safe_height, speed_max=speed_max, 
            device_type_name=device_type_name, movement_buffer=movement_buffer, 
            movement_timeout=movement_timeout, verbose=verbose, simulation=simulation,
            message_end='\r\n',
            **kwargs
        )
        self.vacuum_delays = dict(on=vacuum_on_delay, off=vacuum_off_delay)
        return
    
    # VacuumMixin methods
    def toggleVacuum(self, on:bool):
        return self.toggleCoolantValve(on=on)
    
    def evacuate(self):
        super().evacuate(self.vacuum_delays.get('on',5))
        self.flags.vented = False
        return
    
    def vent(self):
        super().vent(self.vacuum_delays.get('off',5))
        self.flags.vented = True
        return

    # Combined methods
    def reset(self):
        self.vent()
        return super().reset()
    
    def shutdown(self):
        self.vent()
        return super().shutdown()
