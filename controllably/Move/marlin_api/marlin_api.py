# -*- coding: utf-8 -*-
""" 
This module provides a class to interact with the Marlin firmware.

Attributes:
    LOOP_INTERVAL (float): loop interval for checking status
    MOVEMENT_TIMEOUT (int): timeout for movement
    READ_FORMAT (str): read format for serial communication
    WRITE_FORMAT (str): write format for serial communication
    Data (NamedTuple): data structure for serial communication
    
## Classes:
    `Marlin`: Marlin class provides methods to interact with the Marlin firmware.
"""
# Standard library imports
from __future__ import annotations
import time
from typing import Any, NamedTuple

# Third-party imports
import numpy as np

# Local application imports
from ...core.device import SerialDevice, AnyDevice
from ...core.position import Position

LOOP_INTERVAL = 0.1
MOVEMENT_TIMEOUT = 30

READ_FORMAT = "{data}\n"
WRITE_FORMAT = "{data}\n"
Data = NamedTuple("Data", [("data", str), ("channel", int)])

class Marlin(SerialDevice):
    """
    Marlin class provides methods to interact with the Marlin firmware.
    Refer to https://marlinfw.org/meta/gcode/ for more information on the Marlin firmware.
    
    ### Constructor:
        `port` (str|None): Serial port to connect to. Defaults to None.
        `baudrate` (int): baudrate for serial communication. Defaults to 115200.
        `timeout` (int): timeout for serial communication. Defaults to 1.
        `init_timeout` (int): timeout for initialization of serial communication. Defaults to 2.
        `message_end` (str): message end character for serial communication. Defaults to '\n'.
        `simulation` (bool): simulation mode for testing. Defaults to False.
        
    ### Attributes and properties:
        `port` (str): device serial port
        `baudrate` (int): device baudrate
        `timeout` (int): device timeout
        `connection_details` (dict): connection details for the device
        `serial` (serial.Serial): serial object for the device
        `init_timeout` (int): timeout for initialization
        `message_end` (str): message end character
        `flags` (SimpleNamespace[str, bool]): flags for the device
        `is_connected` (bool): whether the device is connected
        `verbose` (bool): verbosity of class
        
    ### Methods:
        `getInfo`: Query device information
        `getSettings`: Query device settings
        `getStatus`: Query device status
        `halt`: Halt the device
        `home`: Home the device
        `setSpeedFactor`: Set the speed factor in the device
        `connect`: Connect to the device
        `query`: Query the device (i.e. write and read data)
        `clear`: clear the input and output buffers
        `connect`: connect to the device
        `disconnect`: disconnect from the device
        `read`: read data from the device
        `write`: write data to the device
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
        self.clearDeviceBuffer()
        time.sleep(1)
        responses = self.query('M503')
        while len(responses)==0 or 'ok' not in responses[-1]:
            time.sleep(1)
            chunk = self.readAll()
            responses.extend(chunk)
        settings = {}
        if self.flags.simulation:
            return settings
        self._logger.debug(responses)
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
        settings['max_accel_x'] = settings.get('M201',{}).get('X',0)
        settings['max_accel_y'] = settings.get('M201',{}).get('Y',0)
        settings['max_accel_z'] = settings.get('M201',{}).get('Z',0)
        settings['max_speed_x'] = settings.get('M203',{}).get('X',0)
        settings['max_speed_y'] = settings.get('M203',{}).get('Y',0)
        settings['max_speed_z'] = settings.get('M203',{}).get('Z',0)
        settings['home_offset_x'] = settings.get('M206',{}).get('X',0)
        settings['home_offset_y'] = settings.get('M206',{}).get('Y',0)
        settings['home_offset_z'] = settings.get('M206',{}).get('Z',0)
        return settings
    
    def getStatus(self) -> tuple[str, np.ndarray[float], np.ndarray[float]]:  # TODO: Implement status check
        """
        Query device status
        
        Returns:
            tuple[str, np.ndarray[float], np.ndarray[float]]: status, current position, home offset
        """
        self.clearDeviceBuffer()
        responses = self.query('M114 R', multi_out=False)
        self.clearDeviceBuffer()
        
        status,current_position = 'Idle', np.array([0,0,0])
        # responses = self.query('M105', multi_out=False)      # Check the current temperature
        if self.flags.simulation:
            return status, current_position, self._home_offset
        while len(responses)==0 or 'ok' not in responses[-1]:
            time.sleep(1)
            chunk = self.readAll()
            responses.extend(chunk)
        relevant_responses = []
        for response in responses:
            response = response.strip()
            if 'Count' not in response:
                continue
            relevant_responses.append(response)
        xyz = relevant_responses[-1].split("E")[0].split(" ")[:-1]
        current_position = [float(c[2:]) for c in xyz]
        return status, current_position, self._home_offset
    
    def halt(self) -> Position:         # TODO: Check if this is the correct implementation
        """
        Halt the device
        
        Returns:
            Position: current position of the device
        """
        self.query('M410', multi_out=False)
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
        axis = '' if axis is None else axis.upper()
        self.query('G90', multi_out=False)
        
        data = f'G28 {axis}'
        self.query(data, multi_out=False)
        self.clearDeviceBuffer()
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
        # self.query(data, multi_out=False)
        speed_percent = speed_factor*100
        data = f'M220 S{int(speed_percent)}'
        self.query(data, multi_out=False)
        return
    
    # Overwritten methods
    def connect(self):
        """Connect to the device"""
        super().connect()
        startup_lines = self.readAll()
        for line in startup_lines:
            if line.startswith('Marlin'):
                self._version = line.split(" ")[-1]
                break
        settings = self.getSettings()
        self._home_offset = np.array([settings.get('home_offset_x',0),settings.get('home_offset_y',0),settings.get('home_offset_z',0)])
        
        self._logger.info(startup_lines)
        self._logger.info(f'Marlin version: {self._version}')
        return
    
    def query(self, 
        data: Any, 
        multi_out: bool = True, 
        *,
        timeout:int|float = 1, 
        wait: bool = False, 
        **kwargs
    ) -> list[str]|None:
        """
        Query the device (i.e. write and read data)
        
        Args:
            data (Any): data to write to the device
            multi_out (bool): whether to read multiple lines of data. Defaults to True.
            timeout (int|float): timeout for reading data. Defaults to 1.
            wait (bool): whether to wait for the device to be idle. Defaults to False.
            
        Returns:
            list[str]|None: response from the device
        """
        if data.startswith('F'):
            data = f'G1 {data}'
        out: Data|list[Data] = super().query(data, multi_out=multi_out, timeout=timeout, **kwargs)
        if isinstance(out,list):
            data_out = [(response.data if response is not None else None) for response in out]
        else:
            data_out = [(out.data if out is not None else None)]
        if wait:
            ...
            # success = self._wait_for_idle()
            # if not success:
            #     self._logger.error(f"Timeout: {data}")
            #     return []
        return data_out
    
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
