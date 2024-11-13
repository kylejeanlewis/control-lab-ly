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

LOOP_INTERVAL = 0.1
MOVEMENT_BUFFER = 1
MOVEMENT_TIMEOUT = 30

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
        responses = self.query('M115')
        info = {}
        if self.flags.simulation:
            return info
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
        settings = {}
        if self.flags.simulation:
            return settings
        while len(responses) == 0 or 'fail' in responses[-1]:
            time.sleep(0.1)
            responses = self.read(True)
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
        settings['max_accel_x'] = settings['M201']['X']
        settings['max_accel_y'] = settings['M201']['Y']
        settings['max_accel_z'] = settings['M201']['Z']
        settings['max_speed_x'] = settings['M203']['X'] * 60
        settings['max_speed_y'] = settings['M203']['Y'] * 60
        settings['max_speed_z'] = settings['M203']['Z'] * 60
        settings['home_offset_x'] = settings['M206']['X']
        settings['home_offset_y'] = settings['M206']['Y']
        settings['home_offset_z'] = settings['M206']['Z']
        return settings
    
    def checkStatus(self) -> tuple[str, np.ndarray[float], np.ndarray[float]]:  # TODO: Implement status check
        """
        """
        self.clear()
        responses = self.query('M114 R')
        settings = {}
        if self.flags.simulation:
            return settings
        while len(responses) == 0 or 'fail' in responses[-1]:
            time.sleep(0.1)
            responses = self.read(True)
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
    
    def halt(self) -> Position:         # TODO: Check if this is the correct implementation
        """
        """
        self.query('M410')
        time.sleep(1)
        _,coordinates,_home_offset = self.checkStatus()
        return Position(coordinates-_home_offset)
    
    def home(self, axis: str|None = None, **kwargs) -> bool:
        """
        """
        if axis is not None:
            logger.warning("Ignoring homing axis parameter for Marlin firmware")
        self.query('G90')
        self.query('G28', wait=True)
        return True
    
    def setSpeedFactor(self, speed_factor:float, **kwargs):
        assert isinstance(speed_factor, float), "Ensure speed factor is a float"
        assert (0.0 <= speed_factor <= 1.0), "Ensure speed factor is between 0.0 and 1.0"
        speed_percent = speed_factor*100
        self.query(f'M220 S{int(speed_percent)}')
        return
    
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
    
    def query(self, data: Any, lines:bool = True, *, wait:bool = False, **kwargs) -> list[str]|None:
        """
        """
        # data = data.replace('G1', 'G0')   # TODO: check if this is necessary
        if data.startswith('F'):
            data = f'G0 {data}'
        if not wait:
            self.write(data)
            return self.read(lines=False)
        
        responses = super().query(data, lines=lines)
        success = self._wait_for_idle()
        if not success:
            logger.error(f"Timeout: {data}")
            return []
        return responses
    
    def _wait_for_idle(self, timeout:int = MOVEMENT_TIMEOUT) -> bool:
        """
        """
        if not self.is_connected or self.flags.simulation:
            return True
        start_time = time.perf_counter()
        while True:
            time.sleep(LOOP_INTERVAL)
            responses = self.read()
            if len(responses) and responses[-1] != b'echo:busy: processing\n':
                break
            if time.perf_counter() - start_time > timeout:
                return False
        return True

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
    