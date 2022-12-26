# %% -*- coding: utf-8 -*-
"""
Created: Tue 2022/11/01 17:13:35
@author: Chang Jie

Notes / actionables:
-
"""
# Standard library imports
import numpy as np

# Local application imports
from ..mover_utils import Mover
print(f"Import: OK <{__name__}>")

class RobotArm(Mover):
    """
    Robot arm controls
    
    Args:
        safe_height (float, optional): safe height. Defaults to None.

    Kwargs:
        home_coordinates (tuple, optional): position to home in arm coordinates. Defaults to (0,0,0).
        home_orientation (tuple, optional): orientation to home. Defaults to (0,0,0).
        orientate_matrix (numpy.matrix, optional): matrix to transform arm axes to workspace axes. Defaults to np.identity(3).
        translate_vector (numpy.ndarray, optional): vector to transform arm position to workspace position. Defaults to (0,0,0).
        implement_offset (tuple, optional): implement offset vector pointing from end of effector to tool tip. Defaults to (0,0,0).
        scale (int, optional): scale factor to transform arm scale to workspace scale. Defaults to 1.
        verbose (bool, optional): whether to print outputs. Defaults to False.
    """
    def __init__(self, safe_height=None, **kwargs):
        super().__init__(**kwargs)
        self.device = None
        
        if safe_height != None:
            self.setHeight('safe', safe_height)
        return
    
    def home(self, tool_offset=True):
        """
        Return the robot to home

        Args:
            tool_offset (bool, optional): whether to consider the offset of the tooltip. Defaults to True.
        """
        # Tuck arm in to avoid collision
        if self._flags['retract']:
            self.retractArm(self.home_coordinates)
        
        # Go to home position
        self.moveCoordTo(self.home_coordinates, self.home_orientation, tool_offset=tool_offset)
        print("Homed")
        return
    
    def moveBy(self, vector=None, angles=None, **kwargs):
        """
        Move robot by specified vector and angles

        Args:
            vector (tuple, optional): vector to move in. Defaults to None.
            angles (tuple, optional): angles to move in. Defaults to None.

        Returns:
            bool: whether movement is successful
        """
        if vector == None:
            vector = (0,0,0)
        if angles == None:
            angles = (0,0,0)
        vector = self._transform_vector_in(vector, offset=False)
        vector = np.array(vector)
        angles = np.array(angles)
        
        if len(angles) != 3:
            if len(angles) == 6:
                return self.moveJointBy(relative_angle=angles)
            return False
        return self.moveCoordBy(vector, angles)

    def moveTo(self, coordinates=None, orientation=None, retract=False, tool_offset=True, **kwargs):
        """
        Absolute Cartesian movement, using workspace coordinates.

        Args:
            coordinates (tuple, optional): coordinates to move to. Defaults to None.
            orientation (tuple, optional): orientation to move to. Defaults to None.
            retract (bool, optional): whether to tuck in arm before moving. Defaults to False.
            tool_offset (bool, optional): whether to consider tooltip offset. Defaults to True.
        
        Returns:
            bool: whether movement is successful
        """
        if coordinates == None:
            coordinates = self.getToolPosition() if tool_offset else self.getUserPosition()
        if orientation == None:
            orientation = self.orientation
        coordinates = self._transform_vector_in(coordinates=coordinates, offset=True, tool=tool_offset)
        coordinates = np.array(coordinates)
        orientation = np.array(orientation)
        
        if self._flags['retract'] and retract:
            self.retractArm(coordinates)
        
        if len(orientation) != 3:
            if len(orientation) == 6:
                return self.moveJointTo(absolute_angle=orientation)
            return False
        return self.moveCoordTo(coordinates, orientation, tool_offset)
    
    def moveCoordBy(self, vector=(0,0,0), angles=(0,0,0)):
        """
        Relative Cartesian movement and tool orientation, using robot coordinates.

        Args:
            vector (tuple, optional): displacement vector. Defaults to (0,0,0).
            angles (tuple, optional): rotation angles in degrees. Defaults to (0,0,0).
        """
        return True

    def moveCoordTo(self, coordinates, orientation=(0,), tool_offset=True):
        """
        Absolute Cartesian movement and tool orientation, using robot coordinates.

        Args:
            coordinates (tuple): position vector
            orientation (tuple, optional): orientation angles in degrees. Defaults to (0,).
            tool_offset (bool, optional): whether to consider implement offset. Defaults to True.
        """
        return True

    def moveJointBy(self, relative_angle=(0,0,0,0,0,0)):
        """
        Relative joint movement.

        Args:
            relative_angle (tuple, optional): rotation angles in degrees. Defaults to (0,0,0,0,0,0).
        """
        return True

    def moveJointTo(self, absolute_angle=(0,0,0,0,0,0)):
        """
        Absolute joint movement.

        Args:
            absolute_angle (tuple, optional): orientation angles in degrees. Defaults to (0,0,0,0,0,0).
        """
        return True
    
    def retractArm(self, target=None):
        """
        Tuck in arm, rotate about base, then extend again.

        Args:
            target (tuple, optional): x,y,z coordinates of destination. Defaults to None.
        """
        return
    
    def rotateBy(self, angles):
        """
        Relative effector rotation.

        Args:
            angles (tuple): rotation angles in degrees
        """
        angles = tuple(angles)
        angles = angles + (0,) * (3-len(angles))
        return self.moveJointBy((0,0,0,*angles))

    def rotateTo(self, orientation):
        """
        Absolute effector rotation.

        Args:
            orientation (tuple): orientation angles in degrees
        """
        return self.moveCoordTo(self.coordinates, orientation)
    
    def updatePosition(self, coordinates=None, orientation=None, vector=(0,0,0), angles=(0,0,0)):
        """
        Update to current position

        Args:
            coordinates (tuple, optional): x,y,z coordinates. Defaults to None.
            orientation (tuple, optional): a,b,g angles. Defaults to None.
            vector (tuple, optional): x,y,z vector. Defaults to (0,0,0).
            angles (tuple, optional): a,b,g,angles. Defaults to (0,0,0).
        """
        if coordinates != None:
            self.coordinates = coordinates
        else:
            self.coordinates = np.array(self.coordinates) + np.array(vector)
            
        if orientation != None:
            self.orientation = orientation
        else:
            self.orientation = np.array(self.orientation) + np.array(angles)
        
        print(f'{self.coordinates}, {self.orientation}')
        return
