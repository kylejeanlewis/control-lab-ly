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
logger.debug(f"Import: OK <{__name__}>")

LOOP_INTERVAL = 0.1
MOVEMENT_TIMEOUT = 30

class Marlin(SerialDevice):
    """
    Marlin class provides methods to interact with the Marlin firmware.
    Refer to https://marlinfw.org/meta/gcode/ for more information on the Marlin firmware.
    """
    
    def __init__(self,
        port: str|None = None, 
        baudrate: int = 115200, 
        timeout: int = 1, 
        init_timeout: int = 2,
        message_end: str = '\n',
        *args,
        simulation: bool = False,
        **kwargs
    ):
        """
        Initialize Marlin class
        
        Args:
            port (str|None): Serial port to connect to. Defaults to None.
            baudrate (int): baudrate for serial communication. Defaults to 115200.
            timeout (int): timeout for serial communication. Defaults to 1.
            init_timeout (int): timeout for initialization of serial communication. Defaults to 2.
            message_end (str): message end character for serial communication. Defaults to '\n'.
            simulation (bool): simulation mode for testing. Defaults to False.
        """
        logger.warning('Marlin firmware support still under development. Proceed with care.')        # TODO: Remove warning when fully supported
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
    
    def getInfo(self) -> dict[str, str]:
        """
        Query device information
        
        Returns:
            dict[str, str]: information in the response
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
    
    def getSettings(self) -> dict[str, int|float|str]:
        """
        Query device settings
        
        Returns:
            dict[str, int|float|str]: settings in the response
        """
        self.clear()
        responses = self.query('M503')
        settings = {}
        if self.flags.simulation:
            return settings
        while len(responses) == 0 or 'fail' in responses[-1]:
            time.sleep(LOOP_INTERVAL)
            try:    # NOTE: temporary for transition to new SerialDevice
                responses = self.readAll()
            except:
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
            self._logger.debug(f"[{setting}]: {value_dict}")
            settings[setting] = value_dict
        settings['max_accel_x'] = settings['M201']['X']
        settings['max_accel_y'] = settings['M201']['Y']
        settings['max_accel_z'] = settings['M201']['Z']
        settings['max_speed_x'] = settings['M203']['X']
        settings['max_speed_y'] = settings['M203']['Y']
        settings['max_speed_z'] = settings['M203']['Z']
        settings['home_offset_x'] = settings['M206']['X']
        settings['home_offset_y'] = settings['M206']['Y']
        settings['home_offset_z'] = settings['M206']['Z']
        return settings
    
    def getStatus(self) -> tuple[str, np.ndarray[float], np.ndarray[float]]:  # TODO: Implement status check
        """
        Query device status
        
        Returns:
            tuple[str, np.ndarray[float], np.ndarray[float]]: status, current position, home offset
        """
        self.clear()
        responses = self.query('M114 R', lines=False)
        # responses = self.query('M105')      # Check the current temperature
        if self.flags.simulation:
            return 'Idle', current_position, self._home_offset
        while len(responses) == 0 or 'fail' in responses[-1]:
            time.sleep(LOOP_INTERVAL)
            responses = self.read()
        
        status,current_position = 'Idle', np.array([0,0,0])
        relevant_responses = []
        for response in responses:
            response = response.strip()
            if 'Count' not in response:
                continue
            relevant_responses.append(response)
        xyz = relevant_responses[-1].split("E")[0].split(" ")[:-1]
        current_position = [float(c[2:]) for c in xyz]
        return (status, current_position, self._home_offset)
    
    def halt(self) -> Position:         # TODO: Check if this is the correct implementation
        """Halt the device"""
        self.query('M410')
        _,coordinates,_home_offset = self.getStatus()
        return Position(coordinates-_home_offset)
    
    def home(self, axis: str|None = None, **kwargs) -> bool:        # TODO: Test if single axis homing works
        """
        Home the device
        
        Args:
            axis (str|None): axis to home. Defaults to None.
            
        Returns:
            bool: whether the device was homed
        """
        # if axis is not None:
        #     self._logger.warning("Ignoring homing axis parameter for Marlin firmware")
        axis = '' if axis is None else f'{axis.upper()}'
        self.query('G90', lines=False)
        
        data = f'G28 {axis}'
        try:
            data = self.processInput(data)
        except:
            pass
        self.write(data)
        self.clear()
        while True:
            time.sleep(LOOP_INTERVAL)
            responses = self.read()
            if self.flags.simulation:
                break
            if not self.is_connected:
                break
            if len(responses) == 0:
                continue
            if 'Count' in responses:
                break
        time.sleep(2)
        return True
    
    def setSpeedFactor(self, speed_factor:float, *, speed_max:int, **kwargs):
        """
        Set the speed factor in the device
        
        Args:
            speed_factor (float): speed factor
            speed_max (int): maximum speed
        """
        assert isinstance(speed_factor, float), "Ensure speed factor is a float"
        assert (0.0 <= speed_factor <= 1.0), "Ensure speed factor is between 0.0 and 1.0"
        # feed_rate = int(speed_factor * speed_max) * 60      # Convert to mm/min
        # data = f'G90 F{feed_rate}'
        # try:
        #     data = self.processInput(data)
        # except:
        #     pass
        # self.write(data)
        speed_percent = speed_factor*100
        data = f'M220 S{int(speed_percent)}'
        try:
            data = self.processInput(data)
        except:
            pass
        self.write(data)
        self.read()
        return
    
    # Overwritten methods
    def connect(self):
        """Connect to the device"""
        super().connect()
        try:    # NOTE: temporary for transition to new SerialDevice
            startup_lines = self.readAll()
        except:
            startup_lines = self.read(True)
        for line in startup_lines:
            if line.startswith('Marlin'):
                self._version = line.split(" ")[-1]
                break
        settings = self.getSettings()
        self._home_offset = np.array([settings.get('home_offset_x',0),settings.get('home_offset_y',0),settings.get('home_offset_z',0)])
        
        self._logger.info(startup_lines)
        self._logger.info(f'Marlin version: {self._version}')
        return
    
    def query(self, data: Any, lines:bool = True, *, wait:bool = False, **kwargs) -> list[str]|None:
        """
        Query the device (i.e. write and read data)
        
        Args:
            data (Any): data to query
            lines (bool): whether to read lines
            wait (bool): whether to wait for the device to reach the status
            
        Returns:
            list[str]|None: response from the device
        """
        if data.startswith('F'):
            data = f'G1 {data}'
        if not wait:
            _data = data
            try:
                _data = self.processInput(_data)
            except:
                pass
            self.write(_data)
            return self.read(lines=lines)
        
        try:    # NOTE: temporary for transition to new SerialDevice
            responses = self.readAll() if lines else self.read()
        except:
            responses = super().query(data, lines=lines)
        # success = self._wait_for_idle()
        # if not success:
        #     self._logger.error(f"Timeout: {data}")
        #     return []
        return responses
    
    # def _wait_for_idle(self, timeout:int = MOVEMENT_TIMEOUT) -> bool:
    #     """
    #     """
    #     if not self.is_connected or self.flags.simulation:
    #         return True
    #     start_time = time.perf_counter()
    #     while True:
    #         time.sleep(LOOP_INTERVAL)
    #         responses = self.read()
    #         if len(responses) and 'echo:busy: processing' not in responses[-1]:
    #             break
    #         if time.perf_counter() - start_time > timeout:
    #             return False
    #     return True
