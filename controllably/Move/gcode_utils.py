# -*- coding: utf-8 -*-
# Standard library imports
from __future__ import annotations
import logging
import time
from types import SimpleNamespace
from typing import Sequence, Protocol, Any

# Third-party imports
import numpy as np

# Local application imports
from ..core.position import Position
from . import Mover
from .grbl_api import GRBL
from .marlin_api import Marlin

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.debug(f"Import: OK <{__name__}>")

LOOP_INTERVAL = 0.1
MOVEMENT_BUFFER = 1
MOVEMENT_TIMEOUT = 30

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

    def query(self, data:Any, lines:bool = True) -> list[str]|None:
        """Query the device"""
        raise NotImplementedError

    def read(self, lines:bool = False) -> str|list[str]:
        """Read data from the device"""
        raise NotImplementedError

    def write(self, data:str) -> bool:
        """Write data to the device"""
        raise NotImplementedError

    def checkSettings(self) -> dict[str, int|float|str]:
        """Check the settings of the device"""
        raise NotImplementedError
    
    def checkStatus(self) -> tuple[str, np.ndarray[float], np.ndarray[float]]:
        """Check the status of the device"""
        raise NotImplementedError
    
    def halt(self) -> Position:
        """Halt the device"""
        raise NotImplementedError
    

class GCode(Mover):
    """
    Refer to https://www.cnccookbook.com/g-code-m-code-command-list-cnc-mills/ for more information on G-code commands.
    """
    _default_flags: SimpleNamespace[str,bool] = SimpleNamespace(busy=False, verbose=False, jog=False)
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
        """
        device_type = globals().get(device_type_name, GRBL)
        super().__init__(device_type=device_type, port=port, baudrate=baudrate, verbose=verbose, **kwargs)
        assert isinstance(self.device, (GRBL,Marlin)), "Ensure device is of type `GRBL` or `Marlin`"
        self.device: GRBL|Marlin = self.device
        self.movement_buffer = movement_buffer if movement_buffer is not None else MOVEMENT_BUFFER
        self.movement_timeout = movement_timeout if movement_timeout is not None else MOVEMENT_TIMEOUT
        return
    
    def halt(self) -> Position:
        position = self.device.halt()
        self._robot_position = position
        logger.warning(f"Halted at {position}")
        logger.warning('To cancel movement, reset robot and re-home')
        logger.warning('To resume movement, use `resume` method')           # TODO: check Marlin resume command
        return position
    
    def home(self, axis: str|None = None) -> Position:
        if isinstance(self.device, GRBL):
            if axis is not None:
                assert axis.upper() in 'XYZ', "Ensure axis is X,Y,Z for GRBL"
            command = '$H' if axis is None else f'$H{axis.upper()}'
            self.query(command)
            success = self._wait_for_status(('Home',), timeout=self.movement_timeout)
            if not success:
                status,_,_ = self.device.checkStatus()
                logger.error(f"Timeout: {status} | {command}")
                return self.robot_position
        elif isinstance(self.device, Marlin):
            if axis is not None:
                logger.warning("Ignoring homing axis parameter for Marlin firmware")
            self.query('G90')
            self.query('G28')
        else:
            raise NotImplementedError
        self.updateRobotPosition(to=self.home_position)
        return self.robot_position
        
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
        mode = 'G0' if rapid else 'G1'
        command_xy = f'{mode} X{move_by.x} Y{move_by.y}'
        command_z = f'{mode} Z{move_by.z}'
        commands = (command_z, command_xy) if (move_by.z > 0) else (command_xy, command_z)
        self.setSpeedFactor(speed_factor, persist=False)
        self.query('G91')
        for command in commands:
            self.query(command, jog=jog, wait=True)
        self.query('G90')
        self.setSpeedFactor(self.speed_factor, persist=False)
        time.sleep(0.5)
        
        # Update position
        self.updateRobotPosition(by=move_by)
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
        logger.debug(f"Moving by {move_to} at speed factor {speed_factor}")
        
        # Convert to robot coordinates
        move_to = move_to if robot else self.transformToolToRobot(self.transformWorkToRobot(move_to, self.calibrated_offset), self.tool_offset)
        if not self.isFeasible(move_to.coordinates, external=False, tool_offset=False):
            logger.warning(f"Target position {move_to} is not feasible")
            return self.robot_position if robot else self.tool_position
        
        # Implementation of absolute movement
        mode = 'G0' if rapid else 'G1'
        command_xy = f'{mode} X{move_to.x} Y{move_to.y}'
        command_z = f'{mode} Z{move_to.z}'
        commands = (command_z, command_xy) if (self.position.z < move_to.z) else (command_xy, command_z)
        self.setSpeedFactor(speed_factor, persist=False)
        self.query('G90')
        for command in commands:
            self.query(command, jog=jog, wait=True)
        self.setSpeedFactor(self.speed_factor, persist=False)
        time.sleep(0.5)
        
        # Update position
        self.updateRobotPosition(to=move_to)
        return self.robot_position if robot else self.tool_position
    
    def query(self, data:str, *, jog:bool = False, wait:bool = False) -> Any:
        if jog:
            assert isinstance(self.device, GRBL), "Ensure device is of type `GRBL` to perform jog movements"
            assert self.device.__version__().startswith("1.1"), "Ensure GRBL version is at least 1.1 to perform jog movements"
            data = data.replace('G0 ', '').replace('G1 ', '')
            data = f'$J={data} F{self.speed}'
            self.device.write(data)
            return self.device.read()
        if not wait:
            self.device.write(data)
            return self.device.read()
        
        success = self._wait_for_status(('Idle',), timeout=MOVEMENT_TIMEOUT)
        if not success:
            status,_,_ = self.device.checkStatus()
            logger.error(f"Timeout: {status} | {data}")
            if status == 'Jog':
                raise RuntimeError("Jog mode still active")
            return []
        
        self.device.write(data)
        response = self.device.read()
        
        success = self._wait_for_status(('Idle',), timeout=self.movement_timeout)
        if not success:
            status,_,_ = self.device.checkStatus()
            logger.error(f"Timeout: {status} | {data}")
        return response
    
    def reset(self):
        self.disconnect()
        self.connect()
        return
    
    def setSpeedFactor(self, speed_factor:float|None = None, persist:bool = True) -> float:
        speed_factor = self.speed_factor if speed_factor is None else speed_factor
        assert isinstance(speed_factor, float), "Ensure speed factor is a float"
        if isinstance(self.device, GRBL):
            feed_rate = self.speed_max * speed_factor
            self.query(f'G90 F{feed_rate}')
        elif isinstance(self.device, Marlin):
            self.query(f'M220 F{speed_factor}')
        else:
            raise NotImplementedError
        if persist:
            self.speed_factor = speed_factor
        return speed_factor
    
    def toggleCoolantValve(self, state:bool) -> bool:
        command = 'M8' if state else 'M9'
        self.query(command)
        return state
    
    def _wait_for_status(self, statuses:Sequence[str], timeout:int = MOVEMENT_TIMEOUT) -> bool:
        status,_,_ = self.device.checkStatus()
        start_time = time.perf_counter()
        while status not in statuses:
            time.sleep(LOOP_INTERVAL)
            status,_,_ = self.device.checkStatus()
            if status == 'Hold':
                raise RuntimeError("Movement paused")
            if time.perf_counter() - start_time > timeout:
                return False
        return True
    
    # Overwritten methods
    def connect(self):
        self.device.connect()
        self.setSpeedFactor(1.0)
        self._settings = self.device.checkSettings()
        print(self._settings)
        return
