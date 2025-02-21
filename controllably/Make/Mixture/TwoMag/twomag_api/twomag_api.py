# -*- coding: utf-8 -*-
"""
"""
# Standard library imports
from __future__ import annotations
import logging
import string
from typing import NamedTuple, Any

# Local application imports
from .....core.device import SerialDevice
from .twomag_lib import ErrorCodes

logger = logging.getLogger("controllably.Make")
logger.debug(f"Import: OK <{__name__}>")

READ_FORMAT = "{status}_{data}_{address}\r"
WRITE_FORMAT = "{data}_{address}\r"
Data = NamedTuple("Data", [("data", str), ("status", str), ("address", str)])

class MIXControlMTP(SerialDevice):
    
    _default_speed = 350
    _default_power = 50
    def __init__(self,
        port: str|None = None, 
        baudrate: int = 9600, 
        timeout: int = 1, 
        *,
        init_timeout: int = 5, 
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
        
        self.address = 'A'
        self.version = ''
        self.mode = ''
        
        self.speed = self._default_speed
        self.power = self._default_power
        return
    
    def getStatus(self) -> tuple[str,str]:
        out: Data = self.query(f'sendstatus', address=self.address)
        status = out.data
        version_mode = status.split('_')
        if len(version_mode) == 2:
            self.version = version_mode[0]
            self.mode = version_mode[1]
        return self.version, self.mode
    
    def start(self) -> bool:
        out: Data = self.query(f'start', address=self.address)
        data = out.data
        return data == 'START'
    
    def stop(self) -> bool:
        out: Data = self.query(f'stop', address=self.address)
        data = out.data
        return data == 'STOP'
        
    def setSpeed(self, speed: int) -> int:
        assert 100<=speed<=2000, f"Speed out of range (100-2000) : {speed}"
        speed = int(round(speed, -1))       # round to nearest 10
        out: Data = self.query(f'setrpm_{int(speed)}', address=self.address)
        data = out.data
        set_speed = int(data.replace('RPM','').lstrip("0"))
        self.speed = set_speed
        return set_speed
        
    def getSpeed(self) -> int:
        out: Data = self.query(f'sendrpm', address=self.address)
        data = out.data
        set_speed = int(data.replace('RPM','').lstrip("0"))
        self.speed = set_speed
        return set_speed
        
    def setPower(self, power: int) -> int:
        assert 25<=power<=100, f"Speed out of range (25-100) : {power}"
        power = round(power/25) * 25       # round to nearest 25
        out: Data = self.query(f'setpower_{int(power)}', address=self.address)
        data = out.data
        set_power = int(data.replace('POWER','').lstrip("0"))
        self.power = set_power
        return set_power
        
    def getPower(self) -> int:
        out: Data = self.query(f'sendpower', address=self.address)
        data = out.data
        set_power = int(data.replace('POWER','').lstrip("0"))
        self.power = set_power
        return set_power
        
    def setDefault(self) -> bool:
        out: Data = self.query(f'setdefault', address=self.address)
        data = out.data
        self.speed = self._default_speed
        self.power = self._default_power
        return data == 'SETDEFAULT'
    
    def setAddress(self, address: str) -> bool:
        assert address in string.ascii_uppercase, f"Invalid address : {address}"
        out: Data = self.query(f'setadd_{address}', address=self.address)
        old_address = out.data
        new_address = out.address
        success = (old_address == self.address) and (new_address == address)
        if success:
            self.address = address
        return success
    
    def query(self, 
        data: Any, 
        multi_out: bool = False,
        *,
        timeout: int|float = 0.3,
        format_in: str|None = None, 
        format_out: str|None = None,
        data_type: NamedTuple|None = None,
        timestamp: bool = False,
        **kwargs
    ) -> Any:
        out: Data = super().query(
            data, multi_out, timeout=timeout, 
            format_in=format_in, format_out=format_out, 
            data_type=data_type, timestamp=timestamp, **kwargs
        )
        
        if out.status == 'ER':
            error = ErrorCodes[out.data]
            logger.error(f"Error: {error}")
        return out
        