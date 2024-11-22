# -*- coding: utf-8 -*-
# Standard imports
from __future__ import annotations
from copy import deepcopy
import ipaddress
import logging
import socket
import time
from types import SimpleNamespace
from typing import Any

# Local imports
from .dobot_api import dobot_api_dashboard, dobot_api_feedback

logger = logging.getLogger("controllably.Move")
logger.setLevel(logging.DEBUG)
logger.debug(f"Import: OK <{__name__}>")

DASHBOARD_PORT = 29999
FEEDBACK_PORT = 30003

class DobotDevice:
    
    _default_flags: SimpleNamespace = SimpleNamespace(verbose=False, connected=False, simulation=False)
    def __init__(self, 
        host: str, 
        port: int|None = None, 
        timeout: int = 10, 
        *, 
        simulation: bool=False, 
        verbose: bool = False, 
        **kwargs
    ):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.socket = socket.socket()
        self.dashboard: dobot_api_dashboard|None = None
        self.feedback: dobot_api_feedback|None = None
        self.flags = deepcopy(self._default_flags)
        
        self.socket.settimeout(self.timeout)
        self.flags.simulation = simulation
        
        self._logger = logger.getChild(f"{self.__class__.__name__}_{id(self)}")
        self._logger.addHandler(logging.StreamHandler())
        self.verbose = verbose
        return
    
    @property
    def connection_details(self) -> dict:
        """Connection details for the device"""
        ports = tuple([s.port for s in (self.dashboard, self.feedback) if s is not None])
        return {
            'host': self.host,
            'port': ports,
            'timeout': self.timeout
        }
    
    @property
    def is_connected(self) -> bool:
        """Whether the device is connected"""
        connected = self.flags.connected if self.flags.simulation else (self.socket.fileno() != -1)
        return connected
    
    @property
    def verbose(self) -> bool:
        """Verbosity of class"""
        return self.flags.verbose
    @verbose.setter
    def verbose(self, value:bool):
        assert isinstance(value,bool), "Ensure assigned verbosity is boolean"
        self.flags.verbose = value
        level = logging.DEBUG if value else logging.INFO
        for handler in self._logger.handlers:
            if not isinstance(handler, logging.StreamHandler):
                continue
            handler.setLevel(level)
        return
    
    def clear(self):
        """Clear the input and output buffers"""
        if self.flags.simulation:
            return
        self.socket.settimeout(0)
        self.socket.recv(1024)
        self.socket.settimeout(self.timeout)
        return

    def connect(self):
        """Connect to the device"""
        if self.is_connected:
            return
        # Check if machine is connected to the same network as device
        hostname = socket.getfqdn()
        local_ip = socket.gethostbyname_ex(hostname)[2][0]
        local_network = f"{'.'.join(local_ip.split('.')[:-1])}.0/24"
        if ipaddress.ip_address(self.host) not in ipaddress.ip_network(local_network):
            print(f"Current IP Network: {local_network[:-3]}")
            print(f"Device  IP Address: {self.host}")
            raise ConnectionError("Ensure device is connected to the same network as the machine")
        
        start_time = time.perf_counter()
        dashboard = dobot_api_dashboard(self.host, DASHBOARD_PORT)
        if time.perf_counter() - start_time > self.timeout:
            raise ConnectionAbortedError(f"Failed to connect to {self.host} at {DASHBOARD_PORT}")
        self.dashboard = dashboard
        
        start_time = time.perf_counter()
        feedback = dobot_api_feedback(self.host, FEEDBACK_PORT)
        if time.perf_counter() - start_time > self.timeout:
            raise ConnectionAbortedError(f"Failed to connect to {self.host} at {FEEDBACK_PORT}")
        self.feedback = feedback
        self._logger.info(f"Connected to {self.host} at {DASHBOARD_PORT} and {FEEDBACK_PORT}")
        
        if isinstance(self.dashboard, dobot_api_dashboard):
            self.dashboard.DisableRobot()
            self.dashboard.ClearError()
            self.dashboard.EnableRobot()
            self.dashboard.User(0)
            self.dashboard.Tool(0)
            self.dashboard.SpeedFactor(100)
        self.flags.connected = True
        return

    def disconnect(self):
        """Disconnect from the device"""
        if not self.is_connected:
            return
        try:
            if isinstance(self.dashboard, dobot_api_dashboard):
                self.dashboard.close()
                self.dashboard = None
            if isinstance(self.feedback, dobot_api_feedback):
                self.feedback.close()
                self.feedback = None
        except socket.error as e:
            self._logger.error(f"Failed to disconnect from {self.host}")
            self._logger.debug(e)
        else:
            self._logger.info(f"Disconnected from {self.host}")
        self.flags.connected = False
        return
    
    def query(self, data:Any, lines:bool = True) -> list[str]|None:     # NOTE: not implemented
        """
        Query the device

        Args:
            data (Any): data to query

        Returns:
            list[str]|None: data read from the device, if any
        """
        raise NotImplementedError
        ret = self.write(str(data))
        if ret:
            response = self.read(lines=lines)
            return response if isinstance(response, list) else [response]
        return

    def read(self, lines:bool = False) -> str|list[str]:                # NOTE: not implemented
        """
        Read data from the device
        
        Args:
            lines (bool, optional): whether to read multiple lines. Defaults to False.
            
        Returns:
            str|list[str]: line(s) of data read from the device
        """
        raise NotImplementedError
        data = []
        try:
            data = self.socket.recv(1024).decode("utf-8", "replace").strip().split('\n')
            self._logger.debug(f"Received: {data!r}")
        except socket.error as e:
            self._logger.debug(f"Failed to receive data")
        return data

    def write(self, data:str) -> bool:                                  # NOTE: not implemented
        """
        Write data to the device

        Args:
            data (str): data to write
        
        Returns:
            bool: whether the write was successful
        """
        raise NotImplementedError
        data = f"{data}\n" if not data.endswith('\n') else data
        try:
            self.socket.sendall(data.encode())
            self._logger.debug(f"Sent: {data!r}")
        except socket.error as e:
            self._logger.debug(f"Failed to send: {data!r}")
        return False
