# -*- coding: utf-8 -*-
# Standard library imports
from __future__ import annotations
import gc
import logging
import socket
import time
from types import SimpleNamespace
from typing import Protocol, Any
import uuid

# Third party imports
import serial                       # pip install pyserial
import serial.tools.list_ports

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.debug(f"Import: OK <{__name__}>")

def get_addresses(registry:dict|None) -> dict|None:
    """
    Get the appropriate addresses for current machine

    Args:
        registry (dict|None): dictionary with com port addresses and camera ids

    Returns:
        dict|None: dictionary of com port addresses and camera ids for current machine
    """
    node_id = get_node()
    addresses = registry.get('machine_id',{}).get(node_id,{})
    if len(addresses) == 0:
        logger.warning("Append machine id and camera ids/port addresses to registry file")
        logger.warning(f"Machine not yet registered. (Current machine id: {node_id})")
        return None
    return addresses

def get_node() -> str:
    """
    Display the machine's unique identifier

    Returns:
        str: machine unique identifier
    """
    node_id = str(uuid.getnode())
    node_out = f"Current machine id: {node_id}"
    logger.info(node_out)
    print(node_out)
    return node_id

def get_ports() -> list[str]:
    """
    Get available ports

    Returns:
        list[str]: list of connected serial ports
    """
    ports = []
    for port, desc, hwid in sorted(serial.tools.list_ports.comports()):
        ports.append(str(port))
        port_desc = f"{port}: [{hwid}] {desc}"
        logger.info(port_desc)
        print(port_desc)
    if len(ports) == 0:
        logger.warning("No ports detected!")
    return ports

class Device(Protocol):
    """
    Protocol for device classes
    """
    connection_details: dict
    is_connected: bool
    verbose: bool
    def clear(self):
        """Clear the input and output buffers"""
        raise NotImplementedError

    def connect(self):
        """Connect to the device"""
        raise NotImplementedError

    def disconnect(self):
        """Disconnect from the device"""
        raise NotImplementedError

    def query(self, data:str) -> Any:
        """Query the device"""
        raise NotImplementedError

    def read(self, **kwargs) -> str|list[str]:
        """Read data from the device"""
        raise NotImplementedError

    def write(self, data:str) -> bool:
        """Write data to the device"""
        raise NotImplementedError


class SerialDevice:
    """
    Class for handling serial devices
    """
    
    def __init__(self,
        port: str|None = None, 
        baudrate: int = 9600, 
        timeout: int = 1, 
        init_timeout: int = 2,
        message_end: str = '\n',
        *,
        simulation: bool = False,
        **kwargs
    ):
        """
        Constructor for SerialDevice

        Args:
            port (str): port for the device
            baudrate (int): baudrate for the device
            timeout (int, optional): timeout for the device. Defaults to 1.
            init_timeout (int, optional): timeout for initialization. Defaults to 2.
        """
        self._port = ''
        self._baudrate = 0
        self._timeout = 0
        self.init_timeout = init_timeout
        self.message_end = message_end
        self.flags = SimpleNamespace(verbose=False, connected=False, simulation=simulation)
        
        self.serial = serial.Serial()
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        return
    
    def __repr__(self):
        return f"{super().__repr__()} ref={len(gc.get_referrers(self))}"
    
    def __del__(self):
        self.disconnect()
        return
    
    @property
    def port(self) -> str:
        """Get port for the device"""
        return self._port
    @port.setter
    def port(self, value:str):
        """Set port for the device"""
        self._port = value
        self.serial.port = value
        return
    
    @property
    def baudrate(self) -> int:
        """Get baudrate for the device"""
        return self._baudrate
    @baudrate.setter
    def baudrate(self, value:int):
        """Set baudrate for the device"""
        self._baudrate = value
        self.serial.baudrate = value
        return
    
    @property
    def timeout(self) -> int:
        """Get timeout for the device"""
        return self._timeout
    @timeout.setter
    def timeout(self, value:int):
        """Set timeout for the device"""
        self._timeout = value
        self.serial.timeout = value
        return
    
    @property
    def connection_details(self) -> dict:
        """
        Get connection details

        Returns:
            dict: connection details
        """
        return {
            'port': self.port,
            'baudrate': self.baudrate,
            'timeout': self.timeout
        }
    
    @property
    def is_connected(self) -> bool:
        """
        Check if the device is connected

        Returns:
            bool: whether the device is connected
        """
        connected = self.flags.connected if self.flags.simulation else self.serial.is_open
        return connected
    
    @property
    def verbose(self) -> bool:
        """Get verbosity of class"""
        return self.flags.verbose
    @verbose.setter
    def verbose(self, value:bool):
        """Set verbosity of class"""
        assert isinstance(value,bool), "Ensure assigned verbosity is boolean"
        self.flags.verbose = value
        level = logging.INFO if value else logging.WARNING
        logger.setLevel(level)
        for handler in logger.handlers:
            if isinstance(handler, type(logging.StreamHandler())):
                handler.setLevel(level)
        return
    
    def clear(self):
        """
        Clear the input and output buffers
        """
        self.serial.reset_input_buffer()
        self.serial.reset_output_buffer()
        return

    def connect(self):
        """
        Connect to the device
        """
        try:
            if self.is_connected:
                return
            self.serial.open()
        except serial.SerialException as e:
            logger.error(f"Failed to connect to {self.port} at {self.baudrate} baud")
            logger.debug(e)
        else:
            logger.info(f"Connected to {self.port} at {self.baudrate} baud")
            time.sleep(self.init_timeout)
        self.flags.connected = True
        return

    def disconnect(self):
        """
        Disconnect from the device
        """
        try:
            if not self.is_connected:
                return
            self.serial.close()
        except serial.SerialException as e:
            logger.error(f"Failed to disconnect from {self.port}")
            logger.debug(e)
        else:
            logger.info(f"Disconnected from {self.port}")
        self.flags.connected = False
        return
    
    def query(self, data:Any) -> Any:
        """
        Query the device

        Args:
            data (str): data to query

        Returns:
            list[str]: data read from the device
        """
        ret = self.write(str(data))
        if ret:
            return self.read(lines=True)
        return
    
    def read(self, lines:bool = False) -> str|list[str]:
        """
        Read data from the device

        Returns:
            list[str]: data read from the device
        """
        data = ''
        try:
            if lines:
                data = self.serial.readlines()
                data = [d.decode("utf-8", "replace").strip() for d in data]
            else:
                data = self.serial.readline().decode("utf-8", "replace").strip()
            logger.info(f"Received: {data}")
            self.serial.reset_output_buffer()
        except serial.SerialException as e:
            logger.info(f"Failed to receive data")
        return data

    def write(self, data:str) -> bool:
        """
        Write data to the device

        Args:
            data (str): data to write
        
        Returns:
            bool: whether the write was successful
        """
        assert isinstance(data, str), "Ensure data is a string"
        data = f"{data}{self.message_end}" if not data.endswith(self.message_end) else data
        try:
            self.serial.write(data.encode())
            logger.info(f"Sent: {data}")
        except serial.SerialException as e:
            logger.info(f"Failed to send: {data}")
            return False
        return True


