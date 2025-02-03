# -*- coding: utf-8 -*-
# Standard library imports
from __future__ import annotations
import logging
from typing import NamedTuple, Any

# Local application imports
from ......core.device import SerialDevice

_logger = logging.getLogger("controllably.Transfer")
_logger.debug(f"Import: OK <{__name__}>")

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
logger.addHandler(handler)

READ_FORMAT = "/{channel}{data}\x03{_checksum}\r"     # response template: <PRE><STRING><POST>
WRITE_FORMAT = '/{channel}{data}\r'         # command template: <PRE><ADR><STRING><POST>
Data = NamedTuple("Data", [("data", str)])
BoolData = NamedTuple("BoolData", [("data", bool)])
FloatData = NamedTuple("FloatData", [("data", float)])
IntData = NamedTuple("IntData", [("data", int)])

class TriContinentDevice(SerialDevice):
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
        self.total_cycles = 0
        self.volume_resolution = 1
        
        self.channel = 1
        self.position = 0
        self.speed_code_in = 3
        self.speed_code_out = 3
        self.status = 0
        
        # self.response_time = response_time
        self.command_buffer = []
        return

    # Properties
    
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
            out: Data = Data(out.data.split('\x03')[0])
            
            if self.flags.simulation:
                data_out = data_type('') if data_type.__annotations__['data'] == str else data_type(0)
            else:
                data_out = self.processOutput(out.data, format=format_out, data_type=data_type)
                data_out = data_out if timestamp else data_out[0]
            all_output.append((data_out, now) if timestamp else data_out)
        return all_output if multi_out else all_output[0]
    
    
    def setChannel(self, channel:int):
        assert channel in list(range(15)), "Channel must be an integer between 0 and 15"
        self.channel = channel
        return
    
    # Getter methods
    def getPosition(self) -> int:
        out: IntData = self.query('?', data_type=IntData, channel=self.channel)
        return out.data
    
    def getInfo(self) -> str:
        out: Data = self.query('&', data_type=Data, channel=self.channel)
        self.info = out.data
        self.model = out.data.split(':')[0].strip()
        self.version = out.data.split(':')[1].strip()
        return out.data

    def getStartSpeed(self) -> int:
        out: IntData =  self.query('?1', data_type=Data, channel=self.channel)
        return out.data

    def getTopSpeed(self) -> int:
        out: IntData = self.query('?2', data_type=Data, channel=self.channel)
        return out.data
    
    def getValvePosition(self) -> str:
        out: Data = self.query('?6', data_type=Data, channel=self.channel)
        return out.data
    
    def getAcceleration(self) -> int:
        out: IntData = self.query('?7', data_type=Data, channel=self.channel)
        return out.data
    
    def getStatus(self) -> str: # TODO
        out: Data = self.query('Q', data_type=Data, channel=self.channel)
        return out.data
    
    def getInitStatus(self) -> str:
        out: Data = self.query('?19', data_type=Data, channel=self.channel)
        return out.data
    
    def getPumpConfig(self) -> str:
        out: Data = self.query('?76', data_type=Data, channel=self.channel)
        return out.data
    
    # Setter methods
    def setPosition(self, *, blocking: bool = True) -> int:
        command = 'A' if blocking else 'a'
        out: IntData = self.query(command, data_type=IntData, channel=self.channel)
        return out.data

    def getStartSpeed(self) -> int:
        command = 'v'
        out: IntData =  self.query('?1', data_type=Data, channel=self.channel)
        return out.data

    def setTopSpeed(self) -> int:
        command = 'V'
        out: IntData = self.query('?2', data_type=Data, channel=self.channel)
        return out.data
    
    def setValvePosition(self) -> str:
        
        out: Data = self.query('?6', data_type=Data, channel=self.channel)
        return out.data
    
    def getAcceleration(self) -> int:
        out: IntData = self.query('?7', data_type=Data, channel=self.channel)
        return out.data
    
    def getStatus(self) -> str: # TODO
        out: Data = self.query('Q', data_type=Data, channel=self.channel)
        return out.data
    
    def getInitStatus(self) -> str:
        out: Data = self.query('?19', data_type=Data, channel=self.channel)
        return out.data
    
    def getPumpConfig(self) -> str:
        out: Data = self.query('?76', data_type=Data, channel=self.channel)
        return out.data
    
    def stop(self) -> str:
        out: Data = self.query('T', data_type=Data, channel=self.channel)
        return out.data
    
    