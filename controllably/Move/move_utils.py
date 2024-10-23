# %% -*- coding: utf-8 -*-
"""
This module holds the base class for mover tools.

Classes:
    Mover (ABC)
"""
# Standard library imports
from __future__ import annotations
from abc import ABC, abstractmethod
import math

# Third party imports
import numpy as np
from scipy.spatial.transform import Rotation

# Local application imports
from ..misc.layout import Deck, Position
print(f"Import: OK <{__name__}>")

class Mover(ABC):
    """
    Abstract Base Class (ABC) for Mover objects (i.e. tools that move objects in space).
    ABC cannot be instantiated, and must be subclassed with abstract methods implemented before use.
    
    ### Constructor
    Args:
        `coordinates` (tuple[float], optional): current coordinates of the robot. Defaults to (0,0,0).
        `deck` (Deck, optional): Deck object for workspace. Defaults to Deck().
        `home_coordinates` (tuple[float], optional): home coordinates for the robot. Defaults to (0,0,0).
        `home_orientation` (tuple[float], optional): home orientation for the robot. Defaults to (0,0,0).
        `implement_offset` (tuple[float], optional): transformation (translation) vector to get from end effector to tool tip. Defaults to (0,0,0).
        `orientate_matrix` (np.ndarray, optional): transformation (rotation) matrix to get from robot to workspace. Defaults to np.identity(3).
        `orientation` (tuple[float], optional): current orientation of the robot. Defaults to (0,0,0).
        `scale` (float, optional): factor to scale the basis vectors by. Defaults to 1.
        `speed_max` (dict[str, float], optional): dictionary of robot maximum speeds. Defaults to dict(general=1).
        `speed_factor` (float, optional): fraction of maximum speed to travel at. Defaults to 1.
        `translate_vector` (tuple[float], optional): transformation (translation) vector to get from robot to end effector. Defaults to (0,0,0).
        `verbose` (bool, optional): verbosity of class. Defaults to False.
    
    ### Attributes
    - `connection_details` (dict): dictionary of connection details (e.g. COM port / IP address)
    - `deck` (Deck): Deck object for workspace
    - `device` (Callable): device object that communicates with physical tool
    - `flags` (dict[str, bool]): keywords paired with boolean flags
    - `heights` (dict[str, float]): specified height names and values
    - `verbose` (bool): verbosity of class
    
    ### Properties
    - `coordinates` (np.ndarray): current coordinates of the robot
    - `home_coordinates` (np.ndarray): home coordinates for the robot
    - `home_orientation` (np.ndarray): home orientation for the robot
    - `implement_offset` (np.ndarray): transformation (translation) vector to get from end effector to tool tip
    - `max_speeds` (np.ndarray): maximum speed(s) of robot
    - `orientate_matrix` (np.ndarray): transformation (rotation) matrix to get from robot to workspace
    - `orientation` (np.ndarray): current orientation of the robot
    - `position` (tuple[np.ndarray]): 2-uple of (coordinates, orientation)
    - `scale` (float): factor to scale the basis vectors by
    - `speed` (float): travel speed of robot
    - `speed_factor` (float): fraction of maximum travel speed of robot
    - `tool_position` (tuple[np.ndarray]): 2-uple of tool tip (coordinates, orientation)
    - `translate_vector` (np.ndarray): transformation (translation) vector to get from robot to end effector
    - `user_position` (tuple[np.ndarray]): 2-uple of user-defined workspace (coordinates, orientation)
    - `workspace_position` (tuple[np.ndarray]): 2-uple of workspace (coordinates, orientation)
    
    ### Methods
    #### Abstract
    - `disconnect`: disconnect from device
    - `home`: make the robot go home
    - `isFeasible`: checks and returns whether the target coordinates is feasible
    - `moveBy`: move the robot by target direction
    - `moveTo`: move the robot to target position
    - `reset`: reset the robot
    - `setSpeed`: set the speed of the robot
    - `setSpeedFactor`: set the speed factor of the robot
    - `shutdown`: shutdown procedure for tool
    - `stop`: halt robot movement
    - `_connect`: connection procedure for tool
    #### Public
    - `calibrate`: calibrate the internal and external coordinate systems
    - `connect`: establish connection with device
    - `getConfigSettings`: retrieve the robot's configuration
    - `isBusy`: checks and returns whether the device is busy
    - `isConnected`: checks and returns whether the device is connected
    - `loadDeck`: load Labware objects onto the deck from file or dictionary
    - `move`: move the robot in a specific axis by a specific value
    - `resetFlags`: reset all flags to class attribute `_default_flags`
    - `safeMoveTo`: safe version of moveTo by moving in Z-axis first
    - `setFlag`: set flags by using keyword arguments
    - `setHeight`: set predefined heights using keyword arguments
    - `setImplementOffset`: set offset of attached implement, then home if desired
    - `updatePosition`: update attributes to current position
    """
    
    _default_flags: dict[str, bool] = {'busy': False, 'connected': False}
    _default_heights: dict[str, float] = {}
    _default_move_time_buffer: float = 0
    _place: str = '.'.join(__name__.split('.')[1:-1])
    def __init__(self, 
        coordinates: tuple[float] = (0,0,0),
        deck: Deck = Deck(),
        home_coordinates: tuple[float] = (0,0,0),
        home_orientation: tuple[float] = (0,0,0),
        implement_offset: tuple[float] = (0,0,0),
        orientate_matrix: np.ndarray = np.identity(3),
        orientation: tuple[float] = (0,0,0),
        scale: float = 1.0,
        speed_max: dict[str, float] = dict(general=20),
        speed_factor: float = 1.0,
        translate_vector: tuple[float] = (0,0,0),
        saved_positions: dict = dict(),
        verbose: bool = False,
        **kwargs
    ):
        """
        Instantiate the class

        Args:
            coordinates (tuple[float], optional): current coordinates of the robot. Defaults to (0,0,0).
            deck (Deck, optional): Deck object for workspace. Defaults to Deck().
            home_coordinates (tuple[float], optional): home coordinates for the robot. Defaults to (0,0,0).
            home_orientation (tuple[float], optional): home_orientation for the robot. Defaults to (0,0,0).
            implement_offset (tuple[float], optional): transformation (translation) vector to get from end effector to tool tip. Defaults to (0,0,0).
            orientate_matrix (np.ndarray, optional): transformation (rotation) matrix to get from robot to workspace. Defaults to np.identity(3).
            orientation (tuple[float], optional): current orientation of the robot. Defaults to (0,0,0).
            scale (float, optional): factor to scale the basis vectors by. Defaults to 1.0.
            speed_max (dict[str, float], optional): dictionary of robot maximum speeds. Defaults to dict(general=1).
            speed_factor (float, optional): fraction of maximum speed to travel at. Defaults to 1.0.
            translate_vector (tuple[float], optional): transformation (translation) vector to get from robot to end effector. Defaults to (0,0,0).
            verbose (bool, optional): verbosity of class. Defaults to False.
        """
        self.deck = deck
        self._position = Position(coordinates, Rotation.from_euler('zyx',orientation), 'euler')
        # self._coordinates = coordinates
        # self._orientation = orientation
        
        self._home_position = Position(home_coordinates, Rotation.from_euler('zyx',home_orientation), 'euler')
        # self._home_coordinates = home_coordinates
        # self._home_orientation = home_orientation
        
        self._calibration_position = Position(translate_vector, Rotation.from_matrix(orientate_matrix), 'matrix')
        # self._orientate_matrix = orientate_matrix
        # self._translate_vector = translate_vector
        
        self._implement_offset = Position(implement_offset)
        self._scale = scale
        self._speed_max = speed_max
        self._speed_factor = speed_factor
        self._move_time_buffer = self._default_move_time_buffer
        
        self.connection_details = {}
        self.device = None
        self.flags = self._default_flags.copy()
        self.heights = self._default_heights.copy()
        self.max_feedrate = 100
        self.saved_positions = saved_positions
        self.verbose = verbose
        return
    
    def __del__(self):
        self.shutdown()
        return
    
    @abstractmethod
    def disconnect(self):
        """Disconnect from device"""
        self.setFlag(connected=False)
        return
        
    @abstractmethod
    def home(self) -> bool:
        """Make the robot go home"""

    @abstractmethod
    def isFeasible(self, 
        coordinates: tuple[float], 
        transform_in: bool = False, 
        tool_offset: bool = False, 
        **kwargs
    ) -> bool:
        """
        Checks and returns whether the target coordinates is feasible

        Args:
            coordinates (tuple[float]): target coordinates
            transform_in (bool, optional): whether to convert to internal coordinates first. Defaults to False.
            tool_offset (bool, optional): whether to convert from tool tip coordinates first. Defaults to False.

        Returns:
            bool: whether the target coordinate is feasible
        """
        return not self.deck.isExcluded(self._transform_out(coordinates, tool_offset=True))
    
    @abstractmethod
    def moveBy(self, 
        vector: tuple[float] = (0,0,0), 
        angles: tuple[float] = (0,0,0), 
        speed_factor: float|None = None,
        **kwargs
    ) -> bool:
        """
        Move the robot by target direction

        Args:
            vector (tuple[float], optional): x,y,z vector to move in. Defaults to (0,0,0).
            angles (tuple[float], optional): a,b,c angles to move in. Defaults to (0,0,0).
            speed_factor (float|None, optional): speed factor of travel. Defaults to None.

        Returns:
            bool: whether the movement is successful
        """
        vector = np.array(vector)
        angles = np.array(angles)
        user_position = self.user_position
        new_coordinates = np.round( user_position[0] + np.array(vector) , 2)
        new_orientation = np.round( user_position[1] + np.array(angles) , 2)
        return self.moveTo(coordinates=new_coordinates, orientation=new_orientation, tool_offset=False, speed_factor=speed_factor, **kwargs)
 
    @abstractmethod
    def moveTo(self, 
        coordinates: tuple[float]|None = None, 
        orientation: tuple[float]|None = None, 
        tool_offset: bool = False, 
        speed_factor: float|None = None,
        **kwargs
    ) -> bool:
        """
        Move the robot to target position

        Args:
            coordinates (tuple[float]|None, optional): x,y,z coordinates to move to. Defaults to None.
            orientation (tuple[float]|None, optional): a,b,c orientation to move to. Defaults to None.
            tool_offset (bool, optional): whether to consider tooltip offset. Defaults to False.
            speed_factor (float|None, optional): speed factor of travel. Defaults to None.

        Returns:
            bool: whether movement is successful
        """
        if coordinates is None:
            coordinates = self.tool_position if tool_offset else self.user_position
        if orientation is None:
            orientation = self.orientation
        coordinates = self._transform_in(coordinates=coordinates, tool_offset=tool_offset)
        coordinates = np.array(coordinates)
        orientation = np.array(orientation)
        
        if not self.isFeasible(coordinates):
            return False
        self.coordinates = coordinates
        self.orientation = orientation
        speed_factor = self.speed_factor if speed_factor is None else speed_factor
        speed_change, prevailing_speed_factor = False, self.speed_factor
        if self.speed_factor != speed_factor:
            speed_change, prevailing_speed_factor = self.setSpeedFactor(speed_factor)
        if speed_change:
            self.setSpeedFactor(prevailing_speed_factor)
        return True
 
    @abstractmethod
    def reset(self):
        """Reset the robot"""
    
    @abstractmethod
    def setSpeed(self, speed:float) -> tuple[bool, float]:
        """
        Set the speed of the robot

        Args:
            speed (float): rate value (value range: 1~100)
            
        Returns:
            tuple[bool, float]: whether speed has changed; prevailing speed
        """
        
    @abstractmethod
    def setSpeedFactor(self, speed_factor:float) -> tuple[bool, float]:
        """
        Set the speed factor of the robot

        Args:
            speed_factor (float): speed ratio of max speed (value range: 0 to 1)
            
        Returns:
            tuple[bool, float]: whether speed has changed; prevailing speed factor
        """
    
    @abstractmethod
    def shutdown(self):
        """Shutdown procedure for tool"""
        self.disconnect()
        self.resetFlags()
        return
    
    @abstractmethod
    def stop(self):
        """Halt robot movement"""
 
    @abstractmethod
    def _connect(self, *args, **kwargs):
        """Connection procedure for tool"""
        self.connection_details = {}
        self.device = None
        self.setFlag(connected=True)
        return
 
    # Properties
    @property
    def coordinates(self) -> np.ndarray:
        """Current coordinates of the robot"""
        return self._position.coordinates
    @coordinates.setter
    def coordinates(self, value):
        self._position.coordinates = value
        return
    
    @property
    def home_coordinates(self) -> np.ndarray:
        """Home coordinates for the robot"""
        return self._home_position.coordinates
    @home_coordinates.setter
    def home_coordinates(self, value):
        self._home_position.coordinates = value
        return
    
    @property
    def home_orientation(self) -> np.ndarray:
        """Home orientation for the robot"""
        return self._home_position.rotation
    @home_orientation.setter
    def home_orientation(self, value):
        self._home_position.rotation = value
        return

    @property
    def implement_offset(self) -> np.ndarray:
        """Transformation (translation) vector to get from end effector to tool tip"""
        return self._implement_offset.coordinates
    @implement_offset.setter
    def implement_offset(self, value):
        self._implement_offset.coordinates = value
        return
    
    @property
    def max_speeds(self) -> np.ndarray:
        """Maximum speed(s) of robot"""
        speeds = [self._speed_max.get('general', 1)] * 6
        movement_L = ('x','y','z','a','b','c')
        movement_J = ('j1','j2','j3','j4','j5','j6')
        for s in self._speed_max:
            if type(s) is not str:
                break
            if s.lower() in movement_L:
                speeds = [self._speed_max.get(axis, np.nan) for axis in movement_L]
                break
            if s.lower() in movement_J:
                speeds = [self._speed_max.get(axis, np.nan) for axis in movement_J]
                break
        return np.array(speeds)
    
    @property
    def orientate_matrix(self) -> np.ndarray:
        """Transformation (rotation) matrix to get from robot to workspace"""
        return self._calibration_position.rotation
    @orientate_matrix.setter
    def orientate_matrix(self, value):
        self._calibration_position.rotation = value
        return
    
    @property
    def orientation(self) -> np.ndarray:
        """Current orientation of the robot"""
        return self._position.rotation
    @orientation.setter
    def orientation(self, value):
        self._position.rotation = value
        return
    
    @property
    def position(self) -> tuple[np.ndarray]:
        """2-uple of (coordinates, orientation)"""
        return self.coordinates, self.orientation
    
    @property
    def scale(self) -> float:
        """Factor to scale the basis vectors by"""
        return self._scale
    @scale.setter
    def scale(self, value):
        if value <= 0:
            raise Exception('Please input a positive scale factor')
        self._scale = float(value)
        return
    
    @property
    def speed(self) -> float:
        """Travel speed of robot"""
        return self._speed_factor * self.max_feedrate
    
    @property
    def speed_factor(self) -> float:
        """Fraction of maximum travel speed of robot"""
        return self._speed_factor
 
    @property
    def tool_position(self) -> tuple[np.ndarray]:
        """2-uple of tool tip (coordinates, orientation)"""
        coordinates = self._transform_out(coordinates=self.coordinates, tool_offset=True)
        return np.array(coordinates), self.orientation
 
    @property
    def translate_vector(self) -> np.ndarray:
        """Transformation (translation) vector to get from robot to end effector"""
        return self._calibration_position.coordinates
    @translate_vector.setter
    def translate_vector(self, value):
        self._calibration_position.coordinates = value
        return
    
    @property
    def user_position(self) -> tuple[np.ndarray]:
        """2-uple of user-defined workspace (coordinates, orientation)"""
        coordinates = self._transform_out(coordinates=self.coordinates, tool_offset=False)
        return np.array(coordinates), self.orientation
    
    @property
    def workspace_position(self) -> tuple[np.ndarray]:
        """2-uple of workspace (coordinates, orientation). Alias for `user_position`"""
        return self.user_position
 
    def calibrate(self, 
        external_pt1: np.ndarray, 
        internal_pt1: np.ndarray, 
        external_pt2: np.ndarray, 
        internal_pt2: np.ndarray
    ):
        """
        Calibrate the internal and external coordinate systems

        Args:
            external_pt1 (np.ndarray): x,y,z coordinates of physical point 1
            internal_pt1 (np.ndarray): x,y,z coordinates of robot point 1
            external_pt2 (np.ndarray): x,y,z coordinates of physical point 2
            internal_pt2 (np.ndarray): x,y,z coordinates of robot point 2
        """
        external_pt1 = np.array(external_pt1)
        external_pt2 = np.array(external_pt2)
        internal_pt1 = np.array(internal_pt1)
        internal_pt2 = np.array(internal_pt2)
        
        space_vector = external_pt2 - external_pt1
        robot_vector = internal_pt2 - internal_pt1
        space_mag = np.linalg.norm(space_vector)
        robot_mag = np.linalg.norm(robot_vector)

        space_unit_vector = space_vector / space_mag
        robot_unit_vector = robot_vector / robot_mag
        dot_product = np.dot(robot_unit_vector, space_unit_vector)
        cross_product = np.cross(robot_unit_vector, space_unit_vector)

        cos_theta = dot_product
        sin_theta = math.copysign(np.linalg.norm(cross_product), cross_product[2])
        # rot_angle = math.acos(cos_theta) if sin_theta>0 else 2*math.pi - math.acos(cos_theta)
        rot_matrix = np.array([[cos_theta,-sin_theta,0],[sin_theta,cos_theta,0],[0,0,1]])
        
        self.orientate_matrix = rot_matrix
        self.translate_vector = np.matmul( self.orientate_matrix.T, external_pt2) - internal_pt2 - self.implement_offset
        self.scale = 1 # (space_mag / robot_mag)
        
        print(f'Orientate matrix:\n{self.orientate_matrix}')
        print(f'Translate vector: {self.translate_vector}')
        print(f'Scale factor: {self.scale}\n')
        return
    
    def connect(self):
        """Establish connection with device"""
        return self._connect(**self.connection_details)
    
    def getConfigSettings(self, attributes:list[str]) -> dict:
        """
        Retrieve the robot's configuration
        
        Args:
            attributes (list[str]): list of attributes to retrieve values from
        
        Returns:
            dict: dictionary of robot class and configuration
        """
        _class = str(type(self)).split("'")[1].split('.')[1]
        # settings = {k: v for k,v in self.__dict__.items() if k in attributes}
        settings = {key: self.__dict__.get(key) for key in attributes}
        for k,v in settings.items():
            if type(v) == tuple:
                settings[k] = {"tuple": list(v)}
            elif type(v) == np.ndarray:
                settings[k] = {"array": v.tolist()}
        return {"class": _class, "settings": settings}

    def isBusy(self) -> bool:
        """
        Checks and returns whether the device is busy
        
        Returns:
            bool: whether the device is busy
        """
        return self.flags.get('busy', False)
    
    def isConnected(self) -> bool:
        """
        Checks and returns whether the device is connected

        Returns:
            bool: whether the device is connected
        """
        if not self.flags.get('connected', False):
            print(f"{self.__class__} is not connected. Details: {self.connection_details}")
        return self.flags.get('connected', False)
 
    def loadDeck(self, layout_file:str|None = None, layout_dict:dict|None = None, **kwargs):
        """
        Load Labware objects onto the deck from file or dictionary
        
        Args:
            layout_file (str|None, optional): filename of layout .json file. Defaults to None.
            layout_dict (dict|None, optional): dictionary of layout. Defaults to None.
        """
        self.deck.loadLayout(layout_file=layout_file, layout_dict=layout_dict, **kwargs)
        return
    
    def move(self, axis:str, value:float, speed_factor:float|None = None, **kwargs) -> bool:
        """
        Move the robot in a specific axis by a specific value

        Args:
            axis (str): axis to move in (x,y,z,a,b,c,j1,j2,j3,j4,j5,j6)
            value (float): value to move by, in mm (translation) or degree (rotation)
            speed (float|None, optional): speed factor of travel. Defaults to None.

        Returns:
            bool: whether movement is successful
        """
        axis = axis.lower()
        movement_L = ('x','y','z','a','b','c')
        movement_J = ('j1','j2','j3','j4','j5','j6')
        success = False
        speed_factor = self.speed_factor if speed_factor is None else speed_factor
        speed_factor = 1 if speed_factor == 0 else speed_factor
        if axis in movement_L:
            values = {m:0 for m in movement_L}
            values[axis] = value
            vector = (values['x'], values['y'], values['z'])
            angles = (values['a'], values['b'], values['c'])
            success = self.moveBy(vector=vector, angles=angles, speed_factor=speed_factor, **kwargs)
        elif axis in movement_J:
            values = {m:0 for m in movement_J}
            values[axis] = value
            angles1 = (values['j1'], values['j2'], values['j3'])
            angles2 = (values['j4'], values['j5'], values['j6'])
            angles = angles1 + angles2
            success = self.moveBy(angles=angles, speed_factor=speed_factor, **kwargs)
        return success
              
    def resetFlags(self):
        """Reset all flags to class attribute `_default_flags`"""
        self.flags = self._default_flags.copy()
        return
    
    def safeMoveTo(self, 
        coordinates: tuple[float]|None = None, 
        orientation: tuple[float]|None = None, 
        tool_offset: bool = True, 
        travel_speed_ratio: float|None = None,
        ascent_speed_ratio: float|None = None, 
        descent_speed_ratio: float|None = None, 
        **kwargs
    ) -> bool:
        """
        Safe version of moveTo by moving in Z-axis first

        Args:
            coordinates (tuple[float]|None, optional): x,y,z coordinates to move to. Defaults to None.
            orientation (tuple[float]|None, optional): a,b,c orientation to move to. Defaults to None.
            tool_offset (bool, optional): whether to consider tooltip offset. Defaults to True.
            travel_speed_ratio (float|None, optional): speed ratio of lateral travel. Defaults to None.
            ascent_speed_ratio (float|None, optional): speed ratio of ascent. Defaults to None.
            descent_speed_ratio (float|None, optional): speed ratio of descent. Defaults to None.
            
        Returns:
            bool: whether movement is successful
        """
        ascent_speed_ratio = self.speed_factor if ascent_speed_ratio is None else ascent_speed_ratio
        descent_speed_ratio = self.speed_factor if descent_speed_ratio is None else descent_speed_ratio
        travel_speed_ratio = self.speed_factor if travel_speed_ratio is None else travel_speed_ratio
        success = []
        if coordinates is None:
            coordinates = self.tool_position if tool_offset else self.user_position
        if orientation is None:
            orientation = self.orientation
        coordinates = np.array(coordinates)
        orientation = np.array(orientation)
        
        # Move to safe height
        safe_height = self.home_coordinates[2] if 'safe' not in self.heights else self.heights['safe']
        ret = self.move('z', max(0, safe_height-self.coordinates[2]), speed_factor=ascent_speed_ratio)
        success.append(ret)
        
        # Move to correct XY-position
        intermediate_position = self.tool_position if tool_offset else self.user_position
        ret = self.moveTo(
            coordinates = [*coordinates[:2],float(intermediate_position[0][2])], 
            orientation = orientation, 
            tool_offset = tool_offset,
            speed_factor = travel_speed_ratio
        )
        success.append(ret)
        
        # Move down to target height
        ret = self.moveTo(
            coordinates = coordinates,
            orientation = orientation, 
            tool_offset = tool_offset,
            speed_factor = descent_speed_ratio
        )
        success.append(ret)
        return all(success)
        
    def setFlag(self, **kwargs):
        """
        Set flags by using keyword arguments

        Kwargs:
            key, value: (flag name, boolean) pairs
        """
        if not all([type(v)==bool for v in kwargs.values()]):
            print(kwargs)
            # raise ValueError("Ensure all assigned flag values are boolean.")
        self.flags.update(kwargs)
        return
    
    def setHeight(self, overwrite:bool = False, **kwargs):
        """
        Set predefined heights using keyword arguments

        Args:
            overwrite (bool, optional): whether to overwrite existing height. Defaults to False.
        
        Kwargs:
            key, value: (height name, float value) pairs
        
        Raises:
            ValueError: Ensure all assigned height values are floating point numbers.
        """
        for k,v in kwargs.items():
            kwargs[k] = float(v) if type(v) is int else v
        if not all([type(v)==float for v in kwargs.values()]):
            raise ValueError("Ensure all assigned height values are floating point numbers.")
        for key, value in kwargs.items():
            if key not in self.heights or overwrite:
                self.heights[key] = value
            elif not overwrite:
                print(f"Previously saved height '{key}': {self.heights[key]}\n")
                print(f"New height received: {value}")
                if input('Overwrite? [y/n]').lower() == 'n':
                    continue
                self.heights[key] = value
        return
    
    def setImplementOffset(self, implement_offset:tuple[float], home:bool = True):
        """
        Set offset of attached implement, then home if desired

        Args:
            implement_offset (tuple[float]): x,y,z offset of implement (i.e. vector pointing from end effector to tool tip)
            home (bool, optional): whether to home after setting implement offset. Defaults to True.
        """
        self.implement_offset = implement_offset
        if home:
            self.home()
        return
    
    def updatePosition(self, 
        coordinates: tuple[float]|None = None, 
        orientation: tuple[float]|None = None, 
        vector: tuple = (0,0,0), 
        angles: tuple = (0,0,0)
    ):
        """
        Update atributes to current position

        Args:
            coordinates (tuple[float]|None, optional): x,y,z coordinates. Defaults to None.
            orientation (tuple[float]|None, optional): a,b,c angles. Defaults to None.
            vector (tuple, optional): x,y,z vector. Defaults to (0,0,0).
            angles (tuple, optional): a,b,c angles. Defaults to (0,0,0).
        """
        if coordinates is not None:
            self.coordinates = coordinates
        else:
            self.coordinates = self.coordinates + np.array(vector)
            
        if orientation is not None:
            self.orientation = orientation
        else:
            self.orientation = self.orientation + np.array(angles)
        
        print(f'{self.coordinates}, {self.orientation}')
        return

    # Protected method(s)
    def _calculate_travel_time(self, 
        distance: float, 
        speed: float, 
        acceleration: float|None = None,
        deceleration: float|None = None
    ) -> float:
        """
        Calculate the travel time of motion

        Args:
            distance (float): distance (linear or angular) travelled
            speed (float): speed (linear or angular) of motion
            acceleration (float|None, optional): acceleration from target speed. Defaults to None.
            deceleration (float|None, optional): deceleration from target speed. Defaults to None.

        Returns:
            float: travel time in seconds
        """
        travel_time = 0
        speed2 = speed*speed
        accel_distance = 0 if not acceleration else speed2 / (2*acceleration)
        decel_distance = 0 if not deceleration else speed2 / (2*deceleration)
        ramp_distance = accel_distance + decel_distance
        if ramp_distance <= distance:
            travel_time = (distance - ramp_distance) / speed
            accel_time = 0 if not acceleration else speed / acceleration
            decel_time = 0 if not deceleration else speed / deceleration
            travel_time += (accel_time + decel_time)
            # print('more time')
        else:
            time2 = (2*distance)* (acceleration + deceleration)/(acceleration*deceleration)
            travel_time = time2**0.5
            # print('less time')
        travel_time = 0.0 if np.isnan(travel_time) else travel_time
        return travel_time
    
    def _diagnostic(self):
        """Run diagnostic test"""
        self.home()
        return
    
    def _get_move_wait_time(self, 
        distances: np.ndarray, 
        speeds: np.ndarray, 
        accels: np.ndarray|None = None
    ) -> float:
        """
        Get the amount of time to wait to complete movement

        Args:
            distances (np.ndarray): array of distances to travel
            speeds (np.ndarray): array of axis speeds
            accels (np.ndarray|None, optional): array of axis accelerations. Defaults to None.

        Returns:
            float: wait time to complete travel
        """
        accels = np.zeros(len(speeds)) if accels is None else accels
        times = [self._calculate_travel_time(d,s,a,a) for d,s,a in zip(distances, speeds, accels)]
        move_time = max(times[:2]) + times[2]
        if self.verbose:
            print(f'distances: {distances}')
            print(f'speeds: {speeds}')
            print(f'accels: {accels}')
            print(f'times: {times}')
        return move_time

    def _transform_in(self, 
        coordinates: tuple[float]|None = None, 
        vector: tuple[float]|None = None, 
        stretch: bool = False, 
        tool_offset: bool = False
    ) -> tuple[float]:
        """
        Order of transformations (scale, rotate, translate)

        Args:
            coordinates (tuple[float]|None, optional): position coordinates. Defaults to None.
            vector (tuple[float]|None, optional): vector. Defaults to None.
            stretch (bool, optional): whether to scale. Defaults to False.
            tool_offset (bool, optional): whether to consider tooltip offset. Defaults to False.

        Raises:
            RuntimeError: Only one of 'coordinates' or 'vector' can be passed
            
        Returns:
            tuple[float]: converted robot vector
        """
        to_be_transformed = None
        if coordinates is None and vector is not None:
            translate = np.zeros(3)
            to_be_transformed = vector
        elif coordinates is not None and vector is None:
            translate = (-1*self.translate_vector)
            translate = translate - self.implement_offset if tool_offset else translate
            to_be_transformed = coordinates
        else:
            raise RuntimeError("Input only either 'coordinates' or 'vector'.")
        scale = (1/self.scale) if stretch else 1
        return tuple( translate + np.matmul(self.orientate_matrix.T, scale * np.array(to_be_transformed)) )

    def _transform_out(self, 
        coordinates: tuple[float]|None = None, 
        vector: tuple[float]|None = None, 
        stretch: bool = False, 
        tool_offset: bool = False
    ) -> tuple[float]:
        """
        Order of transformations (translate, rotate, scale)

        Args:
            coordinates (tuple, optional): position coordinates. Defaults to None.
            vector (tuple, optional): vector. Defaults to None.
            stretch (bool, optional): whether to scale. Defaults to True.
            tool_offset (bool, optional): whether to consider tooltip offset. Defaults to False.

        Raises:
            RuntimeError: Only one of 'coordinates' or 'vector' can be passed
            
        Returns:
            tuple[float]: converted workspace vector
        """
        to_be_transformed = None
        if coordinates is None and vector is not None:
            translate = np.zeros(3)
            to_be_transformed = vector
        elif coordinates is not None and vector is None:
            translate = self.translate_vector
            translate = translate + self.implement_offset if tool_offset else translate
            to_be_transformed = coordinates
        else:
            raise RuntimeError("Input only either 'coordinates' or 'vector'.")
        scale = self.scale if stretch else 1
        return tuple( scale * np.matmul(self.orientate_matrix, translate + np.array(to_be_transformed)) )


    ### NOTE: DEPRECATE
    def getPosition(self):
        """
        Get robot coordinates and orientation.
        
        TO BE DEPRECATED: Use `position` attribute instead.
        
        Returns:
            tuple, tuple: x,y,z coordinates; a,b,c angles
        """
        print("`getPosition()` to be deprecated. Use `position` attribute instead.")
        return self.position
    
    def getToolPosition(self):
        """
        Retrieve coordinates of tool tip/end of implement.
        
        TO BE DEPRECATED: Use `tool_position` attribute instead.

        Returns:
            tuple, tuple: x,y,z coordinates; a,b,c angles
        """
        print("`getToolPosition()` to be deprecated. Use `tool_position` attribute instead.")
        return self.tool_position
    
    def getUserPosition(self):
        """
        Retrieve user-defined workspace coordinates.
        
        TO BE DEPRECATED: Use `user_position` attribute instead.

        Returns:
            tuple, tuple: x,y,z coordinates; a,b,c angles
        """
        print("`getUserPosition()` to be deprecated. Use `user_position` attribute instead.")
        return self.user_position
    
    def getWorkspacePosition(self):
        """
        Alias for getUserPosition.
        
        TO BE DEPRECATED: Use `workspace_position` attribute instead.

        Returns:
            tuple, tuple: x,y,z coordinates; a,b,c angles
        """
        print("`getWorkspacePosition()` to be deprecated. Use `workspace_position` attribute instead.")
        return self.workspace_position
