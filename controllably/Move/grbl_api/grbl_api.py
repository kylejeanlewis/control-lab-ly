# -*- coding: utf-8 -*-
# Standard library imports
from __future__ import annotations
import logging
from typing import Any

# Local application imports
from ...core.connection import SerialDevice
from ...core.position import Position
from .grbl_lib import Alarm, Error, Setting, Status

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.debug(f"Import: OK <{__name__}>")

class GRBL(SerialDevice):
    """
    Refer to https://github.com/gnea/grbl/tree/master/doc/markdown for more information on the GRBL firmware.
    """
    def __init__(self,
        port: str|None = None, 
        baudrate: int = 9600, 
        timeout: int = 1, 
        init_timeout: int = 2,
        message_end: str = '\n',
        *args,
        simulation: bool = False,
        **kwargs
    ):
        """
        """
        super().__init__(
            port=port, 
            baudrate=baudrate, 
            timeout=timeout, 
            init_timeout=init_timeout,
            message_end=message_end,
            *args,
            simulation=simulation,
            **kwargs
        )
        self._version = '1.1' if simulation else ''
        return
    
    def __version__(self) -> str:
        return self._version
    
    @property
    def verbose(self) -> bool:
        """Get verbosity of class"""
        return self.flags.verbose
    @verbose.setter
    def verbose(self, value:bool):
        """Set verbosity of class"""
        assert isinstance(value,bool), "Ensure assigned verbosity is boolean"
        super().flags.verbose = value
        self.flags.verbose = value
        level = logging.INFO if value else logging.WARNING
        logger.setLevel(level)
        for handler in logger.handlers:
            if isinstance(handler, type(logging.StreamHandler())):
                handler.setLevel(level)
        return
    
    def checkAlarms(self, response: str):
        """
        """
        if 'ALARM' not in response:
            return
        alarm_id = response.strip().split(":")[1]
        alarm_int = int(alarm_id) if alarm_id.isnumeric() else alarm_id
        alarm_ = f'ac{alarm_int:02}'
        assert alarm_ in Alarm.__members__, f"Alarm not found: {alarm_}"
        logger.warning(f"ALARM {alarm_int:02}: {Alarm[alarm_].value.message}")
        return
    
    def checkErrors(self, response: str):
        """
        """
        if 'error' not in response:
            return
        error_id = response.strip().split(":")[1]
        error_int = int(error_id) if error_id.isnumeric() else error_id
        error_ = f'er{error_int:02}'
        assert error_ in Error.__members__, f"Error not found: {error_}"
        logger.warning(f"ERROR {error_int:02}: {Error[error_].value.message}")
        return
    
    def checkParameters(self) -> list[tuple[str, list[float]]]:
        """
        """
        responses = self.query('$#')
        parameters = []
        for response in responses:
            response = response.strip()
            if not (response.startswith('[') and response.endswith(']')):
                continue
            response = response[1:-1]
            if response.startswith('PRB'):
                continue
            parameter,values = response.split(":")
            values = [float(c) for c in values.split(",")]
            parameters.append((parameter, values))
        return parameters
    
    def checkSettings(self) -> list[tuple[str, str]]:
        """
        """
        responses = self.query('$$')
        settings = []
        for response in responses:
            response = response.strip()
            if '=' not in response:
                continue
            setting,value = response.split("=")
            setting_int = int(setting[1:]) if setting[1:].isnumeric() else setting[1:]
            setting_ = f'sc{setting_int}'
            assert setting_ in Setting.__members__, f"Setting  not found: {setting_}"
            logger.info(f"[{setting}]: {Setting[setting_].value.message} = {value}")
            settings.append((setting, value))
        return settings
    
    def checkState(self) -> dict[str, str]:
        """
        """
        responses = self.query('$G')
        state = dict()
        for response in responses:
            response = response.strip()
            if not (response.startswith('[') and response.endswith(']')):
                continue
            response = response[1:-1]
            if not response.startswith('GC:'):
                continue
            state_parts = response[3:].split(' ')
            state.update(dict(
                motion_mode =  state_parts[0],
                coordinate_system = state_parts[1],
                plane = state_parts[2],
                units_mode = state_parts[3],
                distance_mode = state_parts[4],
                feed_rate = state_parts[5]
            ))
        return state
    
    def checkStatus(self) -> tuple[str, list[float]]:
        """
        """
        responses = self.query('?')
        for response in responses:
            response = response.strip()
            if not (response.startswith('<') and response.endswith('>')):
                continue
            response = response[1:-1]
            status_parts = response.split('|')
            state = status_parts[0].split(':')[0]
            logger.info(f"{state}: {Status[state].value}")
            current_position = [float(c) for c in status_parts[1].split(':')[1].split(',')]
        return (state, current_position)
    
    def clearAlarms(self):
        """
        """
        self.query('$X')
        return
    
    def halt(self) -> Position:
        """
        """
        self.query('!')
        _,coordinates = self.checkStatus()
        return Position(coordinates)
    
    def resume(self):
        """
        """
        self.query('~')
        return
    
    # Overwritten methods
    def connect(self):
        """
        """
        super().connect()
        startup_lines = self.read(True)
        self._version = startup_lines[0].split(' ')[1]
        return
    
    def query(self, data: Any) -> list[str]:
        """
        """
        responses = super().query(data)
        for response in responses:
            logger.debug(f"Response: {response}")
            self.checkAlarms(response)
            self.checkErrors(response)
        return responses
