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

# Third party imports
import serial # pip install pyserial
import serial.tools.list_ports

# Local application imports
print(f"Import: OK <{__name__}>")

SCALE = True
MOVE_TIME = 0.5

class RobotArm(object):
    def __init__(self, home_position=(0,0,0), home_orientation=(0,0,0), orientate_matrix=np.identity(3), translate_vector=np.zeros(3), scale=1, **kwargs):
        self.home_position = home_position
        self.home_orientation = home_orientation
        self.orientate_matrix = orientate_matrix
        self.translate_vector = translate_vector
        self.scale = scale
        self.implement_offset = (0,0,0)
        
        self.current_x = 0
        self.current_y = 0
        self.current_z = 0
        self.coordinates = (self.current_x, self.current_y, self.current_z)
        self.orientation = (0,0,0)
        pass
    
    def __delete__(self):
        self._shutdown()
        return
    
    def _connect(self, *args, **kwargs):
        """EMPTY METHOD"""
        print(f"'{self.__class__.__name__}' class has no method '_freeze'")
        return
    
    def _freeze(self, *args, **kwargs):
        """EMPTY METHOD"""
        print(f"'{self.__class__.__name__}' class has no method '_freeze'")
        return
    
    def _shutdown(self, *args, **kwargs):
        """EMPTY METHOD"""
        print(f"'{self.__class__.__name__}' class has no method '_shutdown'")
        return
    
    def _transform_vector_in(self, coord, offset=False, stretch=SCALE):
        """
        Order of transformations (scale, rotate, translate).

        Args:
            coord (tuple): vector
            offset (bool, optional): whether to translate. Defaults to False.
            stretch (bool, optional): whether to scale. Defaults to SCALE.

        Returns:
            tuple: converted arm vector
        """
        translate = (-1*self.translate_vector) if offset else np.zeros(3)
        scale = (1/self.scale) if stretch else 1
        return tuple( translate + np.matmul(self.orientate_matrix.T, scale * np.array(coord)) )

    def _transform_vector_out(self, coord, offset=False, stretch=SCALE):
        """
        Order of transformations (translate, rotate, scale).

        Args:
            coord (tuple): vector
            offset (bool, optional): whether to translate. Defaults to False.
            stretch (bool, optional): whether to scale. Defaults to SCALE.

        Returns:
            tuple: converted workspace vector
        """
        translate = self.translate_vector if offset else np.zeros(3)
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
        
        print(f'Address: {self.address}')
        print(f'Orientate matrix:\n{self.orientate_matrix}')
        print(f'Translate vector: {self.translate_vector}')
        print(f'Scale factor: {self.scale}')
        print(f'Offset angle: {rot_angle/math.pi*180} degree')
        print(f'Offset vector: {(external_pt1 - internal_pt1)}')
        
        return
    
    def getOrientation(self):
        """Read the current position and orientation of arm."""
        return self.orientation

    def getPosition(self):
        """Read the current position and orientation of arm."""
        return self.coordinates
    
    def getWorkspacePosition(self, offset=True):
        """
        Retrieve physcial coordinates.

        Args:
            offset (bool, optional): whether to consider offset of implement. Defaults to True.

        Returns:
            tuple: position vector
        """
        return self._transform_vector_out(self.getPosition(), offset=offset)
    
    def tuck(self, *args, **kwargs):
        """EMPTY METHOD"""
        print(f"'{self.__class__.__name__}' class has no method '_tuck'")
        return