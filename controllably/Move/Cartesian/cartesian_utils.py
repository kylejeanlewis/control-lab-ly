# %% -*- coding: utf-8 -*-
"""
This module holds the base class for cartesian mover tools.

Classes:
    Gantry (Mover)
"""
# Standard library imports
from __future__ import annotations
from abc import abstractmethod
import numpy as np
import time
from typing import Optional

# Third party imports
import serial # pip install pyserial

# Local application imports
from ...misc import Helper
from ..move_utils import Mover
print(f"Import: OK <{__name__}>")
    
class Gantry(Mover):
    """
    Abstract Base Class (ABC) for Gantry objects. Gantry provides controls for a general cartesian robot.
    ABC cannot be instantiated, and must be subclassed with abstract methods implemented before use.
    Gantry provides controls for a general cartesian robot

    ### Constructor
    Args:
        `port` (str): COM port address
        `limits` (tuple[tuple[float]], optional): lower and upper limits of gantry. Defaults to ((0, 0, 0), (0, 0, 0)).
        `safe_height` (Optional[float], optional): height at which obstacles can be avoided. Defaults to None.
        `max_speed` (float, optional): maximum travel speed. Defaults to 250.
    
    ### Properties
    - `limits` (np.ndarray):lower and upper limits of gantry
    - `port` (str): COM port address
    
    ### Methods
    #### Abstract
    - `getAcceleration`: get maximum acceleration rates (mm/s^2)
    - `getCoordinates`: get current coordinates from device
    - `getMaxSpeed`: get maximum speeds (mm/s)
    - `home`: make the robot go home
    #### Public
    - `disconnect`: disconnect from device
    - `isFeasible`: checks and returns whether the target coordinate is feasible
    - `moveBy`: move the robot by target direction
    - `moveTo`: move the robot to target position
    - `reset`: reset the robot
    - `setSpeed`: set the speed of the robot
    - `shutdown`: shutdown procedure for tool
    """
    
    _place: str = '.'.join(__name__.split('.')[1:-1])
    def __init__(self, 
        port: str, 
        limits: tuple[tuple[float]] = ((0, 0, 0), (0, 0, 0)), 
        safe_height: Optional[float] = None, 
        max_speed: float = 250, # [mm/s] (i.e. 15,000 mm/min)
        **kwargs
    ):
        """
        Instantiate the class

        Args:
            port (str): COM port address
            limits (tuple[tuple[float]], optional): lower and upper limits of gantry. Defaults to ((0, 0, 0), (0, 0, 0)).
            safe_height (Optional[float], optional): height at which obstacles can be avoided. Defaults to None.
            max_speed (float, optional): maximum travel speed. Defaults to 250.
        """
        super().__init__(**kwargs)
        self._limits = ((0, 0, 0), (0, 0, 0))
        
        self.limits = limits
        self._speed_max = dict(general=max_speed)
        if safe_height is not None:
            self.setHeight(safe=safe_height)
        
        self._connect(port)
        self.home()
        return
    
    @abstractmethod
    def getAcceleration(self) -> np.ndarray:
        """
        Get maximum acceleration rates (mm/s^2)

        Returns:
            np.ndarray: acceleration rates
        """
    
    @abstractmethod
    def getCoordinates(self) -> np.ndarray:
        """
        Get current coordinates from device

        Returns:
            np.ndarray: current device coordinates
        """
    
    @abstractmethod
    def getMaxSpeed(self) -> np.ndarray:
        """
        Get maximum speeds (mm/s)

        Returns:
            np.ndarray: maximum speeds
        """
    
    @abstractmethod
    def getSettings(self) -> list[str]:
        """
        Get hardware settings

        Returns:
            list[str]: hardware settings
        """
    
    # Properties
    @property
    def limits(self) -> np.ndarray:
        return np.array(self._limits)
    @limits.setter
    def limits(self, value:list):
        if len(value) != 2 or any([len(row)!=3 for row in value]):
            raise Exception('Please input a sequence of (lower_xyz_limit, upper_xyz_limit)')
        self._limits = ( tuple(value[0]), tuple(value[1]) )
        return
    
    @property
    def port(self) -> str:
        return self.connection_details.get('port', '')

    def disconnect(self):
        """ Disconnect from device """
        try:
            self.device.close()
        except Exception as e:
            if self.verbose:
                print(e)
        self.setFlag(connected=False)
        return
    
    def isFeasible(self, 
        coordinates: tuple[float], 
        transform_in: bool = False, 
        tool_offset: bool = False, 
        **kwargs
    ) -> bool:
        """
        Checks and returns whether the target coordinate is feasible

        Args:
            coordinates (tuple[float]): target coordinates
            transform_in (bool, optional): whether to convert to internal coordinates first. Defaults to False.
            tool_offset (bool, optional): whether to convert from tool tip coordinates first. Defaults to False.

        Returns:
            bool: whether the target coordinate is feasible
        """
        if transform_in:
            coordinates = self._transform_in(coordinates=coordinates, tool_offset=tool_offset)
        coordinates = np.array(coordinates)
        l_bound, u_bound = self.limits
        
        if all(np.greater_equal(coordinates, l_bound)) and all(np.less_equal(coordinates, u_bound)):
            return not self.deck.isExcluded(self._transform_out(coordinates, tool_offset=True))
        print(f"Range limits reached! {self.limits}")
        return False

    def moveBy(self, vector:tuple[float], **kwargs) -> bool:
        """
        Move the robot by target direction

        Args:
            vector (tuple[float]): x,y,z vector to move in

        Returns:
            bool: whether the movement is successful
        """
        return super().moveBy(vector=vector)
    
    @Helper.safety_measures
    def moveTo(self, coordinates:tuple[float], tool_offset:bool = True, **kwargs) -> bool:
        """
        Move the robot to target position

        Args:
            coordinates (tuple[float]): x,y,z coordinates to move to
            tool_offset (bool, optional): whether to consider tooltip offset. Defaults to True.

        Returns:
            bool: whether movement is successful
        """
        coordinates = np.array(self._transform_in(coordinates=coordinates, tool_offset=tool_offset))
        if not self.isFeasible(coordinates):
            return False
            
        z_first = True if (self.coordinates[2] < coordinates[2]) else False
        positionXY = f'X{coordinates[0]}Y{coordinates[1]}'
        position_Z = f'Z{coordinates[2]}'
        moves = [position_Z, positionXY] if z_first else [positionXY, position_Z]
        moves = [positionXY] if coordinates[2]==self.coordinates[2] else moves
        moves = [position_Z] if (coordinates[0]==self.coordinates[0] and coordinates[1]==self.coordinates[1]) else moves
        
        self._query("G90")
        for move in moves:
            self._query(f"G1 {move}")
        
        if kwargs.get('wait', True):
            distances = abs(self.coordinates - coordinates)
            times = [self._calculate_travel_time(d, s) for d,s in zip(distances, self.speed[:3])]
            print(times)
            move_time = max(times[:2]) + times[2]
            time.sleep(move_time)
        self.updatePosition(coordinates=coordinates)
        return True
    
    def reset(self):
        """Reset the robot"""
        self.disconnect()
        self.connect()
        return
    
    def setSpeed(self, speed: int, axis:str = 'x') -> tuple[bool, float]:
        """
        Set the speed of the robot

        Args:
            speed (int): speed in mm/s
            axis (str, optional): axis speed to be changed. Defaults to 'x'.
        
        Returns:
            tuple[bool, float]: whether speed has changed; prevailing speed
        """
        print(f'Speed: {speed} mm/s')
        max_speed = self._speed_max[axis]
        self._speed_fraction = (speed/max_speed)
        speed = int(max_speed*self._speed_fraction * 60)    # get speed in mm/min
        self._query(f"F{speed}")                            # feed rate (i.e. speed) in mm/min
        return True, self.speed
    
    def setSpeedFraction(self, speed_fraction: float) -> tuple[bool, float]:
        """
        Set the speed fraction of the robot

        Args:
            speed_fraction (float): speed fraction between 0 and 1
        
        Returns:
            tuple[bool, float]: whether speed has changed; prevailing speed fraction
        """
        print(f'Speed fraction: {speed_fraction}')
        prevailing_speed_fraction = self._speed_fraction
        self._speed_fraction = speed_fraction
        self._query(f"M220 S{int(speed_fraction*100)}")
        return True, self.max_speed*prevailing_speed_fraction
    
    def shutdown(self):
        """Shutdown procedure for tool"""
        # self.home()
        return super().shutdown()
    
    # Protected method(s)
    def _connect(self, port:str, baudrate:int = 115200, timeout:int = 0.2):
        """
        Connection procedure for tool

        Args:
            port (str): COM port address
            baudrate (int, optional): baudrate. Defaults to 115200.
            timeout (int, optional): timeout in seconds. Defaults to 1.
        """
        self.connection_details = {
            'port': port,
            'baudrate': baudrate,
            'timeout': timeout
        }
        device = None
        try:
            device = serial.Serial(port, baudrate, timeout=timeout)
        except Exception as e:
            print(f"Could not connect to {port}")
            if self.verbose:
                print(e)
        else:
            self.device = device
            time.sleep(2)
            print(f"Connection opened to {port}")
            self.setFlag(connected=True)
            self.getMaxSpeed()
        return

    def _query(self, command:str) -> list[str]:
        """
        Write command to and read response from device

        Args:
            command (str): command string to send to device

        Returns:
            list[str]: list of response string(s) from device
        """
        responses = [b'']
        self._write(command)
        try:
            responses = self.device.readlines()
        except Exception as e:
            if self.verbose:
                print(e)
        else:
            if self.verbose:
                print(responses)
        return [r.decode().strip() for r in responses]

    def _write(self, command:str) -> bool:
        """
        Write command to device

        Args:
            command (str): command string to send to device

        Returns:
            bool: whether the command is sent successfully
        """
        command = f"{command}\n" if not command.endswith('\n') else command
        if self.verbose:
            print(command)
        try:
            self.device.write(command.encode('utf-8'))
        except Exception as e:
            if self.verbose:
                print(e)
            return False
        return True
