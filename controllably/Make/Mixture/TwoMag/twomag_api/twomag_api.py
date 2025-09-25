# -*- coding: utf-8 -*-
"""
This module holds the API for the 2Mag device.

Attributes:
    READ_FORMAT (str): The read format for the device
    WRITE_FORMAT (str): The write format for the device
    Data (NamedTuple): The data type for the device

## Classes:
    `TwoMagDevice`: Class for the 2Mag device
    
<i>Documentation last updated: 2025-02-22</i>
"""
# Standard library imports
from __future__ import annotations
import string
from typing import NamedTuple, Any

# Local application imports
from .....core.device import SerialDevice, AnyDevice
from .twomag_lib import ErrorCode

READ_FORMAT = "{status}_{data}_{address:.1}\r"
WRITE_FORMAT = "{data}_{address}\r"
Data = NamedTuple("Data", [("data", str), ("status", str), ("address", str)])

class TwoMagDevice(SerialDevice):
    """
    Class for the 2Mag device
    
    ### Constructor:
        `port` (str): The port to which the device is connected
        `baudrate` (int, optional): The baudrate of the device. Defaults to 9600.
        `timeout` (int, optional): The timeout for the device. Defaults to 1.
        `init_timeout` (int, optional): The timeout for initialization. Defaults to 5.
        `data_type` (NamedTuple, optional): The data type for the device. Defaults to Data.
        `read_format` (str, optional): The read format for the device. Defaults to READ_FORMAT.
        `write_format` (str, optional): The write format for the device. Defaults to WRITE_FORMAT.
        `simulation` (bool, optional): Whether to simulate the device. Defaults to False.
        `verbose` (bool, optional): Whether to print out debug information. Defaults to False.
        
    ### Attributes and properties:
        `address` (str): The address of the device
        `version` (str): The version of the device
        `mode` (str): The mode of the device
        `speed` (int): The speed of the device in RPM
        `power` (int): The power of the device in percentage
        `connection_details` (dict): connection details for the device
        `device` (Device): device object that communicates with physical tool
        `flags` (SimpleNamespace[str, bool]): flags for the class
        `is_busy` (bool): whether the device is busy
        `is_connected` (bool): whether the device is connected
        `verbose` (bool): verbosity of class
        
    ### Methods:
        `connect`: connect to the device
        `disconnect`: disconnect from the device
        `execute`: execute task
        `resetFlags`: reset all flags to class attribute `_default_flags`
        `run`: alias for `execute()`
        `shutdown`: shutdown procedure for tool
        `getPower`: get the power of the device
        `getSpeed`: get the speed of the device
        `getStatus`: get the status of the device
        `setDefault`: set the device to default
        `setPower`: set the power of the device
        `setSpeed`: set the speed of the device
        `start`: start the device
        `stop`: stop the device
    """
    
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
        """ 
        Initialize the 2Mag device
        
        Args:
            port (str, optional): The port to which the device is connected. Defaults to None.
            baudrate (int, optional): The baudrate of the device. Defaults to 9600.
            timeout (int, optional): The timeout for the device. Defaults to 1.
            init_timeout (int, optional): The timeout for initialization. Defaults to 5.
            data_type (NamedTuple, optional): The data type for the device. Defaults to Data.
            read_format (str, optional): The read format for the device. Defaults to READ_FORMAT.
            write_format (str, optional): The write format for the device. Defaults to WRITE_FORMAT.
            simulation (bool, optional): Whether to simulate the device. Defaults to False.
            verbose (bool, optional): Whether to print out debug information. Defaults to False.
        """
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
        """
        Get the status of the device
        
        Returns:
            tuple[str,str]: The version and mode of the device
        """
        out: Data = self.query('sendstatus', address=self.address)
        status = out.data
        version_mode = status.split('_')
        if len(version_mode) == 2:
            self.version = version_mode[0]
            self.mode = version_mode[1]
        return self.version, self.mode
    
    def start(self) -> bool:
        """
        Start the device
        
        Returns:
            bool: Whether the device was started 
        """
        out: Data = self.query('start', address=self.address)
        data = out.data
        return data == 'START'
    
    def stop(self) -> bool:
        """
        Stop the device
        
        Returns:
            bool: Whether the device was stopped
        """
        out: Data = self.query('stop', address=self.address)
        data = out.data
        return data == 'STOP'
        
    def setSpeed(self, speed: int) -> int:
        """
        Set the speed of the device
        
        Args:
            speed (int): The speed to set the device to in RPM
            
        Returns:
            int: The speed of the device in RPM
        """
        assert 100<=speed<=2000, f"Speed out of range (100-2000) : {speed}"
        speed = int(round(speed, -1))       # round to nearest 10
        out: Data = self.query(f'setrpm_{int(speed)}', address=self.address)
        data = out.data
        set_speed = int(data.replace('RPM','').replace('\x00', '').lstrip("0"))
        self.speed = set_speed
        return set_speed
        
    def getSpeed(self) -> int:
        """
        Get the speed of the device
        
        Returns:
            int: The speed of the device in RPM
        """
        out: Data = self.query('sendrpm', address=self.address)
        data = out.data
        set_speed = int(data.replace('RPM','').replace('\x00', '').lstrip("0"))
        self.speed = set_speed
        return set_speed
        
    def setPower(self, power: int) -> int:
        """
        Set the power of the device
        
        Args:
            power (int): The power to set the device to in percentage
            
        Returns:
            int: The power of the device in percentage
        """
        assert 25<=power<=100, f"Speed out of range (25-100) : {power}"
        power = round(power/25) * 25       # round to nearest 25
        out: Data = self.query(f'setpower_{int(power)}', address=self.address)
        data = out.data
        set_power = int(data.replace('POWER','').replace('\x00', '').lstrip("0"))
        self.power = set_power
        return set_power
        
    def getPower(self) -> int:
        """
        Get the power of the device
        
        Returns:
            int: The power of the device in percentage
        """
        out: Data = self.query('sendpower', address=self.address)
        data = out.data
        set_power = int(data.replace('POWER','').replace('\x00', '').lstrip("0"))
        self.power = set_power
        return set_power
        
    def setDefault(self) -> bool:
        """
        Set the device to default
        
        Returns:
            bool: Whether the device was set to default
        """
        out: Data = self.query('setdefault', address=self.address)
        data = out.data
        self.speed = self._default_speed
        self.power = self._default_power
        return data == 'SETDEFAULT'
    
    def setAddress(self, address: str) -> bool:
        """
        Set the address of the device
        
        Args:
            address (str): The address to set the device to
            
        Returns:
            bool: Whether the address was set
        """
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
        """
        Query the device
        
        Args:
            data (Any): The data to query
            multi_out (bool, optional): Whether to return multiple outputs. Defaults to False.
            timeout (int|float, optional): The timeout for the query. Defaults to 0.3.
            format_in (str|None, optional): The format of the input. Defaults to None.
            format_out (str|None, optional): The format of the output. Defaults to None.
            data_type (NamedTuple|None, optional): The data type of the output. Defaults to None.
            timestamp (bool, optional): Whether to timestamp the query. Defaults to False.
            
        Returns:
            Any: The output of the query
        """
        out: Data = super().query(
            data, multi_out, timeout=timeout, 
            format_in=format_in, format_out=format_out, 
            data_type=data_type, timestamp=timestamp, **kwargs
        )
        
        if out.status == 'ER':
            error = ErrorCode[out.data]
            self._logger.error(f"Error: {error}")
        return out
        