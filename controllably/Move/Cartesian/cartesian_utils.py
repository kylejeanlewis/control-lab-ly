# %% -*- coding: utf-8 -*-
"""
This module holds the base class for cartesian mover tools.

Classes:
    Gantry (Mover)
"""
# Standard library imports
from __future__ import annotations
import logging
from typing import Sequence

# Local application imports
from ...core.position import BoundingBox, Position,Deck
from ..gcode_utils import GCode

from abc import abstractmethod
import time
from typing import Optional
import numpy as np
from .. import Mover

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.debug(f"Import: OK <{__name__}>")
    
class Gantry(GCode):
    
    def __init__(self, 
        port: str,
        limits: Sequence[Sequence[float]] = ((0, 0, 0), (0, 0, 0)),     # in terms of robot coordinate system   # TODO: implement checking device for limits
        *, 
        robot_position: Position = Position(),
        home_position: Position = Position(),                   # in terms of robot coordinate system
        tool_offset: Position = Position(),
        calibrated_offset: Position = Position(),
        scale: float = 1.0,
        deck: Deck|None = None,
        safe_height: float|None = None,                         # in terms of robot coordinate system
        speed_max: float|None = 600,                            # in mm/min # TODO: implement checking device for speed_max
        device_type_name: str = 'GRBL',
        baudrate: int = 115200, 
        verbose: bool = False, 
        simulation: bool = False,
        **kwargs
    ):
        workspace = BoundingBox(buffer=limits)
        _speed_max = speed_max if speed_max is not None else 600
        super().__init__(
            port=port, baudrate=baudrate, 
            robot_position=robot_position, home_position=home_position,
            tool_offset=tool_offset, calibrated_offset=calibrated_offset, scale=scale, 
            deck=deck, workspace=workspace, safe_height=safe_height, speed_max=_speed_max, 
            device_type_name=device_type_name, verbose=verbose, simulation=simulation,
            **kwargs
        )
        
        self.connect()
        self.home()
        
        # Set limits if none provided
        if not any([any(l) for l in limits]):
            settings = self.device.checkSettings()
            _,coordinates,_ = self.device.checkStatus()
            device_limits = np.array(settings.get('limit_x',0),settings.get('limit_y',0),settings.get('limit_z',0))
            device_limits = device_limits * (coordinates/abs(coordinates)) if any(coordinates) else device_limits
            limits = np.array([coordinates,device_limits])
            limits = np.array([limits.min(axis=0),limits.max(axis=0)])
            self.workspace = BoundingBox(buffer=limits)
        
        # Set maximum speed if none provided
        if speed_max is None:
            settings = self.device.checkSettings()
            speed_max = max([settings.get('max_speed_x',0),settings.get('max_speed_y',0),settings.get('max_speed_z',0)])
            self._speed_max = 600 if speed_max <= 0 else speed_max
        return
    
    @property
    def limits(self):
        return self.workspace.buffer
    
    
