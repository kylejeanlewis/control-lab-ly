# -*- coding: utf-8 -*-
# Standard library imports
from __future__ import annotations
import logging
from typing import Any

# Local application imports
from ...core.connection import SerialDevice

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.debug(f"Import: OK <{__name__}>")

class Marlin(SerialDevice):
    """
    Refer to https://marlinfw.org/meta/gcode/ for more information on the Marlin firmware.
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
    
    def checkAlarms(self, response: str):   # NOTE: This method is not implemented
        """
        """
        logger.debug(f"[{self.__class__.__name__}] Not implemented")
        return
    
    def checkErrors(self, response: str):   # NOTE: This method is not implemented
        """
        """
        logger.debug(f"[{self.__class__.__name__}] Not implemented")
        return
    
    def checkParameters(self) -> list[tuple[str, list[float]]]:     # NOTE: This method is not implemented
        """
        """
        logger.debug(f"[{self.__class__.__name__}] Not implemented")
        # responses = self.query('$#')
        parameters = []
        # for response in responses:
        #     response = response.strip()
        #     if not (response.startswith('[') and response.endswith(']')):
        #         continue
        #     response = response[1:-1]
        #     if response.startswith('PRB'):
        #         continue
        #     parameter,values = response.split(":")
        #     values = [float(c) for c in values.split(",")]
        #     parameters.append((parameter, values))
        return parameters
    
    def checkSettings(self) -> list[tuple[str, str]]:               # TODO: Parse settings from responses
        """
        """
        relevant_settings = dict(
            M201 = 'Maximum Acceleration',
            M203 = 'Maximum Feedrate',
            # M204 = 'Acceleration',
            # M205 = 'Advanced Settings',
            # M206 = 'Home Offset',
            # M207 = 'Calibrate Z Axis',
        )
        responses = self.query('M503')
        settings = []
        for response in responses:
            response = response.strip()
        #     if '=' not in response:
        #         continue
        #     setting,value = response.split("=")
        #     setting_int = int(setting[1:]) if setting[1:].isnumeric() else setting[1:]
        #     setting_ = f'sc{setting_int}'
        #     assert setting_ in Setting.__members__, f"Setting  not found: {setting_}"
        #     logger.info(f"[{setting}]: {Setting[setting_].value.message} = {value}")
        #     settings.append((setting, value))
        return settings
    
    def checkState(self) -> dict[str, str]: # NOTE: This method is not implemented
        """
        """
        logger.debug(f"[{self.__class__.__name__}] Not implemented")
        # responses = self.query('$G')
        state = dict()
        # for response in responses:
        #     response = response.strip()
        #     if not (response.startswith('[') and response.endswith(']')):
        #         continue
        #     response = response[1:-1]
        #     if not response.startswith('GC:'):
        #         continue
        #     state_parts = response[3:].split(' ')
        #     state.update(dict(
        #         motion_mode =  state_parts[0],
        #         coordinate_system = state_parts[1],
        #         plane = state_parts[2],
        #         units_mode = state_parts[3],
        #         distance_mode = state_parts[4],
        #         feed_rate = state_parts[5]
        #     ))
        return state
    
    def checkStatus(self) -> tuple[str, list[float]]:
        """
        """
        responses = self.query('M114')      # Check the current position
        # responses = self.query('M105')      # Check the current temperature
        state = ''
        relevant_responses = []
        for response in responses:
            response = response.strip()
            if 'Count' not in response:
                continue
            relevant_responses.append(response)
        xyz = relevant_responses[-1].split("E")[0].split(" ")[:-1]
        current_position = [float(c[2:]) for c in xyz]
        return (state, current_position)
    
    def clearAlarms(self):                  # NOTE: This method is not implemented
        """
        """
        logger.debug(f"[{self.__class__.__name__}] Not implemented")
        # self.query('$X')
        return
    
    def halt(self):
        """
        """
        self.query('M410')
        return
    
    def resume(self):                       # NOTE: This method is not implemented
        """
        """
        logger.debug(f"[{self.__class__.__name__}] Not implemented")
        # self.query('~')
        return
    
    # Overwritten methods
    def connect(self):
        """
        """
        super().connect()
        startup_lines = self.read(True)
        # self._version = startup_lines[0].split(' ')[1]
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
