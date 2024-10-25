# -*- coding: utf-8 -*-
# Standard library imports
from __future__ import annotations
from logging import getLogger
import socket
import uuid

# Third party imports
import serial                       # pip install pyserial
import serial.tools.list_ports

# Local application imports
from . import factory

logger = getLogger(__name__)
logger.info(f"Import: OK <{__name__}>")

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

def get_plans(configs:dict, registry:dict|None = None) -> dict:
    """
    Get available configurations
    
    Args:
        configs (dict): dictionary of configurations
        registry (dict|None, optional): dictionary of addresses. Defaults to None.
    
    Returns:
        dict: dictionary of available configurations
    """
    addresses = get_addresses(registry)
    configs = factory.get_details(configs, addresses)
    return configs

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

class SerialDevice:
    """
    Class for handling serial devices
    """
    def __init__(self, port:str, baudrate:int, timeout:int=1):
        """
        Constructor for SerialDevice

        Args:
            port (str): port for the device
            baudrate (int): baudrate for the device
            timeout (int, optional): timeout for the device. Defaults to 1.
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.device: serial.Serial|None = None
        return

    def connect(self):
        """
        Connect to the device
        """
        try:
            self.device = serial.Serial(port=self.port, baudrate=self.baudrate, timeout=self.timeout)
            logger.info(f"Connected to {self.port} at {self.baudrate} baud")
        except serial.SerialException as e:
            logger.error(f"Failed to connect to {self.port} at {self.baudrate} baud")
            logger.error(e)
        return

    def disconnect(self):
        """
        Disconnect from the device
        """
        try:
            self.device.close()
            logger.info(f"Disconnected from {self.port}")
        except serial.SerialException as e:
            logger.error(f"Failed to disconnect from {self.port}")
            logger.error(e)
        return
    
    def query(self, data:str) -> list[str]:
        """
        Query the device

        Args:
            data (str): data to query

        Returns:
            list[str]: data read from the device
        """
        self.write(data)
        return self.read()
    
    def read(self) -> list[str]:
        """
        Read data from the device

        Returns:
            list[str]: data read from the device
        """
        data = []
        try:
            data = self.device.readlines()
            data = [d.decode().strip() for d in data]
            logger.info(f"Received: {data}")
            self.device.reset_output_buffer()
        except serial.SerialException as e:
            logger.error(f"Failed to receive data")
            logger.error(e)
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
            self.device.write(data.encode())
            logger.info(f"Sent: {data}")
        except serial.SerialException as e:
            logger.error(f"Failed to send: {data}")
            logger.error(e)
            return False
        return True


class SocketDevice:
    """
    Class for handling socket devices
    """
    def __init__(self, host:str, port:int, timeout:int=1):
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
        self.device: socket.socket|None = None
        return

    def connect(self):
        """
        Connect to the device
        """
        try:
            self.device = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.device.settimeout(self.timeout)
            self.device.connect((self.host, self.port))
            logger.info(f"Connected to {self.host} at {self.port}")
        except socket.error as e:
            logger.error(f"Failed to connect to {self.host} at {self.port}")
            logger.error(e)
        return

    def disconnect(self):
        """
        Disconnect from the device
        """
        try:
            self.device.close()
            logger.info(f"Disconnected from {self.host}")
        except socket.error as e:
            logger.error(f"Failed to disconnect from {self.host}")
            logger.error(e)
        return
    
    def query(self, data:str) -> list[str]:
        """
        Query the device

        Args:
            data (str): data to query

        Returns:
            list[str]: data read from the device
        """
        self.write(data)
        return self.read()
    
    def read(self) -> list[str]:
        """
        Read data from the device

        Returns:
            list[str]: data read from the device
        """
        data = []
        try:
            data = self.device.recv(1024).decode().strip().split('\n')
            logger.info(f"Received: {data}")
        except socket.error as e:
            logger.error(f"Failed to receive data")
            logger.error(e)
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
            self.device.sendall(data.encode())
            logger.info(f"Sent: {data}")
        except socket.error as e:
            logger.error(f"Failed to send: {data}")
            logger.error(e)
        return False


class DeviceFactory:
    """
    Factory class for creating devices
    """
    @staticmethod
    def createDevice(device_type:str, *args, **kwargs) -> SerialDevice|SocketDevice|None:
        """
        Create a device

        Args:
            device_type (str): type of device to create

        Returns:
            SerialDevice|SocketDevice|None: created device
        """
        match device_type:
            case 'serial':
                return SerialDevice(*args, **kwargs)
            case 'socket':
                return SocketDevice(*args, **kwargs)
            case _:
                logger.warning(f"Unknown device type: {device_type}")
        return None
    
    @staticmethod
    def createDeviceFromDict(device_dict:dict) -> SerialDevice|SocketDevice|None:
        """
        Create a device from a dictionary

        Args:
            device_dict (dict): dictionary containing device details

        Returns:
            SerialDevice|SocketDevice|None: created device
        """
        return DeviceFactory.createDevice(device_dict['type'], **device_dict['details'])


__where__ = "misc.Connections"
from .factory import include_this_module
include_this_module(get_local_only=True)