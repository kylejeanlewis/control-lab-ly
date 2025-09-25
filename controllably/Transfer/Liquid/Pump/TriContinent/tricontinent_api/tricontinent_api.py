# -*- coding: utf-8 -*-
""" 
This module provides a class for controlling TriContinent pumps.

Attributes:
    MAX_CHANNELS (int): Maximum number of channels.
    ACCEL_MULTIPLIER (int): Acceleration multiplier.
    BUSY (str): Busy status codes.
    IDLE (str): Idle status codes.
    READ_FORMAT (str): Read format template.
    WRITE_FORMAT (str): Write format template.
    Data (NamedTuple): Data type for the device.
    BoolData (NamedTuple): Boolean data type for the device.
    FloatData (NamedTuple): Float data type for the device.
    IntData (NamedTuple): Integer data type for the device.
    
## Classes:
    `TriContinentDevice`: TriContinent pump device class.
    
<i>Documentation last updated: 2025-02-22</i>
"""
# Standard library imports
from __future__ import annotations
from datetime import datetime
import time
from types import SimpleNamespace
from typing import NamedTuple, Any

# Local application imports
from ......core.device import SerialDevice, AnyDevice
from .tricontinent_lib import ErrorCode, StatusCode

MAX_CHANNELS = 15
ACCEL_MULTIPLIER = 2500
BUSY = StatusCode.Busy.value
IDLE = StatusCode.Idle.value

READ_FORMAT = "/{channel:1}{data}\x03\r"        # response template: <PRE><CHANNEL><STATUS><STRING><POST>
WRITE_FORMAT = '/{channel}{data}\r'             # command template: <PRE><ADR><STRING><POST>
Data = NamedTuple("Data", [("data", str), ("channel", int)])
BoolData = NamedTuple("BoolData", [("data", bool), ("channel", int)])
FloatData = NamedTuple("FloatData", [("data", float), ("channel", int)])
IntData = NamedTuple("IntData", [("data", int), ("channel", int)])

