# -*- coding: utf-8 -*-
# Standard library imports
from __future__ import annotations
import logging
from typing import Sequence, Protocol, Any

# Local application imports
from ..core.position import Position
from . import Mover
from .grbl_api import GRBL

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.debug(f"Import: OK <{__name__}>")

class GCodeDevice(Protocol):
    connection_details: dict
    is_connected: bool
    verbose: bool
    def clear(self):
        """Clear the input and output buffers"""
        raise NotImplementedError

    def connect(self):
        """Connect to the device"""
        raise NotImplementedError

    def disconnect(self):
        """Disconnect from the device"""
        raise NotImplementedError

    def query(self, data:str) -> Any:
        """Query the device"""
        raise NotImplementedError

    def read(self, **kwargs) -> str|list[str]:
        """Read data from the device"""
        raise NotImplementedError

    def write(self, data:str) -> bool:
        """Write data to the device"""
        raise NotImplementedError
    
    def checkAlarms(self):
        """Check the alarms of the device"""
        raise NotImplementedError
    
    def checkErrors(self):
        """Check the errors of the device"""
        raise NotImplementedError

    def checkParameters(self):
        """Check the parameters of the device"""
        raise NotImplementedError

    def checkSettings(self):
        """Check the settings of the device"""
        raise NotImplementedError
    
    def checkState(self):
        """Check the state of the device"""
        raise NotImplementedError
    
    def checkStatus(self) -> tuple[str, Sequence[float]]:
        """Check the status of the device"""
        raise NotImplementedError
    
    def clearAlarms(self):
        """Clear the alarms of the device"""
        raise NotImplementedError
    
    def halt(self):
        """Halt the device"""
        raise NotImplementedError
    
    def resume(self):
        """Resume the device"""
        raise NotImplementedError
    

class GCode(Mover):
    """
    Refer to https://www.cnccookbook.com/g-code-m-code-command-list-cnc-mills/ for more information on G-code commands.
    """
    def __init__(self,
        port: str,
        *,
        baudrate: int = 115200,
        verbose: bool = False,
        **kwargs
    ):
        """
        """
        super().__init__(device_type=GRBL, port=port, baudrate=baudrate, verbose=verbose, **kwargs)
        assert isinstance(self.device, GRBL), "Ensure device is of type GRBL"
        self.device: GRBL = self.device
        return
    
    def home(self, axis: str|None = None) -> Position:
        self.device.query('G90 G28')
        self.updateRobotPosition(to=self.home_position)
        return self.robot_position
        
    def moveBy(self,
        by: Sequence[float]|Position,
        speed_factor: float|None = None,
        *,
        rapid: bool = False,
        robot: bool = False
    ) -> Position:
        assert isinstance(by, (Sequence, Position)), f"Ensure `by` is a Sequence or Position object"
        if isinstance(by, Sequence):
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
        
        # Implementation of relative movement
        by = move_by.coordinates
        mode = 'G0' if rapid else 'G1'
        self.setSpeedFactor(speed_factor, persist=False)
        self.device.query(f'G91 {mode} X{by[0]} Y{by[1]} Z{by[2]}')
        self.device.query('G90')
        self.setSpeedFactor(self.speed_factor, persist=False)
        
        # Update position
        self.updateRobotPosition(by=move_by)
        return self.robot_position if robot else self.tool_position
    
    def moveTo(self,
        to: Sequence[float]|Position,
        speed_factor: float|None = None,
        *,
        rapid: bool = False,
        robot: bool = False
    ) -> Position:
        assert isinstance(to, (Sequence, Position)), f"Ensure `to` is a Sequence or Position object"
        if isinstance(to, Sequence):
            assert len(to) == 3, f"Ensure `to` is a 3-element sequence for x,y,z"
        move_to = to if isinstance(to, Position) else Position(to)
        logger.debug(f"Moving by {move_to} at speed factor {speed_factor}")
        
        # Convert to robot coordinates
        move_to = move_to if robot else self.transformToolToRobot(self.transformWorkToRobot(move_to))
        
        # Implementation of absolute movement
        to = move_to.coordinates
        mode = 'G0' if rapid else 'G1'
        self.setSpeedFactor(speed_factor, persist=False)
        self.device.query(f'G90 {mode} X{to[0]} Y{to[1]} Z{to[2]}')
        self.setSpeedFactor(self.speed_factor, persist=False)
        
        # Update position
        self.updateRobotPosition(to=move_to)
        return self.robot_position if robot else self.tool_position
    
    def reset(self):
        self.disconnect()
        self.connect()
        return
    
    def setSpeedFactor(self, speed_factor:float, persist:bool = True) -> float:
        feed_rate = self.speed
        self.query(f'G90 F{feed_rate}')
        if persist:
            self.speed_factor = speed_factor
        return speed_factor
    
    # Overridden methods
    def connect(self):
        self.device.connect()
        self.device.clearAlarms()
        self.setSpeedFactor(1.0)
        self.device.checkSettings()
        _, coordinates = self.device.checkStatus()
        print(coordinates)
        return