# -*- coding: utf-8 -*-
"""
GRBL API for controlling CNC machines using the GRBL firmware.
Refer to https://github.com/gnea/grbl/tree/master/doc/markdown for more information on the GRBL firmware.

Attributes:
    LOOP_INTERVAL (float): loop interval for device
    MOVEMENT_TIMEOUT (int): timeout for movement
    READ_FORMAT (str): read format for device
    WRITE_FORMAT (str): write format for device
    Data (NamedTuple): data for device
    
## Classes:
    `GRBL`: GRBL class for controlling CNC machines using the GRBL firmware.
    
<i>Documentation last updated: 2025-02-22</i>
"""
# Standard library imports
from __future__ import annotations
import time
from typing import Any, Sequence, NamedTuple

# Third-party imports
import numpy as np

# Local application imports
from ...core.device import SerialDevice, AnyDevice
from ...core.position import Position
from .grbl_lib import Alarm, Error, Setting, Status

LOOP_INTERVAL = 0.1
MOVEMENT_TIMEOUT = 30

READ_FORMAT = "{data}\n"
WRITE_FORMAT = "{data}\n"
Data = NamedTuple("Data", [("data", str), ("channel", int)])

class GRBL(SerialDevice):
    """
    GRBL class for controlling CNC machines using the GRBL firmware.
    Refer to https://github.com/gnea/grbl/tree/master/doc/markdown for more information on the GRBL firmware.
    
    ### Constructor:
        `port` (str|None): Serial port to connect to. Defaults to None.
        `baudrate` (int): Baudrate of the serial connection. Defaults to 115200.
        `timeout` (int): Timeout for serial connection. Defaults to 1.
        `init_timeout` (int): Timeout for initialization of serial connection. Defaults to 2.
        `message_end` (str): Message end character for serial communication. Defaults to '\n'.
        `simulation` (bool): Simulation mode for testing. Defaults to False.
        
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
        `getAlarms`: check for alarms in the response
        `getErrors`: check for errors in the response
        `getInfo`: query device information
        `getParameters`: query device parameters
        `getSettings`: query device settings
        `getState`: query device state
        `getStatus`: query device status
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
        baudrate: int = 115200, 
        timeout: int = 1, 
        init_timeout: int = 2,
        message_end: str = '\n',
        *args,
        simulation: bool = False,
        **kwargs
    ):
        """
        Initialize GRBL class
        
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
    
    def getAlarms(self, response: str) -> bool:
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
    
    def getErrors(self, response: str) -> bool:
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
    
    def getInfo(self) -> list[str]:
        """
        Query device information
        
        Returns:
            list[str]: information in the response
        """
        self.clearDeviceBuffer()
        responses = self.query('$I')
        if self.flags.simulation:
            return ['GRBL:1.1']
        return responses
    
    def getParameters(self) -> dict[str, list[float]]:
        """
        Query device parameters
        
        Returns:
            dict[str, list[float]]: parameters in the response
        """
        self.clearDeviceBuffer()
        responses = self.query('$#')
        parameters = {}
        if self.flags.simulation:
            return parameters
        for response in responses:
            if 'WIFI' in response:
                continue
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
    
    def getSettings(self) -> dict[str, int|float|str]:
        """
        Query device settings
        
        Returns:
            dict[str, int|float|str]: settings in the response
        """
        self.clearDeviceBuffer()
        responses = self.query('$$')
        while len(responses)==0 or 'ok' not in responses[-1]:
            if self.flags.simulation:
                break
            time.sleep(1)
            chunk = self.readAll()
            responses.extend(chunk)
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
    
    def getState(self) -> dict[str, str]:
        """
        Query device state
        
        Returns:
            dict[str, str]: state in the response
        """
        self.clearDeviceBuffer()
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
    
    def getStatus(self) -> tuple[str, np.ndarray[float], np.ndarray[float]]:
        """
        Query device status
        
        Returns:
            tuple[str, np.ndarray[float], np.ndarray[float]]: status, current position, home offset
        """
        self.clearDeviceBuffer()
        responses = self.query('?',multi_out=False)
        self.clearDeviceBuffer()
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
        _,coordinates,_home_offset = self.getStatus()
        return Position(coordinates-_home_offset)
    
    def home(self, axis:str|None = None, *, timeout:int|None = None) -> bool:
        """
        Home the device
        
        Args:
            axis (str|None): axis to home. Defaults to None.
            timeout (int|None): timeout for homing
            
        Returns:
            bool: whether the device was homed
        """
        if axis is not None:
            assert axis.upper() in 'XYZ', "Ensure axis is X,Y,Z for GRBL"
        command = '$H' if axis is None else f'$H{axis.upper()}'
        self.clearDeviceBuffer()
        self.query(command)
        while True:
            if self.flags.simulation:
                break
            if not self.is_connected:
                break
            time.sleep(LOOP_INTERVAL)
            responses = self.read()
            if len(responses) and 'Home' not in responses:
                break
        # self.query(command)
        # success = self._wait_for_status(('Home',), timeout=timeout)
        # if not success:
        #     status,_,_ = self.getStatus()
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
        
        data = f'G90 F{feed_rate}'
        self.query(data)
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
        status,_,_ = self.getStatus()
        start_time = time.perf_counter()
        if self.flags.simulation:
            return True
        while status not in statuses:
            if self.flags.simulation:
                break
            time.sleep(LOOP_INTERVAL)
            status,_,_ = self.getStatus()
            if status == 'Hold':
                raise RuntimeError("Movement paused")
            if time.perf_counter() - start_time > timeout:
                return False
        return True
    
    # Overwritten methods
    def connect(self):
        """Connect to the device"""
        super().connect()
        self.clearDeviceBuffer()
        startup_lines = self.readAll()
        self.clearAlarms()
        info = self.getInfo()
        try:
            self._version = info[0].split(':')[1]
        except IndexError:
            self._version = '1.1'
            self._logger.error(f"GRBL version not found. Defaulting to {self._version}")
        parameters = self.getParameters()
        self._home_offset = np.array(parameters.get('G54', [0,0,0]))
        
        self._logger.info(startup_lines)
        self._logger.info(f'GRBL version: {self._version}')
        return
    
    def query(self, 
        data: Any, 
        multi_out:bool = True, 
        *, 
        timeout:int|float = 1, 
        jog:bool = False, 
        wait:bool = False,
        **kwargs
    ) -> list[str]|None:
        """
        Query the device (i.e. write and read data)
        
        Args:
            data (Any): data to query
            multi_out (bool): whether to read lines
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
            jog_out: Data = super().query(data, multi_out=False, timeout=timeout, **kwargs)
            return jog_out.data
        out: Data|list[Data] = super().query(data, multi_out=multi_out, timeout=timeout, **kwargs)
        if isinstance(out,list):
            data_out = [(response.data if response is not None else None) for response in out]
        else:
            data_out = [(out.data if out is not None else None)]
        if wait:
            for response in data_out:
                self._logger.debug(f"Response: {response}")
                if response == 'ok':
                    continue
                if any([self.getAlarms(response), self.getErrors(response)]):
                    raise RuntimeError(f"Response: {response}")
        return data_out