class _Gantry(Mover):
    """
    Abstract Base Class (ABC) for Gantry objects. Gantry provides controls for a general cartesian robot.
    ABC cannot be instantiated, and must be subclassed with abstract methods implemented before use.
    Gantry provides controls for a general cartesian robot

    ### Constructor
    Args:
        `port` (str): COM port address
        `limits` (tuple[tuple[float]], optional): lower and upper limits of gantry. Defaults to ((0, 0, 0), (0, 0, 0)).
        `safe_height` (Optional[float], optional): height at which obstacles can be avoided. Defaults to None.
    
    ### Properties
    - `limits` (np.ndarray): lower and upper limits of gantry
    - `port` (str): COM port address
    - `max_accels` (np.ndarray): array of maximum accelerations for each axis
    
    ### Methods
    #### Abstract
    - `getAcceleration`: get maximum acceleration rates (mm/s^2)
    - `getCoordinates`: get current coordinates from device
    - `getMaxSpeeds`: get maximum speeds (mm/s)
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
        accel_max: Optional[dict[str, float]] = None,
        *,
        baudrate: int = 115200,
        verbose: bool = False,
        **kwargs
    ):
        """
        Instantiate the class

        Args:
            port (str): COM port address
            limits (tuple[tuple[float]], optional): lower and upper limits of gantry. Defaults to ((0, 0, 0), (0, 0, 0)).
            safe_height (Optional[float], optional): height at which obstacles can be avoided. Defaults to None.
        """
        workspace = BoundingBox(buffer=limits)
        super().__init__(
            port=port, baudrate=baudrate, verbose=verbose, 
            workspace=workspace, safe_height=safe_height, **kwargs
        )
        self._accel_max = dict(general=np.nan)
        self._limits = ((0, 0, 0), (0, 0, 0))
        
        self.limits = limits
        
        # self._connect(port)
        # if 'speed_max' not in kwargs:
        #     self.getMaxSpeeds()
        # if accel_max is None:
        #     self.getAcceleration()
        # else:
        #     self._accel_max = accel_max
        # self.home()
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
    def getMaxSpeeds(self) -> np.ndarray:
        """
        Get maximum speeds (mm/s)

        Returns:
            np.ndarray: maximum speeds
        """
        self.max_feedrate = np.linalg.norm(self.max_speeds[:2])
        return
    
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
    def max_accels(self) -> np.ndarray:
        accels = [self._accel_max.get('general', 0)] * 6
        movement_L = ('x','y','z','a','b','c')
        movement_J = ('j1','j2','j3','j4','j5','j6')
        for a in self._accel_max:
            if type(a) is not str:
                break
            if a.lower() in movement_L:
                accels = [self._accel_max.get(axis, np.nan) for axis in movement_L]
                break
            if a.lower() in movement_J:
                accels = [self._accel_max.get(axis, np.nan) for axis in movement_J]
                break
        return np.array(accels)
    
    @property
    def port(self) -> str:
        return self.connection_details.get('port', '')
    
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
        # if transform_in:
        #     coordinates = self._transform_in(coordinates=coordinates, tool_offset=tool_offset)
        # coordinates = np.array(coordinates)
        # l_bound, u_bound = self.limits
        
        # if all(np.greater_equal(coordinates, l_bound)) and all(np.less_equal(coordinates, u_bound)):
        #     return not self.deck.isExcluded(self._transform_out(coordinates, tool_offset=True))
        # logger.warning(f"Range limits reached! {self.limits}")
        # return False

    def moveBy(self,
        vector: tuple[float] = (0,0,0), 
        angles: tuple[float] = (0,0,0), 
        speed_factor: Optional[float] = None,
        **kwargs
    ) -> bool:
        """
        Move the robot by target direction

        Args:
            vector (tuple[float], optional): x,y,z vector to move in. Defaults to (0,0,0).
            angles (tuple[float], optional): a,b,c angles to move in. Defaults to (0,0,0).
            speed_factor (Optional[float], optional): speed factor of travel. Defaults to None.

        Returns:
            bool: whether the movement is successful
        """
        return super().moveBy(vector=vector, speed_factor=speed_factor)
    
    # @Helper.safety_measures
    def moveTo(self, 
        coordinates: tuple[float], 
        orientation: Optional[tuple[float]] = None,
        tool_offset: bool = True, 
        speed_factor: Optional[float] = None, 
        **kwargs
    ) -> bool:
        """
        Move the robot to target position

        Args:
            coordinates (tuple[float]): x,y,z coordinates to move to
            orientation (Optional[tuple[float]], optional): a,b,c orientation to move to. Defaults to None.
            tool_offset (bool, optional): whether to consider tooltip offset. Defaults to True.
            speed_factor (Optional[float], optional): speed factor of travel. Defaults to None.

        Returns:
            bool: whether movement is successful
        """
        coordinates = np.array(self._transform_in(coordinates=coordinates, tool_offset=tool_offset))
        if not self.isFeasible(coordinates):
            return False
        distances = abs(self.coordinates - coordinates)
        speed_factor = self.speed_factor if speed_factor is None else speed_factor
        speed_change, prevailing_speed_factor = False, self.speed_factor
        if self.speed_factor != speed_factor:
            speed_change = True
            
        z_first = True if (self.coordinates[2] < coordinates[2]) else False
        positionXY = f'X{coordinates[0]}Y{coordinates[1]}'
        position_Z = f'Z{coordinates[2]}'
        moves = [position_Z, positionXY] if z_first else [positionXY, position_Z]
        moves = [positionXY] if coordinates[2]==self.coordinates[2] else moves
        moves = [position_Z] if (coordinates[0]==self.coordinates[0] and coordinates[1]==self.coordinates[1]) else moves
        
        self.device.query("G90")
        for move in moves:
            if distances[2] and 'Z' in move:
                _max_feedrate = self.max_feedrate
                self.max_feedrate = self.max_speeds[2]
            
            self.setSpeedFactor(speed_factor)
            self.device.query(f"G1 {move}")
            
            if distances[2] and 'Z' in move:
                self.max_feedrate = _max_feedrate
            self.setSpeedFactor(prevailing_speed_factor)
        
        if kwargs.get('wait', True) and self.isConnected():
            distances = abs(self.coordinates - coordinates)
            speeds = self.max_speeds[:3] * speed_factor
            accels = self.max_accels[:3]
            
            move_time = self._get_move_wait_time(distances=distances, speeds=speeds, accels=accels)
            logger.info(f'Move for {move_time}s...')
            time.sleep(move_time)
        self.updatePosition(coordinates=coordinates)
        
        if speed_change:
            self.setSpeedFactor(prevailing_speed_factor)
        return True
    
    def reset(self):
        """Reset the robot"""
        self.disconnect()
        self.connect()
        return
    
    def setSpeed(self, speed: float) -> tuple[bool, float]:
        """
        Set the speed of the robot

        Args:
            speed (float): speed in mm/s
        
        Returns:
            tuple[bool, float]: whether speed has changed; prevailing speed
        """
        if speed == self.speed or speed is None:
            return False, self.speed
        prevailing_speed = self.speed
        speed = min(speed, self.max_feedrate)
        self.device.query(f"F{int(speed*60)}")                                # feed rate (i.e. speed) in mm/min
        self._speed_factor = speed/self.max_feedrate
        return True, prevailing_speed
    
    def setSpeedFactor(self, speed_factor: float) -> tuple[bool, float]:
        """
        Set the speed fraction of the robot

        Args:
            speed_factor (float): speed fraction between 0 and 1
        
        Returns:
            tuple[bool, float]: whether speed has changed; prevailing speed fraction
        """
        if speed_factor == self.speed_factor or speed_factor is None:
            return False, self.speed_factor
        if speed_factor < 0 or speed_factor > 1:
            return False, self.speed_factor
        prevailing_speed_factor = self.speed_factor
        ret,_ = self.setSpeed(self.max_feedrate * speed_factor)
        if ret:
            self._speed_factor = speed_factor
        return ret, prevailing_speed_factor
    
    def shutdown(self):
        """Shutdown procedure for tool"""
        # self.home()
        return super().shutdown()
    
    # Protected method(s)
    # def _connect(self, port:str, baudrate:int = 115200, timeout:int = 1):
    #     """
    #     Connection procedure for tool

    #     Args:
    #         port (str): COM port address
    #         baudrate (int, optional): baudrate. Defaults to 115200.
    #         timeout (int, optional): timeout in seconds. Defaults to 1.
    #     """
        # self.connection_details = {
        #     'port': port,
        #     'baudrate': baudrate,
        #     'timeout': timeout
        # }
        # device = None
        # try:
        #     device = serial.Serial(port, baudrate, timeout=timeout)
        # except Exception as e:
        #     logger.warning(f"Could not connect to {port}")
        #     logger.exception(e, exc_info=self.verbose)
        #     self.max_feedrate = np.linalg.norm(self.max_speeds[:2])
        # else:
        #     self.device = device
        #     time.sleep(2)
        #     logger.info(f"Connection opened to {port}")
        #     self.setFlag(connected=True)
        # return

    # def _query(self, command:str) -> list[str]:
    #     """
    #     Write command to and read response from device

    #     Args:
    #         command (str): command string to send to device

    #     Returns:
    #         list[str]: list of response string(s) from device
    #     """
    #     responses = [b'']
    #     self._write(command)
    #     responses = self._read()
    #     try:
    #         self.device.flush()
    #         self.device.reset_output_buffer()
    #     except Exception as e:
    #         logger.exception(e, exc_info=self.verbose)
    #     return [r.decode("utf-8", "replace").strip() for r in responses]
    
    # def _read(self) -> list[str]:
    #     """
    #     Read responses from device

    #     Returns:
    #         list[str]: list of response string(s) from device
    #     """
    #     responses = []
    #     try:
    #         responses = self.device.readlines()
    #     except Exception as e:
    #         logger.exception(e, exc_info=self.verbose)
    #     else:
    #         if self.verbose and len(responses):
    #             logger.debug(responses)
    #     return responses

    # def _write(self, command:str) -> bool:
    #     """
    #     Write command to device

    #     Args:
    #         command (str): command string to send to device

    #     Returns:
    #         bool: whether the command is sent successfully
    #     """
    #     command = f"{command}\n" if not command.endswith('\n') else command
    #     if self.verbose:
    #         logger.debug(command)
    #     try:
    #         self.device.write(command.encode('utf-8'))
    #     except Exception as e:
    #         if self.verbose:
    #             print(e)
    #         return False
    #     return True
