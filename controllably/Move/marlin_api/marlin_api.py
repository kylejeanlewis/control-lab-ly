# -*- coding: utf-8 -*-
# Standard library imports
from __future__ import annotations
import logging
import time
from typing import Any

# Third-party imports
import numpy as np

# Local application imports
from ...core.connection import SerialDevice
from ...core.position import Position

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
        logger.warning('Marlin firmware is not fully supported. Proceed with care.')        # TODO: Remove warning when fully supported
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
        self._home_offset = np.array([0,0,0])
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
        # super().verbose = value
        self.flags.verbose = value
        level = logging.INFO if value else logging.WARNING
        logger.setLevel(level)
        for handler in logger.handlers:
            if isinstance(handler, type(logging.StreamHandler())):
                handler.setLevel(level)
        return
    
    def checkInfo(self) -> dict[str, str]:
        """
        """
        responses = self.query('M115')  # FIRMWARE_NAME:Marlin 2.1.3 (Aug  1 2024 12:00:00) SOURCE_CODE_URL:github.com/MarlinFirmware/Marlin PROTOCOL_VERSION:1.0 MACHINE_TYPE:3D Printer KINEMATICS:Cartesian EXTRUDER_COUNT:1 UUID:cede2a2f-41a2-4748-9b12-c55c62f367ff
        info = {}
        start = False
        for response in responses:
            response = response.strip().replace('Cap:','')
            if 'FIRMWARE_NAME' in response:
                start = True
            if not start:
                continue
            if response == 'ok':
                break
            parts = response.split(":")
            info[parts[0]] = ' '.join(parts[1:])
        return info
    
    def checkSettings(self) -> dict[str, int|float|str]:
        """
        """
        self.clear()
        responses = self.query('M503')
        while len(responses) == 0 or 'fail' in responses[-1]:
            time.sleep(0.1)
            responses = self.read(True)
        settings = {}
        for response in responses:
            response = response.replace('echo:','').split(';')[0].strip()
            if not len(response):
                continue
            if response[0] not in ('G','M'):
                continue
            if not response[1].isdigit():
                continue
            out = response.split(" ")
            setting = out[0]
            values = out[1:] if len(out) > 1 else ['']
            if len(values) == 1:
                settings[setting] = values[0]
                continue
            value_dict = {}
            for value in values:
                k,v = value[0], value[1:]
                negative = v.startswith('-')
                if negative:
                    v = v[1:]
                v: int|float|str = int(v) if v.isnumeric() else (float(v) if v.replace('.','',1).isdigit() else v)
                value_dict[k] = v * ((-1)**int(negative)) if isinstance(v, (int,float)) else v
            logger.info(f"[{setting}]: {value_dict}")
            settings[setting] = value_dict
        settings['max_speed_x'] = settings['M203']['X'] * 60
        settings['max_speed_y'] = settings['M203']['Y'] * 60
        settings['max_speed_z'] = settings['M203']['Z'] * 60
        settings['home_offset_x'] = settings['M206']['X']
        settings['home_offset_y'] = settings['M206']['Y']
        settings['home_offset_z'] = settings['M206']['Z']
        # settings['limit_x'] = settings['$130']
        # settings['limit_y'] = settings['$131']
        # settings['limit_z'] = settings['$132']
        # settings['homing_pulloff'] = settings['$27']
        return settings
    
    def checkStatus(self) -> tuple[str, np.ndarray[float], np.ndarray[float]]:  # TODO: Implement status check
        """
        """
        responses = self.query('M114 R')      # Check the current position
        # responses = self.query('M105')      # Check the current temperature
        status,current_position = 'Idle', np.array([0,0,0])
        # relevant_responses = []
        if self.flags.simulation:
            return 'Idle', current_position, self._home_offset
        # for response in responses:
        #     response = response.strip()
        #     if 'Count' not in response:
        #         continue
        #     relevant_responses.append(response)
        # xyz = relevant_responses[-1].split("E")[0].split(" ")[:-1]
        # current_position = [float(c[2:]) for c in xyz]
        
        return (status, current_position, self._home_offset)
    
    def halt(self) -> Position:
        """
        """
        self.query('M410')
        time.sleep(1)
        _,coordinates,_home_offset = self.checkStatus()
        return Position(coordinates-_home_offset)
    
    # Overwritten methods
    def connect(self):
        """
        """
        super().connect()
        startup_lines = self.read(True)
        for line in startup_lines:
            if line.startswith('Marlin'):
                self._version = line.split(" ")[-1]
                break
        settings = self.checkSettings()
        self._home_offset = np.array([settings.get('home_offset_x',0),settings.get('home_offset_y',0),settings.get('home_offset_z',0)])
        
        print(startup_lines)
        print(f'Marlin version: {self._version}')
        return
    
    def query(self, data: Any, lines:bool = True) -> list[str]|None:
        """
        """
        # data = data.replace('G1', 'G0')   # TODO: check if this is necessary
        if data.startswith('F'):
            data = f'G0 {data}'
        responses = super().query(data)
        # for response in responses:
        #     logger.debug(f"Response: {response}")
        #     self.checkAlarms(response)
        #     self.checkErrors(response)
        return responses

    # Methods not implemented
    def checkAlarms(self, response: str) -> bool:           # NOTE: This method is not implemented
        """
        """
        logger.debug(f"[{self.__class__.__name__}] Not implemented")
        return False
    
    def checkErrors(self, response: str) -> bool:           # NOTE: This method is not implemented
        """
        """
        logger.debug(f"[{self.__class__.__name__}] Not implemented")
        return False
    
    def checkParameters(self) -> dict[str, list[float]]:    # NOTE: This method is not implemented
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
    
    def checkState(self) -> dict[str, str]:                 # NOTE: This method is not implemented
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
    
    def clearAlarms(self):                                  # NOTE: This method is not implemented
        """
        """
        logger.debug(f"[{self.__class__.__name__}] Not implemented")
        # self.query('$X')
        return
    
    def resume(self):                                       # NOTE: This method is not implemented
        """
        """
        logger.debug(f"[{self.__class__.__name__}] Not implemented")
        # self.query('~')
        return
    