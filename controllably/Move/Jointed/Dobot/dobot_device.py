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
from .dobot_api import DobotApiDashboard, DobotApiMove

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
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.dashboard_api: DobotApiDashboard|None = None
        self.move_api: DobotApiMove|None = None
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
        ports = tuple([s.port for s in (self.dashboard_api, self.move_api) if s is not None])
        return {
            'host': self.host,
            'port': ports,
            'timeout': self.timeout
        }
    
    @property
    def is_connected(self) -> bool:
        """Whether the device is connected"""
        connected = self.flags.connected
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
        dashboard_api = DobotApiDashboard(self.host, DASHBOARD_PORT)
        if time.perf_counter() - start_time > self.timeout:
            raise ConnectionAbortedError(f"Failed to connect to {self.host} at {DASHBOARD_PORT}")
        self.dashboard_api = dashboard_api
        
        start_time = time.perf_counter()
        move_api = DobotApiMove(self.host, FEEDBACK_PORT)
        if time.perf_counter() - start_time > self.timeout:
            raise ConnectionAbortedError(f"Failed to connect to {self.host} at {FEEDBACK_PORT}")
        self.move_api = move_api
        self._logger.info(f"Connected to {self.host} at {DASHBOARD_PORT} and {FEEDBACK_PORT}")
        
        self.reset()
        if isinstance(self.dashboard_api, DobotApiDashboard):
            self.dashboard_api.User(0)
            self.dashboard_api.Tool(0)
        self.flags.connected = True
        return

    def disconnect(self):
        """Disconnect from the device"""
        if not self.is_connected:
            return
        try:
            self.close()
        except socket.error as e:
            self._logger.error(f"Failed to disconnect from {self.host}")
            self._logger.debug(e)
        else:
            self._logger.info(f"Disconnected from {self.host}")
        self.flags.connected = False
        return
    
    def reset(self):
        self.DisableRobot()
        self.ClearError()
        self.EnableRobot()
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

    # Dobot API
    def close(self):
        self._logger.debug("close")
        if isinstance(self.dashboard_api, DobotApiDashboard):
            self.dashboard_api.close()
            self.dashboard_api = None
        if isinstance(self.move_api, DobotApiMove):
            self.move_api.close()
            self.move_api = None
        return

    # Dashboard API
    def ClearError(self):
        self._logger.debug("ClearError")
        return self.dashboard_api.ClearError() if isinstance(self.dashboard_api, DobotApiDashboard) else None
    
    def DisableRobot(self):
        self._logger.debug("DisableRobot")
        return self.dashboard_api.DisableRobot() if isinstance(self.dashboard_api, DobotApiDashboard) else None
    
    def EnableRobot(self, *args):
        self._logger.debug("EnableRobot")
        return self.dashboard_api.EnableRobot(*args) if isinstance(self.dashboard_api, DobotApiDashboard) else None
    
    def ResetRobot(self):
        self._logger.debug("ResetRobot")
        return self.dashboard_api.ResetRobot() if isinstance(self.dashboard_api, DobotApiDashboard) else None
    
    def SetArmOrientation(self, right_handed:bool):
        self._logger.debug(f"SetArmOrientation | {right_handed=}")
        return self.dashboard_api.SetArmOrientation(int(right_handed)) if isinstance(self.dashboard_api, DobotApiDashboard) else None
    
    def SpeedFactor(self, speed_factor:int):
        self._logger.debug(f"SpeedFactor | {speed_factor=}")
        return self.dashboard_api.SpeedFactor(speed_factor) if isinstance(self.dashboard_api, DobotApiDashboard) else None
    
    # Move API
    def JointMovJ(self, j1:float, j2:float, j3:float, j4:float, *args):
        self._logger.debug(f"JointMovJ | {j1=}, {j2=}, {j3=}, {j4=}")
        return self.move_api.JointMovJ(j1,j2,j3,j4, *args) if isinstance(self.move_api, DobotApiMove) else None    
    
    def MovJ(self, x:float, y:float, z:float, r:float, *args):
        self._logger.debug(f"MovJ | {x=}, {y=}, {z=}, {r=}")
        return self.move_api.MovJ(x,y,z,r, *args) if isinstance(self.move_api, DobotApiMove) else None
    
    def RelMovJ(self, offset1:float, offset2:float, offset3:float, offset4:float, *args):
        self._logger.debug(f"RelMovJ | {offset1=}, {offset2=}, {offset3=}, {offset4=}")
        return self.move_api.RelMovJ(offset1,offset2,offset3,offset4, *args) if isinstance(self.move_api, DobotApiMove) else None
    
    def RelMovL(self, offsetX:float, offsetY:float, offsetZ:float, offsetR:float, *args):
        """
        Move the robot by the specified cartesian offsets
        
        Args:
            offsetX (float): x offset
            offsetY (float): y offset
            offsetZ (float): z offset
            offsetR (float): r offset
        """
        self._logger.debug(f"RelMovL | {offsetX=}, {offsetY=}, {offsetZ=}, {offsetR=}")
        return self.move_api.RelMovL(offsetX,offsetY,offsetZ,offsetR, *args) if isinstance(self.move_api, DobotApiMove) else None
    