class SocketDevice:
    """
    Class for handling socket devices
    """
    def __init__(self, host:str, port:int, timeout:int=1, *, simulation:bool=False, **kwargs):
        """
        Constructor for SocketDevice

        Args:
            host (str): host for the device
            port (int): port for the device
            timeout (int, optional): timeout for the device. Defaults to 1.
        """
        self.host = host
        self.port = port
        self.timeout = timeout
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.flags = SimpleNamespace(verbose=False, connected=False, simulation=simulation)
        
        self.socket.settimeout(self.timeout)
        return

    @property
    def connection_details(self) -> dict:
        """
        Get connection details

        Returns:
            dict: connection details
        """
        return {
            'host': self.host,
            'port': self.port,
            'timeout': self.timeout
        }
    
    @property
    def is_connected(self) -> bool:
        """
        Check if the device is connected

        Returns:
            bool: whether the device is connected
        """
        connected = self.flags.connected if self.flags.simulation else (self.socket.fileno() != -1)
        return connected
    
    @property
    def verbose(self) -> bool:
        """Get verbosity of class"""
        return self.flags.verbose
    @verbose.setter
    def verbose(self, value:bool):
        """Set verbosity of class"""
        assert isinstance(value,bool), "Ensure assigned verbosity is boolean"
        self.flags.verbose = value
        level = logging.INFO if value else logging.WARNING
        logger.setLevel(level)
        for handler in logger.handlers:
            if isinstance(handler, type(logging.StreamHandler())):
                handler.setLevel(level)
        return
    
    def clear(self):
        """
        Clear the input and output buffers
        """
        self.socket.settimeout(0)
        self.socket.recv(1024)
        self.socket.settimeout(self.timeout)
        return

    def connect(self):
        """
        Connect to the device
        """
        try:
            if self.is_connected:
                return
            self.socket.connect((self.host, self.port))
        except socket.error as e:
            logger.error(f"Failed to connect to {self.host} at {self.port}")
            logger.debug(e)
        else:
            logger.info(f"Connected to {self.host} at {self.port}")
        self.flags.connected = True
        return

    def disconnect(self):
        """
        Disconnect from the device
        """
        try:
            if not self.is_connected:
                return
            self.socket.close()
        except socket.error as e:
            logger.error(f"Failed to disconnect from {self.host}")
            logger.debug(e)
        else:
            logger.info(f"Disconnected from {self.host}")
        self.flags.connected = False
        return
    
    def query(self, data:str) -> Any:
        """
        Query the device

        Args:
            data (str): data to query

        Returns:
            list[str]: data read from the device
        """
        self.write(data)
        return self.read()
    
    def read(self) -> str|list[str]:
        """
        Read data from the device

        Returns:
            list[str]: data read from the device
        """
        data = []
        try:
            data = self.socket.recv(1024).decode("utf-8", "replace").strip().split('\n')
            logger.info(f"Received: {data}")
        except socket.error as e:
            logger.info(f"Failed to receive data")
        return data

    def write(self, data:str) -> bool:
        """
        Write data to the device

        Args:
            data (str): data to write
        
        Returns:
            bool: whether the write was successful
        """
        data = f"{data}\n" if not data.endswith('\n') else data
        try:
            self.socket.sendall(data.encode())
            logger.info(f"Sent: {data}")
        except socket.error as e:
            logger.info(f"Failed to send: {data}")
        return False


class DeviceFactory:
    """
    Factory class for creating devices
    """
    @staticmethod
    def createDevice(device_type:str, *args, **kwargs) -> Device:
        """
        Create a device

        Args:
            device_type (str): type of device to create

        Returns:
            Device: created device
        """
        return device_type(*args, **kwargs)
    
    @staticmethod
    def createDeviceFromDict(device_dict:dict) -> Device:
        """
        Create a device from a dictionary

        Args:
            device_dict (dict): dictionary containing device details

        Returns:
            Device: created device
        """
        device_type = device_dict.pop('device_type', None)
        if device_type is not None:
            assert callable(device_type), "Ensure device_type is a callable class"
            return DeviceFactory.createDevice(device_type, **device_dict)
        if 'baudrate' in device_dict:
            device_type = SerialDevice
        elif 'host' in device_dict:
            device_type = SocketDevice
        return DeviceFactory.createDevice(device_type, **device_dict)