class TriContinentDevice(SerialDevice):
    """ 
    TriContinent pump device class.
    
    ### Constructor:
        `port` (str, optional): The port to connect to. Defaults to None.
        `baudrate` (int, optional): The baudrate of the connection. Defaults to 9600.
        `timeout` (int, optional): The timeout for the connection. Defaults to 1.
        `init_timeout` (int, optional): The timeout for initialization. Defaults to 1.
        `data_type` (NamedTuple, optional): The data type for the device. Defaults to Data.
        `read_format` (str, optional): The read format for the device. Defaults to READ_FORMAT.
        `write_format` (str, optional): The write format for the device. Defaults to WRITE_FORMAT.
        `simulation` (bool, optional): Whether to simulate the device. Defaults to False.
        `verbose` (bool, optional): Whether to print verbose output. Defaults to False.
        
    ### Attributes and properties:
        `info` (str): Model and version information of the pump.
        `model` (str): Model of the pump.
        `version` (str): Version of the pump.
        `channel` (int): Channel number of the pump.
        `position` (int): Current position of the pump.
        `status` (int): Status of the pump.
        `start_speed` (int): Start speed of the pump.
        `speed` (int): Top speed of the pump.
        `acceleration` (int): Acceleration of the pump.
        `valve_position` (str): Valve position of the pump.
        `init_status` (bool): Initialization status of the pump.
        `pump_config` (str): Pump configuration.
        `command_buffer` (str): Command buffer.
        `output_right` (bool): Output side of the pump.
        `max_position` (int): Maximum position of the pump.
        
    ### Methods:
        `connect`: Connect to the pump
        `query`: Query the pump
        `setChannel`: Set the channel of the pump
        `getStatus`: Get the status of the pump
        `getPosition`: Get the current position of the pump
        `getInfo`: Get the model and version information of the pump
        `getState`: Get the state of the pump
        `getStartSpeed`: Get the start speed of the pump
        `getTopSpeed`: Get the top speed of the pump
        `getValvePosition`: Get the valve position of the pump
        `getAcceleration`: Get the acceleration of the pump
        `getInitStatus`: Get the initialization status of the pump
        `getPumpConfig`: Get the pump configuration
        `setStartSpeed`: Set the start speed of the pump
        `setTopSpeed`: Set the top speed of the pump
        `setValvePosition`: Set the valve position of the pump
        `setAcceleration`: Set the acceleration of the pump
        `initialize`: Initialize the pump
        `reverse`: Reverse the pump
        `wait`: Wait for a specified duration
        `repeat`: Repeat the last command for a specified number of cycles
        `run`: Run the command buffer
        `stop`: Stop the pump
        `aspirate`: Aspirate a specified number of steps
        `dispense`: Dispense a specified number of steps
        `move`: Move the plunger by a specified number of steps
        `moveBy`: Move the plunger by a specified number of steps
        `moveTo`: Move the plunger to a specified position
    """
    
    _default_flags: SimpleNamespace = SimpleNamespace(busy=False, verbose=False, connected=False, simulation=False)
    def __init__(self,
        port: str|None = None, 
        baudrate: int = 9600, 
        timeout: int = 1, 
        *,
        init_timeout: int = 1, 
        data_type: NamedTuple = Data,
        read_format: str = READ_FORMAT,
        write_format: str = WRITE_FORMAT,
        simulation: bool = False, 
        verbose: bool = False,
        **kwargs
    ):
        """
        Initialize the TriContinent pump device.
        
        Args:
            port (str, optional): The port to connect to. Defaults to None.
            baudrate (int, optional): The baudrate of the connection. Defaults to 9600.
            timeout (int, optional): The timeout for the connection. Defaults to 1.
            init_timeout (int, optional): The timeout for initialization. Defaults to 1.
            data_type (NamedTuple, optional): The data type for the device. Defaults to Data.
            read_format (str, optional): The read format for the device. Defaults to READ_FORMAT.
            write_format (str, optional): The write format for the device. Defaults to WRITE_FORMAT.
            simulation (bool, optional): Whether to simulate the device. Defaults to False.
            verbose (bool, optional): Whether to print verbose output. Defaults to False.
        """
        super().__init__(
            port=port, baudrate=baudrate, timeout=timeout,
            init_timeout=init_timeout, simulation=simulation, verbose=verbose, 
            data_type=data_type, read_format=read_format, write_format=write_format, **kwargs
        )
        
        self.info = "C3000: MMDDYY"
        self.model = 'C3000'
        self.version = 'MMDDYY'
        # self.volume_resolution = 1
        
        self.channel = 1
        self.position = 0
        self.status = 0
        
        self.start_speed = 0
        self.speed = 0
        self.acceleration = 0
        self.valve_position = ''
        self.init_status = False
        self.pump_config = ''
        
        self.command_buffer = ''
        self.output_right: bool|None = None
        return

    # Properties
    @property
    def max_position(self) -> int:
        """Maximum position of the pump"""
        return int(''.join(filter(str.isdigit, self.model)))
    
    def connect(self):
        super().connect()
        self.getState()
        return
    
    def query(self, 
        data: Any, 
        multi_out: bool = False, 
        *, 
        timeout: int|float = 0.3, 
        format_in: str|None = None, 
        format_out: str|None = None, 
        data_type: NamedTuple|None = None, 
        timestamp: bool = False
    ):
        data_type: NamedTuple = data_type or self.data_type
        format_in = format_in or self.write_format
        format_out = format_out or self.read_format
        if self.flags.simulation:
            field_types = data_type.__annotations__
            data_defaults = data_type._field_defaults
            defaults = [data_defaults.get(f, ('' if t is str else t(0))) for f,t in field_types.items()]
            data_out = data_type(*defaults)
            response = (data_out, datetime.now()) if timestamp else data_out
            return [response] if multi_out else response
        
        responses = super().query(
            data, multi_out, timeout=timeout, 
            format_in=format_in, timestamp=timestamp,
            channel=self.channel
        )
        self._logger.debug(repr(responses))
        if multi_out and not len(responses):
            return None
        responses = responses if multi_out else [responses]
        
        all_output = []
        for response in responses:
            if timestamp:
                out,now = response
            else:
                out = response
            if out is None:
                all_output.append(response)
                continue
            out: Data = out
            
            status, content = (out.data[0],out.data[1:]) if len(out.data) > 1 else (out.data,'0')
            # Check status code
            if status not in BUSY + IDLE:
                raise RuntimeError(f"Unknown status code: {status!r}")
            self.flags.busy = (status in BUSY)
            self.status = BUSY.index(status) if self.flags.busy else IDLE.index(status)
            if self.status:
                self._logger.warning(f"Error [{self.status}]: {ErrorCode[f'er{self.status}'].value}")
            if self.status in (1,7,9,10):
                raise Exception(f"Please reinitialize: Pump {self.channel}.")
            
            data_dict = out._asdict()
            data_dict.update(dict(data=content))
            data_out = self.processOutput(format_out.format(**data_dict).strip(), format_out=format_out, data_type=data_type)
            data_out = data_out if timestamp else data_out[0]
            
            all_output.append((data_out, now) if timestamp else data_out)
        return all_output if multi_out else all_output[0]
    
    def setChannel(self, channel:int):
        """ 
        Set the channel of the pump.
        
        Args:
            channel (int): The channel number of the pump.
        """
        assert channel in list(range(MAX_CHANNELS)), f"Channel must be an integer between 0 and {MAX_CHANNELS-1}"
        _old_channel = self.channel
        self.channel = channel
        try:
            self.getStatus()
            self.getState()
        except AttributeError:
            self._logger.warning(f"Channel {channel} not available.")
            self.channel = _old_channel
        return
    
    # Status query methods
    def getStatus(self) -> tuple[bool,str]:
        """
        Get the status of the pump.
        
        Returns:
            tuple[bool,str]: A tuple containing the busy status and the error code.
        """
        out: Data|None = self.query('Q', data_type=IntData)
        if self.flags.simulation:
            return self.flags.busy, self.status
        self.status = out.data
        return self.flags.busy, ErrorCode[f'er{self.status}'].value
    
    def getPosition(self) -> int:
        """
        Get the current position of the pump.
        
        Returns:
            int: The current position of the pump.
        """
        out: Data = self.query('?', data_type=IntData)
        if self.flags.simulation:
            return self.position
        self.position = out.data
        return self.position
    
    # Getter methods
    def getInfo(self) -> str:
        """
        Get the model and version information of the pump.
        
        Returns:
            str: The model and version information of the pump.
        """
        out: Data = self.query('&')
        self.info = out.data
        model_version = out.data.split(':')
        self.model = model_version[0].strip() or self.model
        self.version = model_version[1].strip() if len(model_version) > 1 else self.version
        return out.data
    
    def getState(self) -> dict[str, int|bool]:
        """
        Get the state of the pump.
        
        Returns:
            dict[str, int|bool]: A dictionary containing the state of the pump.
        """
        self.getInfo()
        self.getStartSpeed()
        self.getTopSpeed()
        self.getAcceleration()
        self.getValvePosition()
        self.getPosition()
        self.getInitStatus()
        return {
            'start_speed': self.start_speed,
            'speed': self.speed,
            'acceleration': self.acceleration,
            'valve_position': self.valve_position,
            'position': self.position,
            'init_status': self.init_status
        }

    def getStartSpeed(self) -> int:
        """
        Get the start speed of the pump.
        
        Returns:
            int: The start speed of the pump.
        """
        out: Data =  self.query('?1', data_type=IntData)
        self.start_speed = out.data
        return self.start_speed

    def getTopSpeed(self) -> int:
        """
        Get the top speed of the pump.
        
        Returns:
            int: The top speed of the pump.
        """
        out: Data = self.query('?2', data_type=IntData)
        self.speed = out.data
        return self.speed
    
    def getValvePosition(self) -> str:
        """ 
        Get the valve position of the pump.
        
        Returns:
            str: The valve position of the pump.
        """
        out: Data = self.query('?6')
        self.valve_position = out.data
        if out.data == '0':
            self.valve_position = None
        return self.valve_position
    
    def getAcceleration(self) -> int:
        """
        Get the acceleration of the pump.
        
        Returns:
            int: The acceleration of the pump.
        """
        out: Data = self.query('?7', data_type=IntData)
        self.acceleration = out.data * ACCEL_MULTIPLIER
        return self.acceleration
    
    def getInitStatus(self) -> bool:
        """
        Get the initialization status of the pump.
        
        Returns:
            bool: The initialization status of the pump.
        """
        out: Data = self.query('?19', data_type=BoolData)
        self.init_status = out.data
        return self.init_status
    
    # def getPumpConfig(self) -> str:     #TODO     out --> '/0`10,75,14,62,0,1,20,10,48,210,2130001,0,0,0,0,0,25,20,15,5,60\x03'
    #     out: Data = self.query('?76')
    #     self.pump_config = out.data
    #     return self.pump_config
    
    # Setter methods
    def setStartSpeed(self, speed: int, *, immediate: bool = True):
        """
        Set the start speed of the pump.
        
        Args:
            speed (int): The start speed of the pump.
            immediate (bool, optional): Whether to execute the command immediately. Defaults to True.
        """
        speed = round(speed)
        assert (0<=speed<=1000), "Start speed must be an integer between 0 and 1000"
        command = f'v{speed}'
        if immediate:
            self.run(command)
        else:
            self.command_buffer += command
        return

    def setTopSpeed(self, speed: int, *, immediate: bool = True):
        """
        Set the top speed of the pump.
        
        Args:
            speed (int): The top speed of the pump.
            immediate (bool, optional): Whether to execute the command immediately. Defaults to True.
        """
        speed = round(speed)
        assert (0<=speed<=6000), "Start speed must be an integer between 0 and 6000"
        command = f'V{speed}'
        if immediate:
            self.run(command)
        else:
            self.command_buffer += command
        return
    
    def setValvePosition(self, valve: str, *, immediate: bool = True):
        """
        Set the valve position of the pump.
        
        Args:
            valve (str): The valve position of the pump.
            immediate (bool, optional): Whether to execute the command immediately. Defaults to True.
        """
        assert isinstance(valve,str)
        valve = valve.upper()
        assert len(valve)==1 and (valve in 'IOBE'), "Valve must be one of 'I', 'O', 'B', or 'E'"
        if immediate:
            self.run(valve)
        else:
            self.command_buffer += valve
        return
    
    def setAcceleration(self, acceleration: int, *, immediate: bool = True):
        """
        Set the acceleration of the pump.
        
        Args:
            acceleration (int): The acceleration of the pump.
            immediate (bool, optional): Whether to execute the command immediately. Defaults to True.
        """
        assert (ACCEL_MULTIPLIER<=acceleration<=20*ACCEL_MULTIPLIER), "Acceleration code must be an integer between 2,500 and 50,000"
        acceleration_code = int(acceleration/ACCEL_MULTIPLIER)
        command = f'L{acceleration_code}'
        if immediate:
            self.run(command)
        else:
            self.command_buffer += command
        return
    
    # Actions
    def initialize(self, output_right: bool|None = None, *, immediate: bool = True):
        """
        Initialize the pump.
        
        Args:
            output_right (bool): Whether the output is on the right side.
            immediate (bool, optional): Whether to execute the command immediately. Defaults to True.
        """
        output_right = output_right if output_right is not None else self.output_right
        assert output_right is not None, "Provide a boolean value for 'output_right"
        mode = 'Z' if output_right else 'Y'
        if immediate:
            self.run(mode)
        else:
            self.command_buffer += mode
        self.output_right = output_right
        return
    
    def reverse(self, *, immediate: bool = True):
        """
        Reverse the pump.
        
        Args:
            immediate (bool, optional): Whether to execute the command immediately. Defaults to True.
        """
        assert self.output_right is not None, "Pump must be initialized first!"
        self.initialize(not self.output_right, immediate=immediate)
        return
    
    def wait(self, duration: int|float, *, immediate: bool = True):
        """
        Wait for a specified duration.
        
        Args:
            duration (int|float): The duration to wait.
            immediate (bool, optional): Whether to execute the command immediately. Defaults to True.
        """
        duration_ms = round(duration * 1000)
        assert 0<=duration_ms<=30_000, "Duration must be between 0 and 30"
        command = f'M{duration_ms}'
        if immediate:
            self.run(command)
        else:
            self.command_buffer += command
        return
    
    def repeat(self, cycles: int):
        """
        Repeat the last command for a specified number of cycles.
        
        Args:
            cycles (int): The number of cycles to repeat the last command.
        """
        assert 0<=cycles<=30_000, "Cycles must be between 0 and 30,000"
        self.command_buffer = f'g{self.command_buffer}G{cycles}'
        return
    
    def run(self, command: str|None = None):
        """
        Run the command buffer.
        
        Args:
            command (str, optional): The command to run. Defaults to None.
        """
        command = command or self.command_buffer
        self.query(f'{command}R')
        self.command_buffer = ''
        self.flags.busy = True
        while self.flags.busy:
            if self.flags.simulation:
                break
            time.sleep(0.1)
            self.getStatus()
        self.getStatus()
        self.getPosition()
        self.getInitStatus()
        return
    
    def stop(self):
        """Stop the pump."""
        self.query('T')
        return
    
    # Plunger actions
    def aspirate(self, steps:int, *, blocking: bool = True, immediate: bool = True):
        """
        Aspirate a specified number of steps.
        
        Args:
            steps (int): The number of steps to aspirate.
            blocking (bool, optional): Whether to block until the command is executed. Defaults to True.
            immediate (bool, optional): Whether to execute the command immediately. Defaults to True.
        """
        steps = round(steps)
        assert steps >= 0, f"Ensure non-negative steps! [received: {steps}]"
        self.setValvePosition('I', immediate=False)
        self.moveBy(steps, blocking=blocking, immediate=False)
        if immediate:
            self.run()
        return
    
    def dispense(self, steps:int, *, blocking: bool = True, immediate: bool = True):
        """
        Dispense a specified number of steps.
        
        Args:
            steps (int): The number of steps to dispense.
            blocking (bool, optional): Whether to block until the command is executed. Defaults to True.
            immediate (bool, optional): Whether to execute the command immediately. Defaults to True.
        """
        steps = round(steps)
        assert steps >= 0, f"Ensure non-negative steps! [received: {steps}]"
        self.setValvePosition('O', immediate=False)
        self.moveBy(-steps, blocking=blocking, immediate=False)
        if immediate:
            self.run()
        return
    
    def move(self, steps:int, *, blocking: bool = True, immediate: bool = True):
        """
        Move the plunger by a specified number of steps.
        
        Args:
            steps (int): The number of steps to move.
            blocking (bool, optional): Whether to block until the command is executed. Defaults to True.
            immediate (bool, optional): Whether to execute the command immediately. Defaults to True.
        """
        return self.moveBy(steps, blocking=blocking, immediate=immediate)
    
    def moveBy(self, steps: int, *, blocking: bool = True, immediate: bool = True):
        """
        Move the plunger by a specified number of steps.
        
        Args:
            steps (int): The number of steps to move.
            blocking (bool, optional): Whether to block until the command is executed. Defaults to True.
            immediate (bool, optional): Whether to execute the command immediately. Defaults to True.
        """
        steps = round(steps)
        assert (0<=(self.position+steps)<=self.max_position), f"Range limits [0,{self.max_position}] reached! [received: {self.position}+{steps}]"
        prefix = 'p' if steps >= 0 else 'd'
        prefix = prefix.upper() if blocking else prefix.lower()
        command = f'{prefix}{abs(steps)}'
        if immediate:
            self.run(command)
        else:
            self.command_buffer += command
        self.position += steps
        return
    
    def moveTo(self, position: int, *, blocking: bool = True, immediate: bool = True):
        """
        Move the plunger to a specified position.
        
        Args:
            position (int): The position to move to.
            blocking (bool, optional): Whether to block until the command is executed. Defaults to True.
            immediate (bool, optional): Whether to execute the command immediately. Defaults to True.
        """
        position = round(position)
        assert (0<=position<=self.max_position), f"Position must be an integer between 0 and {self.max_position} [received: {position}]"
        prefix = 'A' if blocking else 'a'
        command = f'{prefix}{position}'
        if immediate:
            self.run(command)
        else:
            self.command_buffer += command
        self.position = position
        return
    