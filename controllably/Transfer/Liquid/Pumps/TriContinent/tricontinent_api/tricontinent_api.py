# -*- coding: utf-8 -*-
# Standard library imports
from __future__ import annotations
import logging
import time
from types import SimpleNamespace
from typing import NamedTuple, Any

# Local application imports
from ......core.device import SerialDevice
from .tricontinent_lib import ErrorCode

_logger = logging.getLogger("controllably.Transfer")
_logger.debug(f"Import: OK <{__name__}>")

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
logger.addHandler(handler)

MAX_CHANNELS = 15
BUSY = '@ABCDEFGHIJKO'
IDLE = '`abcdefghijko'

READ_FORMAT = "/{channel:1}{data}\x03\r"        # response template: <PRE><STRING><POST>
WRITE_FORMAT = '/{channel}{data}\r'                         # command template: <PRE><ADR><STRING><POST>
Data = NamedTuple("Data", [("data", str), ("channel", int)])
BoolData = NamedTuple("BoolData", [("data", bool), ("channel", int)])
FloatData = NamedTuple("FloatData", [("data", float), ("channel", int)])
IntData = NamedTuple("IntData", [("data", int), ("channel", int)])

class TriContinentDevice(SerialDevice):
    
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
        super().__init__(
            port=port, baudrate=baudrate, timeout=timeout,
            init_timeout=init_timeout, simulation=simulation, verbose=verbose, 
            data_type=data_type, read_format=read_format, write_format=write_format, **kwargs
        )
        
        self._logger = logger.getChild(f"{self.__class__.__name__}_{id(self)}")
        self._logger.addHandler(logging.StreamHandler())
        self.verbose = verbose
        
        self.info = "C3000: MMDDYY"
        self.model = 'C3000'
        self.version = 'MMDDYY'
        # self.volume_resolution = 1
        
        self.channel = 1
        self.position = 0
        self.status = 0
        
        self.command_buffer = ''
        self.output_right: bool|None = None
        return

    # Properties
    @property
    def max_position(self) -> int:
        return int(''.join(filter(str.isdigit, self.model)))
    
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
        data_type: NamedTuple = data_type or Data
        responses = super().query(
            data, multi_out, timeout=timeout, 
            format_in=format_in, timestamp=timestamp,
            channel=self.channel
        )
        if multi_out and not len(responses):
            return None
        responses = responses if multi_out else [responses]
        
        all_output = []
        for response in responses:
            if timestamp:
                out,now = response
            else:
                out = response
            if out is None or len(out.data) == 0:
                all_output.append(None)
                continue
            status, content = (out.data[0],out.data[1:]) if len(out.data) > 1 else (out.data,'0')
            out: Data = out
            # Check channel
            if out.channel != str(self.channel):
                self._logger.warning(f"Channel mismatch: {out.channel} != {self.channel}")
                all_output.append(('', now) if timestamp else '')
                continue
            # Check status code
            if status not in BUSY + IDLE:
                raise RuntimeError(f"Unknown status code: {status!r}")
            self.flags.busy = (status in BUSY)
            self.status = BUSY.index(status) if self.flags.busy else IDLE.index(status)
            if self.status:
                self._logger.warning(f"Error [{self.status}]: {ErrorCode[f'er{self.status}'].value}")
            if self.status in (1,7,9,10):
                raise Exception(f"Please reinitialize: Pump {self.channel}.")
            
            if self.flags.simulation:
                field_types = data_type.__annotations__
                data_defaults = data_type._field_defaults
                defaults = [data_defaults.get(f, ('' if t==str else 0)) for f,t in field_types.items()]
                data_out = data_type(defaults)
            else:
                data_dict = out._asdict()
                data_dict.update(dict(data=content))
                data_out = self.processOutput(format_out.format(**data_dict).strip(), format=format_out, data_type=data_type)
                data_out = data_out if timestamp else data_out[0]
            all_output.append((data_out, now) if timestamp else data_out)
        return all_output if multi_out else all_output[0]
    
    def setChannel(self, channel:int):
        assert channel in list(range(MAX_CHANNELS)), f"Channel must be an integer between 0 and {MAX_CHANNELS-1}"
        self.channel = channel
        return
    
    # Status query methods
    def getStatus(self) -> tuple[bool,str]:
        out: Data = self.query('Q')
        status = out.data[1] if len(out.data) > 1 else ''
        if status not in BUSY + IDLE:
            raise RuntimeError(f"Unknown status code: {status!r}")
        self.flags.busy = (status in BUSY)
        self.status = BUSY.index(status) if self.flags.busy else IDLE.index(status)
        if self.status:
            self._logger.warning(f"Error [{self.status}]: {ErrorCode[f'er{self.status}'].value}")
        if self.status in (1,7,9,10):
            raise Exception(f"Please reinitialize: Pump {self.channel}.")
        return self.flags.busy, self.status
    
    def getPosition(self) -> int:
        out: Data = self.query('?')
        self.position = int(out.data[2:]) if len(out.data) > 2 else self.position
        return self.position
    
    # Getter methods
    def getInfo(self) -> str:
        out: Data = self.query('&')
        self.info = out.data
        self.model = out.data.split(':')[0].strip()
        self.version = out.data.split(':')[1].strip()
        return out.data

    def getStartSpeed(self) -> int:
        out: Data =  self.query('?1')
        start_speed = int(out.data[2:]) if len(out.data) > 2 else 0
        return start_speed

    def getTopSpeed(self) -> int:
        out: Data = self.query('?2')
        top_speed = int(out.data[2:]) if len(out.data) > 2 else 0
        return top_speed
    
    def getValvePosition(self) -> str:
        out: Data = self.query('?6')
        valve_position = out.data[2] if len(out.data) > 2 else ''
        return valve_position
    
    def getAcceleration(self) -> int:
        out: Data = self.query('?7')
        acceleration = out.data[2:] if len(out.data) > 2 else 0
        return acceleration
    
    def getInitStatus(self) -> bool:
        out: Data = self.query('?19')
        init = bool(out.data[2:]) if len(out.data) > 2 else False
        return init
    
    def getPumpConfig(self) -> str:     #TODO
        out: Data = self.query('?76')
        return out.data
    
    # Setter methods
    def setStartSpeed(self, speed: int, *, immediate: bool = True):
        speed = round(speed)
        assert (0<=speed<=1000), f"Start speed must be an integer between 0 and 1000"
        command = f'v{speed}'
        if immediate:
            self.run(command)
        else:
            self.command_buffer += command
        return

    def setTopSpeed(self, speed: int, *, immediate: bool = True):
        speed = round(speed)
        assert (0<=speed<=6000), f"Start speed must be an integer between 0 and 6000"
        command = f'V{speed}'
        if immediate:
            self.run(command)
        else:
            self.command_buffer += command
        return
    
    def setValvePosition(self, valve: str, *, immediate: bool = True):
        assert len(valve)==1 and (valve in 'IOBE'), f"Valve must be one of 'I', 'O', 'B', or 'E'"
        if immediate:
            self.run(valve)
        else:
            self.command_buffer += valve
        return
    
    def setAcceleration(self, acceleration: int, *, immediate: bool = True):
        assert (2500<=acceleration_code<=50_000), f"Acceleration code must be an integer between 2,500 and 50,000"
        acceleration_code = int(acceleration/2500)
        command = f'L{acceleration_code}'
        if immediate:
            self.run(command)
        else:
            self.command_buffer += command
        return
    
    # Actions
    def initialize(self, output_right: bool, *, immediate: bool = True):
        mode = 'Z' if output_right else 'Y'
        if immediate:
            self.run(mode)
        else:
            self.command_buffer += mode
        self.output_right = output_right
        return
    
    def reverse(self, *, immediate: bool = True):
        assert self.output_right is not None, "Pump must be initialized first!"
        self.initialize(not self.output_right, immediate=immediate)
        return
    
    def wait(self, duration: int|float, *, immediate: bool = True):
        duration_ms = round(duration * 1000)
        assert 0<=duration_ms<=30_000, "Duration must be between 0 and 30"
        command = f'M{duration_ms}'
        if immediate:
            self.run(command)
        else:
            self.command_buffer += command
        return
    
    def repeat(self, cycles: int):
        assert 0<=cycles<=30_000, "Cycles must be between 0 and 30,000"
        self.command_buffer = f'g{self.command_buffer}G{cycles}'
        return
    
    def run(self, command: str|None = None):
        command = command or self.command_buffer
        self.query(f'{command}R')
        self.command_buffer = ''
        self.flags.busy = True
        while self.flags.busy:
            time.sleep(0.1)
            self.getStatus()
        self.getStatus()
        self.getPosition()
        return
    
    def stop(self) :
        self.query('T')
        return
    
    # Plunger actions
    def aspirate(self, steps:int, *, blocking: bool = True, immediate: bool = True):
        steps = round(steps)
        assert steps >= 0, "Ensure non-negative steps!"
        self.setValvePosition('I', immediate=False)
        self.moveBy(steps, blocking=blocking, immediate=False)
        if immediate:
            self.run()
        return
    
    def dispense(self, steps:int, *, blocking: bool = True, immediate: bool = True) -> str:
        steps = round(steps)
        assert steps >= 0, "Ensure non-negative steps!"
        self.setValvePosition('O', immediate=False)
        self.moveBy(-steps, blocking=blocking, immediate=False)
        if immediate:
            self.run()
        return
    
    def move(self, steps:int, *, blocking: bool = True, immediate: bool = True):
        return self.moveBy(steps, blocking=blocking, immediate=immediate)
    
    def moveBy(self, steps: int, *, blocking: bool = True, immediate: bool = True):
        steps = round(steps)
        assert (0<=(self.position+steps)<=self.max_position), "Range limits reached!"
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
        position = round(position)
        assert (0<=position<=self.max_position), f"Position must be an integer between 0 and {self.max_position}"
        prefix = 'A' if blocking else 'a'
        command = f'{prefix}{position}'
        if immediate:
            self.run(command)
        else:
            self.command_buffer += command
        self.position = position
        return
    