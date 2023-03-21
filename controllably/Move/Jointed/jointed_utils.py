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
from ...misc import HELPER
from ..move_utils import Mover
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
        self._speed_angular = 1
        self.setFlag('retract', False)
        
        if safe_height is not None:
            self.setHeight('safe', safe_height)
        # else:
        #     self.setHeight('safe', self.home_coordinates[2])
        return
    
    @property
    def speed_angular(self):
        return self._speed_angular * self._speed_fraction
    
    def home(self, tool_offset=True):
        """
        Return the robot to home

        Args:
            tool_offset (bool, optional): whether to consider the offset of the tooltip. Defaults to True.
        
        Returns:
            bool: whether movement is successful
        """
        return_values= []
        # Tuck arm in to avoid collision
        if self._flags['retract']:
            ret = self.retractArm(self.home_coordinates)
            return_values.append(ret)
        
        # Go to home position
        coordinates = self.home_coordinates - self.implement_offset if tool_offset else self.home_coordinates
        # coordinates = self._transform_out(coordinates=coordinates, tool_offset=tool_offset)
        # ret = self.safeMoveTo(coordinates=coordinates, orientation=self.home_orientation)
        ret = self.moveCoordTo(coordinates, self.home_orientation)
        return_values.append(ret)
        print("Homed")
        return all(return_values)
    
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
        vector = self._transform_in(vector=vector)
        vector = np.array(vector)
        angles = np.array(angles)
        
        if len(angles) != 3:
            if len(angles) == 6:
                return self.moveJointBy(relative_angle=angles)
            return False
        return self.moveCoordBy(vector, angles)

    def moveTo(self, coordinates=None, orientation=None, tool_offset=True, retract=False, **kwargs):
        """
        Absolute Cartesian movement, using workspace coordinates.

        Args:
            coordinates (tuple, optional): x,y,z coordinates to move to. Defaults to None.
            orientation (tuple, optional): a,b,c orientation to move to. Defaults to None.
            retract (bool, optional): whether to tuck in arm before moving. Defaults to False.
            tool_offset (bool, optional): whether to consider tooltip offset. Defaults to True.
        
        Returns:
            bool: whether movement is successful
        """
        if coordinates is None:
            coordinates,_ = self.getToolPosition() if tool_offset else self.getUserPosition()
        if orientation is None:
            orientation = self.orientation
        coordinates = self._transform_in(coordinates=coordinates, tool_offset=tool_offset)
        coordinates = np.array(coordinates)
        orientation = np.array(orientation)
        
        if self._flags['retract'] and retract:
            self.retractArm(coordinates)
        
        if len(orientation) != 3:
            if len(orientation) == 6:
                return self.moveJointTo(absolute_angle=orientation)
            return False
        return self.moveCoordTo(coordinates, orientation)
    
    @HELPER.safety_measures
    def moveCoordBy(self, vector=None, angles=None):
        """
        Relative Cartesian movement and tool orientation, using robot coordinates.

        Args:
            vector (tuple, optional): x,y,z displacement vector. Defaults to None.
            angles (tuple, optional): a,b,c rotation angles in degrees. Defaults to None.
        
        Returns:
            bool: whether movement is successful
        """
        return True

    @HELPER.safety_measures
    def moveCoordTo(self, coordinates=None, orientation=None):
        """
        Absolute Cartesian movement and tool orientation, using robot coordinates.

        Args:
            coordinates (tuple, optional): x,y,z position vector. Defaults to None.
            orientation (tuple, optional): a,b,c orientation angles in degrees. Defaults to None.
            tool_offset (bool, optional): whether to consider implement offset. Defaults to True.
        
        Returns:
            bool: whether movement is successful
        """
        return True

    @HELPER.safety_measures
    def moveJointBy(self, relative_angles):
        """
        Relative joint movement.

        Args:
            relative_angles (tuple): j1~j6 rotation angles in degrees
        
        Raises:
            Exception: Input has to be length 6
        
        Returns:
            bool: whether movement is successful
        """
        if len(relative_angles) != 6:
            raise Exception('Length of input needs to be 6')
        return True

    @HELPER.safety_measures
    def moveJointTo(self, absolute_angles):
        """
        Absolute joint movement.

        Args:
            absolute_angles (tuple): j1~j6 orientation angles in degrees
        
        Raises:
            Exception: Input has to be length 6
        
        Returns:
            bool: whether movement is successful
        """
        if len(absolute_angles) != 6:
            raise Exception('Length of input needs to be 6')
        return True
    
    @HELPER.safety_measures
    def retractArm(self, target=None):
        """
        Tuck in arm, rotate about base, then extend again.

        Args:
            target (tuple, optional): x,y,z coordinates of destination. Defaults to None.
        
        Returns:
            bool: whether movement is successful
        """
        return True
    
    def rotateBy(self, angles):
        """
        Relative effector rotation.

        Args:
            angles (tuple): a,b,c rotation angles in degrees
        
        Raises:
            Exception: Input has to be length 3
        
        Returns:
            bool: whether movement is successful
        """
        if len(angles) != 3:
            raise Exception('Length of input needs to be 3')
        angles = tuple(angles)
        if not any(angles):
            return True
        return self.moveJointBy((0,0,0,*angles))

    def rotateTo(self, orientation):
        """
        Absolute effector rotation.

        Args:
            orientation (tuple): a,b,c orientation angles in degrees
        
        Raises:
            Exception: Input has to be length 3
        
        Returns:
            bool: whether movement is successful
        """
        if len(orientation) != 3:
            raise Exception('Length of input needs to be 3')
        angles = np.array(orientation) - np.array(self.orientation)
        return self.rotateBy(angles)
