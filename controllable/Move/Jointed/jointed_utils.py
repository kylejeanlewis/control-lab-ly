# %% -*- coding: utf-8 -*-
"""
Created: Tue 2022/11/01 17:13:35
@author: Chang Jie

Notes / actionables:
-
"""
# Standard library imports
import math
import numpy as np

# Local application imports
from .. import Mover
print(f"Import: OK <{__name__}>")

class RobotArm(Mover):
    """
    RobotArm class.

    Args:
        home_position (tuple, optional): position to home in arm coordinates. Defaults to (0,0,0).
        home_orientation (tuple, optional): orientation to home. Defaults to (0,0,0).
        orientate_matrix (numpy.matrix, optional): matrix to transform arm axes to workspace axes. Defaults to np.identity(3).
        translate_vector (numpy.array, optional): vector to transform arm position to workspace position. Defaults to np.zeros(3).
        scale (int, optional): scale factor to transform arm scale to workspace scale. Defaults to 1.
        implement_offset (tuple, optional): implement offset vector pointing from end of effector to tool tip. Defaults to (0,0,0).
        verbose (bool, optional): whether to print outputs. Defaults to False.
    """
    def __init__(self, home_position=(0,0,0), home_orientation=(0,0,0), orientate_matrix=np.identity(3), translate_vector=np.zeros(3), scale=1, implement_offset=(0,0,0), verbose=False, **kwargs):
        self.home_position = home_position
        self.home_orientation = home_orientation
        self.orientate_matrix = orientate_matrix
        self.translate_vector = translate_vector
        self.scale = scale
        
        self.implement_offset = implement_offset
        self.coordinates = (0,0,0)
        self.orientation = (0,0,0)
        
        self.verbose = verbose
        self._flags = {}
        pass
    
    def __delete__(self):
        self._shutdown()
        return
      
    def _transform_vector_in(self, coord, offset=False, stretch=True, tool=False):
        """
        Order of transformations (scale, rotate, translate).

        Args:
            coord (tuple): vector
            offset (bool, optional): whether to translate. Defaults to False.
            stretch (bool, optional): whether to scale. Defaults to True.
            tool (bool, optional): whether to consider tooltip offset. Defaults to False.

        Returns:
            tuple: converted arm vector
        """
        translate = (-1*self.translate_vector) if offset else np.zeros(3)
        translate = translate - self.implement_offset if tool else translate
        scale = (1/self.scale) if stretch else 1
        return tuple( translate + np.matmul(self.orientate_matrix.T, scale * np.array(coord)) )

    def _transform_vector_out(self, coord, offset=False, stretch=True, tool=False):
        """
        Order of transformations (translate, rotate, scale).

        Args:
            coord (tuple): vector
            offset (bool, optional): whether to translate. Defaults to False.
            stretch (bool, optional): whether to scale. Defaults to True.
            tool (bool, optional): whether to consider tooltip offset. Defaults to False.

        Returns:
            tuple: converted workspace vector
        """
        translate = self.translate_vector if offset else np.zeros(3)
        translate = translate + self.implement_offset if tool else translate
        scale = self.scale if stretch else 1
        return tuple( scale * np.matmul(self.orientate_matrix, translate + np.array(coord)) )

    def calibrate(self, external_pt1, internal_pt1, external_pt2, internal_pt2):
        """
        Calibrate internal and external coordinate systems.

        Args:
            external_pt1 (tuple): x,y,z coordinates of physical point 1
            internal_pt1 (tuple): x,y,z coordinates of robot point 1
            external_pt2 (tuple): x,y,z coordinates of physical point 2
            internal_pt2 (tuple): x,y,z coordinates of robot point 2
        """
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
        rot_angle = math.acos(cos_theta) if sin_theta>0 else 2*math.pi - math.acos(cos_theta)
        rot_matrix = np.array([[cos_theta,-sin_theta,0],[sin_theta,cos_theta,0],[0,0,1]])
        
        self.orientate_matrix = rot_matrix
        self.translate_vector = (external_pt1 - internal_pt1)
        self.scale = (space_mag / robot_mag)
        
        print(f'Orientate matrix:\n{self.orientate_matrix}')
        print(f'Translate vector: {self.translate_vector}')
        print(f'Scale factor: {self.scale}')
        print(f'Offset angle: {rot_angle/math.pi*180} degree')
        print(f'Offset vector: {(external_pt1 - internal_pt1)}')
        return
    
    def getConfigSettings(self, params:list):
        """
        Read the arm configuration settings.
        
        Args:
            params (list): list of attributes to retrieve values from
        
        Returns:
            dict: dictionary of arm class and details/attributes
        """
        arm = str(type(self)).split("'")[1].split('.')[1]
        details = {k: v for k,v in self.__dict__.items() if k in params}
        for k,v in details.items():
            if type(v) == tuple:
                details[k] = {"tuple": list(v)}
            elif type(v) == np.ndarray:
                details[k] = {"array": v.tolist()}
        settings = {"arm": arm, "details": details}
        return settings

    def getPosition(self):
        """
        Read the current position and orientation of arm.
        
        Returns:
            tuple, tuple: x,y,z coordinates; a,b,g angles
        """
        return self.coordinates, self.orientation
    
    def getToolPosition(self):
        """
        Retrieve coordinates of tool tip/end of implement.

        Returns:
            tuple, tuple: x,y,z coordinates; a,b,g angles
        """
        coordinates, orientation = self.getPosition()
        return self._transform_vector_out(coordinates, offset=True, tool=True), orientation
    
    def getUserPosition(self):
        """
        Retrieve user-defined workspace coordinates.

        Returns:
            tuple, tuple: x,y,z coordinates; a,b,g angles
        """
        coordinates, orientation = self.getPosition()
        return self._transform_vector_out(coordinates, offset=True), orientation
    
    def getWorkspacePosition(self):
        """
        Alias for getUserPosition

        Returns:
            tuple, tuple: x,y,z coordinates; a,b,g angles
        """
        return self.getUserPosition()

    def setImplementOffset(self, implement_offset):
        """
        Set offset of implement.

        Args:
            implement_offset (tuple): x,y,z offset of implement (i.e. vector pointing from end of effector to tooltip)
        """
        self.implement_offset = tuple(implement_offset)
        self.home()
        return

    def setPosition(self, coord):
        """
        Set robot coordinates.

        Args:
            coord (tuple): x,y,z workspace coordinates
        """
        self.coordinates = self._transform_vector_in(coord, offset=True, stretch=True)
        return

    def updatePosition(self, coord=(0,), orientation=(0,), vector=(0,0,0), angles=(0,0,0)):
        """
        Update to current position

        Args:
            coord (tuple, optional): x,y,z coordinates. Defaults to (0,).
            orientation (tuple, optional): a,b,g angles. Defaults to (0,).
            vector (tuple, optional): x,y,z vector. Defaults to (0,0,0).
            angles (tuple, optional): a,b,g,angles. Defaults to (0,0,0).
        """
        if len(coord) == 1:
            new_coord = np.array(self.coordinates) + np.array(vector)
            self.coordinates = tuple(new_coord)
        else:
            self.coordinates = tuple(coord)
        
        if len(orientation) == 1:
            new_orientation = np.array(self.orientation) + np.array(angles)
            self.orientation = tuple(new_orientation)
        else:
            self.orientation = tuple(orientation)
        
        print(f'{self.coordinates}, {self.orientation}')
        return
