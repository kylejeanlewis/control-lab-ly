# -*- coding: utf-8 -*-
""" 
This module provides a class to connect and interface with Dobot's arms

Attributes:
    DASHBOARD_PORT (int): port number for the dashboard API
    FEEDBACK_PORT (int): port number for the feedback API
    
## Classes:
    `DobotDevice`: DobotDevice provides methods to connect and interface with Dobot's arms
    
<i>Documentation last updated: 2025-02-22</i>
"""
# Standard imports
from __future__ import annotations
from copy import deepcopy
import logging
import time
from types import SimpleNamespace
from typing import Any

# Local imports
from .....core import connection
from .....external.Dobot_Arm import DobotApiDashboard, DobotApiMove

# Configure logging
from controllably import CustomLevelFilter
logger = logging.getLogger(__name__)

DASHBOARD_PORT = 29999
FEEDBACK_PORT = 30003

class DobotDevice:
    """ 
    DobotDevice provides methods to connect and interface with Dobot's arms
    
    ### Constructor:
        `host` (str): IP address of Dobot
        `port` (int, optional): port number. Defaults to None.
        `timeout` (int, optional): timeout for connection. Defaults to 10.
        `simulation` (bool, optional): whether to simulate the connection. Defaults to False.
        `verbose` (bool, optional): whether to log debug messages. Defaults to False.
    
    ### Attributes and properties:
        `host` (str): device host
        `port` (int): device port
        `timeout` (int): device timeout
        `connection_details` (dict): connection details for the device
        `dashboard_api` (DobotApiDashboard): dashboard API for the device
        `move_api` (DobotApiMove): move API for the device
        `flags` (SimpleNamespace[str, bool]): flags for the device
        `is_connected` (bool): whether the device is connected
        `verbose` (bool): verbosity of class
        
    ### Methods:
        `connect`: connect to the device
        `disconnect`: disconnect from the device
        `reset`: reset the device
        `clear`: clear the input and output buffers
        `query`: query the device
        `read`: read data from the device
        `write`: write data to the device
        `close`: close the connection to the device
        `ClearError`: clear any errors on the device
        `DisableRobot`: disable the robot
        `EnableRobot`: enable the robot
        `ResetRobot`: stop the robot
        `SetArmOrientation`: set the handedness of the robot
        `SpeedFactor`: set the speed factor of the robot
        `GetAngle`: get the angle of the robot
        `GetPose`: get the pose of the robot
        `DOExecute`: execute a digital output
        `JointMovJ`: move the robot to the specified joint coordinates
        `MovJ`: move the robot to the specified cartesian coordinates
        `RelMovJ`: move the robot by the specified joint offsets
        `RelMovL`: move the robot by the specified cartesian offsets
    """
    
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
        self.dashboard_api: DobotApiDashboard|None = None
        self.move_api: DobotApiMove|None = None
        self.flags = deepcopy(self._default_flags)
        self.flags.simulation = simulation
        
        self._logger = logger.getChild(f"{self.__class__.__name__}.{id(self)}")
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
        CustomLevelFilter().setModuleLevel(self._logger.name, level)
        return
    
    def connect(self):
        """Connect to the device"""
        if self.is_connected:
            return
        if not connection.match_current_ip_address(self.host):
            self._logger.warning(f"Device  IP Address: {self.host}")
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
            self.ResetRobot()
            self.DisableRobot()
            self.close()
        except OSError as e:
            self._logger.error(f"Failed to disconnect from {self.host}")
            self._logger.debug(e)
        else:
            self._logger.info(f"Disconnected from {self.host}")
        self.flags.connected = False
        return
    
    def reset(self):
        """Reset the device"""
        self.DisableRobot()
        self.ClearError()
        self.EnableRobot()
        return
    
    def clear(self):                                                    # NOTE: not implemented
        """Clear the input and output buffers"""
        raise NotImplementedError
    
    def query(self, data:Any, lines:bool = True) -> list[str]|None:     # NOTE: not implemented
        """
        Query the device

        Args:
            data (Any): data to query

        Returns:
            list[str]|None: data read from the device, if any
        """
        raise NotImplementedError

    def read(self, lines:bool = False) -> str|list[str]:                # NOTE: not implemented
        """
        Read data from the device
        
        Args:
            lines (bool, optional): whether to read multiple lines. Defaults to False.
            
        Returns:
            str|list[str]: line(s) of data read from the device
        """
        raise NotImplementedError

    def write(self, data:str) -> bool:                                  # NOTE: not implemented
        """
        Write data to the device

        Args:
            data (str): data to write
        
        Returns:
            bool: whether the write was successful
        """
        raise NotImplementedError

    # Dobot API
    def close(self):
        """Close the connection to the device"""
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
        """Clear any errors on the device"""
        self._logger.debug("ClearError")
        return self.dashboard_api.ClearError() if isinstance(self.dashboard_api, DobotApiDashboard) else None
    
    def DisableRobot(self):
        """Disable the robot"""
        self._logger.debug("DisableRobot")
        return self.dashboard_api.DisableRobot() if isinstance(self.dashboard_api, DobotApiDashboard) else None
    
    def EnableRobot(self, *args):
        """Enable the robot"""
        self._logger.debug("EnableRobot")
        return self.dashboard_api.EnableRobot(*args) if isinstance(self.dashboard_api, DobotApiDashboard) else None
    
    def ResetRobot(self):
        """Stop the robot"""
        self._logger.debug("ResetRobot")
        return self.dashboard_api.ResetRobot() if isinstance(self.dashboard_api, DobotApiDashboard) else None
    
    def SetArmOrientation(self, right_handed:bool):
        """ 
        Set the handedness of the robot
        
        Args:
            right_handed (bool): whether to select right-handed mode
        """
        self._logger.debug(f"SetArmOrientation | {right_handed=}")
        return self.dashboard_api.SetArmOrientation(int(right_handed)) if isinstance(self.dashboard_api, DobotApiDashboard) else None
    
    def SpeedFactor(self, speed_factor:int):
        """
        Set the speed factor of the robot
        
        Args:
            speed_factor (int): speed factor to set
        """
        self._logger.debug(f"SpeedFactor | {speed_factor=}")
        return self.dashboard_api.SpeedFactor(speed_factor) if isinstance(self.dashboard_api, DobotApiDashboard) else None
    
    def GetAngle(self):
        """Get the angle of the robot"""
        self._logger.debug("GetAngle")
        return self.dashboard_api.GetAngle() if isinstance(self.dashboard_api, DobotApiDashboard) else None
    
    def GetPose(self):
        """Get the pose of the robot"""
        self._logger.debug("GetPose")
        return self.dashboard_api.GetPose() if isinstance(self.dashboard_api, DobotApiDashboard) else None
    
    def DOExecute(self, channel:int, on:int):
        """
        Execute a digital output
        
        Args:
            channel (int): channel of the digital output
            on (int): whether to enable the digital output (1 or 0)
        """
        self._logger.debug(f"DOExecute | {channel=}, {on=}")
        return self.dashboard_api.DOExecute(channel, on) if isinstance(self.dashboard_api, DobotApiDashboard) else None
    
    # Move API
    def JointMovJ(self, j1:float, j2:float, j3:float, j4:float, *args):
        """ 
        Move the robot to the specified joint coordinates
        
        Args:
            j1 (float): joint 1 coordinate
            j2 (float): joint 2 coordinate
            j3 (float): joint 3 coordinate
            j4 (float): joint 4 coordinate
        """
        self._logger.debug(f"JointMovJ | {j1=}, {j2=}, {j3=}, {j4=}")
        return self.move_api.JointMovJ(j1,j2,j3,j4, *args) if isinstance(self.move_api, DobotApiMove) else None    
    
    def MovJ(self, x:float, y:float, z:float, r:float, *args):
        """
        Move the robot to the specified cartesian coordinates
        
        Args:
            x (float): x-coordinate
            y (float): y-coordinate
            z (float): z-coordinate
            r (float): r-coordinate
        """
        self._logger.debug(f"MovJ | {x=}, {y=}, {z=}, {r=}")
        return self.move_api.MovJ(x,y,z,r, *args) if isinstance(self.move_api, DobotApiMove) else None
    
    def RelMovJ(self, offset1:float, offset2:float, offset3:float, offset4:float, *args):
        """
        Move the robot by the specified joint offsets
        
        Args:
            offset1 (float): joint 1 offset
            offset2 (float): joint 2 offset
            offset3 (float): joint 3 offset
            offset4 (float): joint 4 offset
        """
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
    