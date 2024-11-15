# -*- coding: utf-8 -*-
"""
GRBL API for controlling CNC machines using the GRBL firmware.
Refer to https://github.com/gnea/grbl/tree/master/doc/markdown for more information on the GRBL firmware.

Attributes:
    LOOP_INTERVAL (float): loop interval for device
    MOVEMENT_BUFFER (int): buffer time after movement
    MOVEMENT_TIMEOUT (int): timeout for movement
    
## Classes:
    `GRBL`: GRBL class for controlling CNC machines using the GRBL firmware.
    
<i>Documentation last updated: 2024-11-14</i>
"""
# Standard library imports
from __future__ import annotations
import logging
import time
from typing import Any, Sequence

# Third-party imports
import numpy as np

# Local application imports
from ...core.connection import SerialDevice
from ...core.position import Position
from .grbl_lib import Alarm, Error, Setting, Status

logger = logging.getLogger("controllably.Move")
logger.debug(f"Import: OK <{__name__}>")

LOOP_INTERVAL = 0.1
MOVEMENT_TIMEOUT = 30

class GRBL(SerialDevice):
    """
    GRBL class for controlling CNC machines using the GRBL firmware.
    Refer to https://github.com/gnea/grbl/tree/master/doc/markdown for more information on the GRBL firmware.
    
    ### Constructor
        `port` (str|None): Serial port to connect to. Default is None.
        `baudrate` (int): Baudrate of the serial connection. Default is 9600.
        `timeout` (int): Timeout for serial connection. Default is 1.
        `init_timeout` (int): Timeout for initialization of serial connection. Default is 2.
        `message_end` (str): Message end character for serial communication. Default is '\n'.
        `simulation` (bool): Simulation mode for testing. Default is False.
        
    ### Attributes and properties
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
        
    ### Methods
        `checkAlarms`: check for alarms in the response
        `checkErrors`: check for errors in the response
        `checkInfo`: query device information
        `checkParameters`: query device parameters
        `checkSettings`: query device settings
        `checkState`: query device state
        `checkStatus`: query device status
        `clearAlarms`: clear alarms in the response
        `halt`: halt the device
        `home`: home the device
        `resume`: resume activity on the device
        `setSpeedFactor`: set the speed factor in the device
        `clear`: clear the input and output buffers
        `connect`: connect to the device
        `disconnect`: disconnect from the device
        `query`: query the device (i.e. write and read data)
        `read`: read data from the device
        `write`: write data to the device
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
        self._home_offset = np.array([0,0,0])
        return
    
    def __version__(self) -> str:
        return self._version
    
    def checkAlarms(self, response: str) -> bool:
        """
        Checks for alarms in the response
        
        Args:
            response (str): response
            
        Returns:
            bool: whether an alarm was found
        """
        if 'ALARM' not in response:
            return False
        alarm_id = response.strip().split(":")[1]
        alarm_int = int(alarm_id) if alarm_id.isnumeric() else alarm_id
        alarm_ = f'ac{alarm_int:02}'
        assert alarm_ in Alarm.__members__, f"Alarm not found: {alarm_}"
        self._logger.warning(f"ALARM {alarm_int:02}: {Alarm[alarm_].value.message}")
        return True
    
    def checkErrors(self, response: str) -> bool:
        """
        Checks for errors in the response
        
        Args:
            response (str): response
            
        Returns:
            bool: whether an error was found
        """
        if 'error' not in response:
            return False
        error_id = response.strip().split(":")[1]
        error_int = int(error_id) if error_id.isnumeric() else error_id
        error_ = f'er{error_int:02}'
        assert error_ in Error.__members__, f"Error not found: {error_}"
        self._logger.warning(f"ERROR {error_int:02}: {Error[error_].value.message}")
        return True
    
    def checkInfo(self) -> list[str]:
        """
        Query device information
        
        Returns:
            list[str]: information in the response
        """
        self.clear()
        responses = self.query('$I')
        if self.flags.simulation:
            return ['GRBL:1.1']
        return responses
    
    def checkParameters(self) -> dict[str, list[float]]:
        """
        Query device parameters
        
        Returns:
            dict[str, list[float]]: parameters in the response
        """
        self.clear()
        responses = self.query('$#')
        parameters = {}
        if self.flags.simulation:
            return parameters
        for response in responses:
            response = response.strip()
            if not (response.startswith('[') and response.endswith(']')):
                continue
            response = response[1:-1]
            splits = response.split(":")
            parameter,values = splits[0],splits[1]
            if parameter in ('HOME','PRB') and len(splits)>2:
                values = ','.join([values, splits[2]])
            values = [float(c) for c in values.split(",")]
            parameters[parameter] = values
        return parameters
    
    def checkSettings(self) -> dict[str, int|float|str]:
        """
        Query device settings
        
        Returns:
            dict[str, int|float|str]: settings in the response
        """
        self.clear()
        responses = self.query('$$')
        settings = {}
        if self.flags.simulation:
            return settings
        for response in responses:
            response = response.strip()
            if '=' not in response or len(response) < 3:
                continue
            setting,value = response.split("=")
            setting_int = int(setting[1:]) if setting[1:].isnumeric() else setting[1:]
            setting_ = f'sc{setting_int}'
            if setting_ not in Setting.__members__:
                continue
            self._logger.debug(f"[{setting}]: {Setting[setting_].value.message} = {value}")
            negative = value.startswith('-')
            if negative:
                    value = value[1:]
            value: int|float|str = int(value) if value.isnumeric() else (float(value) if value.replace('.','',1).isdigit() else value)
            settings[setting] = value * ((-1)**int(negative)) if isinstance(value, (int,float)) else value
        settings['max_accel_x'] = settings.get('$120', 0)
        settings['max_accel_y'] = settings.get('$121', 0)
        settings['max_accel_z'] = settings.get('$122', 0)
        settings['max_speed_x'] = settings.get('$110', 0)/60
        settings['max_speed_y'] = settings.get('$111', 0)/60
        settings['max_speed_z'] = settings.get('$112', 0)/60
        settings['limit_x'] = settings.get('$130', 0)
        settings['limit_y'] = settings.get('$131', 0)
        settings['limit_z'] = settings.get('$132', 0)
        settings['homing_pulloff'] = settings.get('$27', 0)
        return settings
    
    def checkState(self) -> dict[str, str]:
        """
        Query device state
        
        Returns:
            dict[str, str]: state in the response
        """
        self.clear()
        responses = self.query('$G')
        state = {}
        if self.flags.simulation:
            return state
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
    
    def checkStatus(self) -> tuple[str, np.ndarray[float], np.ndarray[float]]:
        """
        Query device status
        
        Returns:
            tuple[str, np.ndarray[float], np.ndarray[float]]: status, current position, home offset
        """
        self.clear()
        responses = self.query('?',lines=False)
        self.clear()
        status,current_position = '', np.array([0,0,0])
        if self.flags.simulation:
            return 'Idle', current_position, self._home_offset
        for response in responses:
            response = response.strip()
            if not (response.startswith('<') and response.endswith('>')):
                continue
            response = response[1:-1]
            status_parts = response.split('|')
            status = status_parts[0].split(':')[0]
            self._logger.debug(f"{status}: {Status[status].value}")
            current_position = np.array([float(c) for c in status_parts[1].split(':')[1].split(',')])
        return (status, current_position, self._home_offset)
    
    def clearAlarms(self):
        """Clear alarms in the device"""
        self.query('$X')
        return
    
    def halt(self) -> Position:
        """Halt the device"""
        self.query('!')
        # self.clearAlarms()
        # self.resume()
        _,coordinates,_home_offset = self.checkStatus()
        return Position(coordinates-_home_offset)
    
    def home(self, axis:str|None = None, *, timeout:int|None = None) -> bool:
        """
        Home the device
        
        Args:
            axis (str|None): axis to home
            timeout (int|None): timeout for homing
            
        Returns:
            bool: whether the device was homed
        """
        if axis is not None:
            assert axis.upper() in 'XYZ', "Ensure axis is X,Y,Z for GRBL"
        command = '$H' if axis is None else f'$H{axis.upper()}'
        self.clear()
        self.write(command)
        while True:
            time.sleep(LOOP_INTERVAL)
            responses = self.read()
            if self.flags.simulation:
                break
            if not self.is_connected:
                break
            if len(responses) and 'Home' not in responses:
                break
        # self.query(command)
        # success = self._wait_for_status(('Home',), timeout=timeout)
        # if not success:
        #     status,_,_ = self.checkStatus()
        #     self._logger.error(f"Timeout: {status} | {command}")
        return True
    
    def resume(self):
        """Resume activity on the device"""
        self.query('~')
        return
    
    def setSpeedFactor(self, speed_factor:float, *, speed_max:int, **kwargs):
        """
        Set the speed factor in the device
        
        Args:
            speed_factor (float): speed factor
            speed_max (int): maximum speed
        """
        assert isinstance(speed_factor, float), "Ensure speed factor is a float"
        assert (0.0 <= speed_factor <= 1.0), "Ensure speed factor is between 0.0 and 1.0"
        feed_rate = int(speed_factor * speed_max) * 60      # Convert to mm/min
        self.write(f'G90 F{feed_rate}')
        self.read()
        return
    
    def _wait_for_status(self, statuses:Sequence[str], timeout:int = MOVEMENT_TIMEOUT) -> bool:
        """
        Wait for the device to reach a certain status
        
        Args:
            statuses (Sequence[str]): statuses to wait for
            timeout (int): timeout for waiting
            
        Returns:
            bool: whether the device reached the status
        """
        status,_,_ = self.checkStatus()
        start_time = time.perf_counter()
        if self.flags.simulation:
            return True
        while status not in statuses:
            time.sleep(LOOP_INTERVAL)
            status,_,_ = self.checkStatus()
            if status == 'Hold':
                raise RuntimeError("Movement paused")
            if time.perf_counter() - start_time > timeout:
                return False
        return True
    
    # Overwritten methods
    def connect(self):
        """Connect to the device"""
        super().connect()
        self.clear()
        startup_lines = self.read(True)
        self.clearAlarms()
        info = self.checkInfo()
        self._version = info[0].split(':')[1]
        parameters = self.checkParameters()
        self._home_offset = np.array(parameters.get('G54', [0,0,0]))
        
        self._logger.info(startup_lines)
        self._logger.info(f'GRBL version: {self._version}')
        return
    
    def query(self, data: Any, lines:bool = True, *, timeout:int|None = None, jog:bool = False, wait:bool = False) -> list[str]|None:
        """
        Query the device (i.e. write and read data)
        
        Args:
            data (Any): data to query
            lines (bool): whether to read lines
            timeout (int|None): timeout for query
            jog (bool): whether to perform jog movements
            wait (bool): whether to wait for the device to reach the status
            
        Returns:
            list[str]|None: response from the device
        """
        if self.flags.simulation:
            wait = False
        # For quick queries
        if jog:
            assert self.__version__().startswith("1.1"), "Ensure GRBL version is at least 1.1 to perform jog movements"
            data = data.replace('G0 ', '').replace('G1 ', '')
            data = f'$J={data}'
            self.write(data)
            return self.read(lines=False)
        if not wait:
            self.write(data)
            return self.read(lines=lines)
        
        # success = self._wait_for_status(('Idle',), timeout=timeout)
        # if not success:
        #     status,_,_ = self.checkStatus()
        #     self._logger.error(f"Timeout: {data} | {status}")
        #     if status == 'Jog':
        #         raise RuntimeError("Jog mode still active")
        #     return []
        
        responses = super().query(data, lines=lines)
        for response in responses:
            self._logger.debug(f"Response: {response}")
            if response == 'ok':
                continue
            if any([self.checkAlarms(response), self.checkErrors(response)]):
                raise RuntimeError(f"Response: {response}")
        
        # success = self._wait_for_status(('Idle',), timeout=timeout)
        # if not success:
        #     status,_,_ = self.checkStatus()
        #     self._logger.error(f"Timeout: {data} | {status}")
        return responses
