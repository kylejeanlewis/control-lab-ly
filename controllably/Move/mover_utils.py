# %% -*- coding: utf-8 -*-
"""
Created: Tue 2022/12/26 17:13:35
@author: Chang Jie

Notes / actionables:
- 
"""
# Standard library imports
import math
import numpy as np

# Local application imports
print(f"Import: OK <{__name__}>")

class Mover(object):
    """
    General mover class

    Kwargs:
        home_coordinates (tuple, optional): position to home in arm coordinates. Defaults to (0,0,0).
        home_orientation (tuple, optional): orientation to home. Defaults to (0,0,0).
        orientate_matrix (numpy.matrix, optional): matrix to transform arm axes to workspace axes. Defaults to np.identity(3).
        translate_vector (numpy.ndarray, optional): vector to transform arm position to workspace position. Defaults to (0,0,0).
        implement_offset (tuple, optional): implement offset vector pointing from end of effector to tool tip. Defaults to (0,0,0).
        scale (int, optional): scale factor to transform arm scale to workspace scale. Defaults to 1.
        verbose (bool, optional): whether to print outputs. Defaults to False.
    """
    max_actions = 0
    def __init__(self, **kwargs):
        self._coordinates = (0,0,0)
        self._orientation = (0,0,0)
        self._home_coordinates = (0,0,0)
        self._home_orientation = (0,0,0)
        self._orientate_matrix = np.identity(3)
        self._translate_vector = (0,0,0)
        self._implement_offset = (0,0,0)
        self._scale = 1
        self._speed = 1
        self._speed_fraction = 1

        self.verbose = False
        self._flags = {}
        self.heights = {}
        
        self.setConfigSettings(kwargs)
        return
    
    def __delete__(self):
        self._shutdown()
        return
    
    @property
    def coordinates(self):
        return np.array(self._coordinates)
    @coordinates.setter
    def coordinates(self, value):
        if len(value) != 3:
            raise Exception('Please input x,y,z coordinates')
        self._coordinates = tuple(value)
        return
    
    @property
    def orientation(self):
        return np.array(self._orientation)
    @orientation.setter
    def orientation(self, value):
        if len(value) != 3:
            raise Exception('Please input a,b,c angles')
        self._orientation = tuple(value)
        return
       
    @property
    def home_coordinates(self):
        return np.array(self._home_coordinates)
    @home_coordinates.setter
    def home_coordinates(self, value):
        if len(value) != 3:
            raise Exception('Please input x,y,z coordinates')
        self._home_coordinates = tuple(value)
        return
    
    @property
    def home_orientation(self):
        return np.array(self._home_orientation)
    @home_orientation.setter
    def home_orientation(self, value):
        if len(value) != 3:
            raise Exception('Please input a,b,c angles')
        self._home_orientation = tuple(value)
        return
    
    @property
    def orientate_matrix(self):
        return self._orientate_matrix
    @orientate_matrix.setter
    def orientate_matrix(self, value):
        if len(value) != 3 or any([len(row)!=3 for row in value]):
            raise Exception('Please input 3x3 matrix')
        self._orientate_matrix = np.array(value)
        return
    
    @property
    def translate_vector(self):
        return np.array(self._translate_vector)
    @translate_vector.setter
    def translate_vector(self, value):
        if len(value) != 3:
            raise Exception('Please input x,y,z vector')
        self._translate_vector = tuple(value)
        return
    
    @property
    def implement_offset(self):
        return np.array(self._implement_offset)
    @implement_offset.setter
    def implement_offset(self, value):
        if len(value) != 3:
            raise Exception('Please input x,y,z offset')
        self._implement_offset = tuple(value)
        return
    
    @property
    def position(self):
        return self.coordinates, self.orientation
    
    @property
    def scale(self):
        return self._scale
    @scale.setter
    def scale(self, value):
        if value <= 0:
            raise Exception('Please input a positive scale factor')
        self._scale = float(value)
        return
    
    @property
    def speed(self):
        print(f'Speed fraction: {self._speed_fraction}')
        return self._speed * self._speed_fraction
    
    def _diagnostic(self):
        """
        Run diagnostic on tool
        """
        self.home()
        return
    
    def _shutdown(self):
        """
        Close serial connection and shutdown
        """
        return
    
    def _transform_in(self, coordinates=None, vector=None, stretch=False, tool_offset=False):
        """
        Order of transformations (scale, rotate, translate).

        Args:
            coordinates (tuple, optional): position coordinates. Defaults to None.
            vector (tuple, optional): vector. Defaults to None.
            stretch (bool, optional): whether to scale. Defaults to True.
            tool_offset (bool, optional): whether to consider tooltip offset. Defaults to False.

        Raises:
            Exception: Only one of 'coordinates' or 'vector' can be passed
            
        Returns:
            tuple: converted robot vector
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
            raise Exception("Input only either 'coordinates' or 'vector'.")
        scale = (1/self.scale) if stretch else 1
        return tuple( translate + np.matmul(self.orientate_matrix.T, scale * np.array(to_be_transformed)) )

    def _transform_out(self, coordinates=None, vector=None, stretch=False, tool_offset=False):
        """
        Order of transformations (translate, rotate, scale).

        Args:
            coordinates (tuple, optional): position coordinates. Defaults to None.
            vector (tuple, optional): vector. Defaults to None.
            stretch (bool, optional): whether to scale. Defaults to True.
            tool_offset (bool, optional): whether to consider tooltip offset. Defaults to False.

        Raises:
            Exception: Only one of 'coordinates' or 'vector' can be passed
            
        Returns:
            tuple: converted workspace vector
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
            raise Exception("Input only either 'coordinates' or 'vector'.")
        scale = self.scale if stretch else 1
        return tuple( scale * np.matmul(self.orientate_matrix, translate + np.array(to_be_transformed)) )

    def calibrate(self, external_pt1:np.ndarray, internal_pt1:np.ndarray, external_pt2:np.ndarray, internal_pt2:np.ndarray):
        """
        Calibrate internal and external coordinate systems.

        Args:
            external_pt1 (numpy.ndarray): x,y,z coordinates of physical point 1
            internal_pt1 (numpy.ndarray): x,y,z coordinates of robot point 1
            external_pt2 (numpy.ndarray): x,y,z coordinates of physical point 2
            internal_pt2 (numpy.ndarray): x,y,z coordinates of robot point 2
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
    
    def getConfigSettings(self, attributes:list):
        """
        Read the robot configuration settings
        
        Args:
            attributes (list): list of attributes to retrieve values from
        
        Returns:
            dict: dictionary of robot class and settings
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

    def getPosition(self):
        """
        Get robot coordinates and orientation.
        
        Returns:
            tuple, tuple: x,y,z coordinates; a,b,c angles
        """
        return self.position
    
    def getToolPosition(self):
        """
        Retrieve coordinates of tool tip/end of implement.

        Returns:
            tuple, tuple: x,y,z coordinates; a,b,c angles
        """
        coordinates, orientation = self.getPosition()
        return self._transform_out(coordinates=coordinates, tool_offset=True), orientation
    
    def getUserPosition(self):
        """
        Retrieve user-defined workspace coordinates.

        Returns:
            tuple, tuple: x,y,z coordinates; a,b,c angles
        """
        coordinates, orientation = self.getPosition()
        return self._transform_out(coordinates=coordinates, tool_offset=False), orientation
    
    def getWorkspacePosition(self):
        """
        Alias for getUserPosition

        Returns:
            tuple, tuple: x,y,z coordinates; a,b,c angles
        """
        return self.getUserPosition()
   
    def home(self):
        """
        Home the mover
        """
        return True
    
    def isFeasible(self, coordinates, transform=False, tool_offset=False, **kwargs):
        """
        Checks if specified coordinates is a feasible position for robot to access

        Args:
            coordinates (tuple): x,y,z coordinates
            transform (bool, optional): whether to transform the coordinates. Defaults to False.
            tool_offset (bool, optional): whether to consider tooltip offset. Defaults to False.

        Returns:
            bool: whether coordinates is a feasible position
        """
        return True
    
    def move(self, axis:str, value, speed_fraction=1, **kwargs):
        """
        Move robot along axis by specified value

        Args:
            axis (str): axis to move in (x,y,z,a,b,c,j1,j2,j3,j4,j5,j6)
            value (int, or float): value to move by, in mm (translation) or degree (rotation)
            speed_fraction (int, optional): fraction of full speed. Defaults to 1.

        Returns:
            bool: whether movement is successful
        """
        success = False
        speed_change = False
        if 0 < speed_fraction < 1:
            speed_change = True
            self.setSpeed(int(max(1, speed_fraction*100)))      # change speed here
        axis = axis.lower()
        movement_L = {
            'x':0, 'y':0, 'z':0,
            'a':0, 'b':0, 'c':0,
        }
        movement_J = {
            'j1':0, 'j2':0, 'j3':0,
            'j4':0, 'j5':0, 'j6':0,
        }
        if axis in movement_L.keys():
            movement_L[axis] = value
            vector = (movement_L['x'], movement_L['y'], movement_L['z'])
            angles = (movement_L['a'], movement_L['b'], movement_L['c'])
            success = self.moveBy(vector=vector, angles=angles, **kwargs)
        elif axis in movement_J.keys():
            movement_J[axis] = value
            angles1 = (movement_J['j1'], movement_J['j2'], movement_J['j3'])
            angles2 = (movement_J['j4'], movement_J['j5'], movement_J['j6'])
            angles = angles1 + angles2
            success = self.moveBy(angles=angles, **kwargs)
        if speed_change:
            self.setSpeed(self.speed)                           # change speed back here
        return success
    
    def moveBy(self, vector=None, angles=None, **kwargs):
        """
        Move robot by specified vector and angles

        Args:
            vector (tuple, optional): x,y,z vector to move in. Defaults to None.
            angles (tuple, optional): a,b,c angles to move in. Defaults to None.

        Returns:
            bool: whether movement is successful
        """
        if vector is None:
            vector = (0,0,0)
        if angles is None:
            angles = (0,0,0)
        vector = np.array(vector)
        angles = np.array(angles)
        user_position = self.getUserPosition()
        new_coordinates = np.round( user_position[0] + np.array(vector) , 2)
        new_orientation = np.round( user_position[1] + np.array(angles) , 2)
        return self.moveTo(coordinates=new_coordinates, orientation=new_orientation, tool_offset=False, **kwargs)
    
    def moveTo(self, coordinates=None, orientation=None, tool_offset=True, **kwargs):
        """
        Move robot to specified coordinates and orientation

        Args:
            coordinates (tuple, optional): x,y,z coordinates to move to. Defaults to None.
            orientation (tuple, optional): a,b,c orientation to move to. Defaults to None.
            tool_offset (bool, optional): whether to consider tooltip offset. Defaults to True.

        Returns:
            bool: whether movement is successful
        """
        if coordinates is None:
            coordinates = self.getToolPosition() if tool_offset else self.getUserPosition()
        if orientation is None:
            orientation = self.orientation
        coordinates = self._transform_in(coordinates=coordinates, tool_offset=tool_offset)
        coordinates = np.array(coordinates)
        orientation = np.array(orientation)
        
        if not self.isFeasible(coordinates):
            return False
        self.coordinates = coordinates
        self.orientation = orientation
        return True
    
    def reset(self):
        """
        Clear any errors and enable robot
        """
        return
    
    def safeMoveTo(self, coordinates=None, orientation=None, tool_offset=True, ascent_speed_fraction=1, descent_speed_fraction=1, **kwargs):
        """
        Safe version of moveTo by moving in Z-axis first

        Args:
            coordinates (tuple, optional): x,y,z coordinates to move to. Defaults to None.
            orientation (tuple, optional): a,b,c orientation to move to. Defaults to None.
            tool_offset (bool, optional): whether to consider tooltip offset. Defaults to True.
            descent_speed_fraction (int, optional): _description_. Defaults to 1.
            
        Returns:
            bool: whether movement is successful
        """
        if coordinates is None:
            coordinates = self.getToolPosition() if tool_offset else self.getUserPosition()
        if orientation is None:
            orientation = self.orientation
        coordinates = np.array(coordinates)
        orientation = np.array(orientation)
        
        self.move('z', max(0, self.home_coordinates[2]-self.coordinates[2]), speed_fraction=ascent_speed_fraction)
        intermediate_position = self.getToolPosition() if tool_offset else self.getUserPosition()
        self.moveTo(
            coordinates=list(coordinates[:2])+[float(intermediate_position[0][2])], 
            orientation=orientation, 
            tool_offset=tool_offset
        )
        if 0 < descent_speed_fraction < 1:
            self.setSpeed(int(max(1, descent_speed_fraction*100)))      # change speed here
        self.moveTo(
            coordinates=coordinates,
            orientation=orientation, 
            tool_offset=tool_offset
        )
        self.setSpeed(self.speed)                                       # change speed back here
        return
    
    def setConfigSettings(self, config:dict):
        """
        Set configuration settings.
        
        Args:
            config (dict): dictionary of attribute names and values
        """
        for k,v in config.items():
            if k in dir(self):
                self.__setattr__(k,v)
            else:
                print(f"'{k}' is not an attribute of {self.__class__}")
        return
    
    def setFlag(self, name:str, value:bool):
        """
        Set a flag truth value

        Args:
            name (str): label
            value (bool): flag value
        """
        self._flags[name] = value
        return
    
    def setHeight(self, name:str, value, overwrite=False):
        """
        Set predefined height

        Args:
            name (str): label
            value (int, or float): height value
            overwrite (bool, optional): whether to overwrite existing height. Defaults to False.
        
        Raises:
            Exception: Height with the same name has already been defined
        """
        if name not in self.heights.keys() or overwrite:
            self.heights[name] = value
        else:
            raise Exception(f"The height '{name}' has already been defined at: {self.heights[name]}")
        return
    
    def setImplementOffset(self, implement_offset, home=True):
        """
        Set offset of implement, then home

        Args:
            implement_offset (tuple): x,y,z offset of implement (i.e. vector pointing from end of effector to tooltip)
            home (bool, optional): whether to home after setting implement offset. Defaults to True
        """
        self.implement_offset = implement_offset
        if home:
            self.home()
        return
    
    def setSpeed(self, speed:int):
        """
        Setting the movement speed rate.

        Args:
            speed (int): rate value (value range: 1~100)
        """
        return True

    def switchFlag(self, name:str):
        """
        Switch a flag truth value

        Args:
            name (str): label
        """
        self._flags[name] = not self._flags[name]
        return
    
    def updatePosition(self, coordinates=None, orientation=None, vector=(0,0,0), angles=(0,0,0)):
        """
        Update to current position

        Args:
            coordinates (tuple, optional): x,y,z coordinates. Defaults to None.
            orientation (tuple, optional): a,b,c angles. Defaults to None.
            vector (tuple, optional): x,y,z vector. Defaults to (0,0,0).
            angles (tuple, optional): a,b,c angles. Defaults to (0,0,0).
        """
        if coordinates is not None:
            self.coordinates = coordinates
        else:
            self.coordinates = np.array(self.coordinates) + np.array(vector)
            
        if orientation is not None:
            self.orientation = orientation
        else:
            self.orientation = np.array(self.orientation) + np.array(angles)
        
        print(f'{self.coordinates}, {self.orientation}')
        return
