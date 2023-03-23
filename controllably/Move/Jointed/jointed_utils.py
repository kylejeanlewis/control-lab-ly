# %% -*- coding: utf-8 -*-
"""
Created: Tue 2022/11/01 17:13:35
@author: Chang Jie

Notes / actionables:
-
"""
# Standard library imports
from __future__ import annotations
from abc import abstractmethod
import numpy as np
from typing import Optional

# Local application imports
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
    def __init__(self, safe_height:Optional[float] = None, retract:bool = False, **kwargs):
        super().__init__(**kwargs)
        self._speed_angular_max = 1
        
        self.setFlag(retract=retract)
        if safe_height is not None:
            self.setHeight(safe=safe_height)
        # else:
        #     self.setHeight('safe', self.home_coordinates[2])
        return
    
    @abstractmethod
    def moveCoordBy(self, 
        vector: tuple[float] = (0,0,0), 
        angles: tuple[float] = (0,0,0)
    ) -> bool:
        """
        Relative Cartesian movement and tool orientation, using robot coordinates.

        Args:
            vector (tuple, optional): x,y,z displacement vector. Defaults to None.
            angles (tuple, optional): a,b,c rotation angles in degrees. Defaults to None.
        
        Returns:
            bool: whether movement is successful
        """

    @abstractmethod
    def moveCoordTo(self, 
        coordinates: Optional[tuple[float]] = None, 
        orientation: Optional[tuple[float]] = None
    ) -> bool:
        """
        Absolute Cartesian movement and tool orientation, using robot coordinates.

        Args:
            coordinates (tuple, optional): x,y,z position vector. Defaults to None.
            orientation (tuple, optional): a,b,c orientation angles in degrees. Defaults to None.
        
        Returns:
            bool: whether movement is successful
        """

    @abstractmethod
    def moveJointBy(self, relative_angles: tuple[float]) -> bool:
        """
        Relative joint movement.

        Args:
            relative_angles (tuple): j1~j6 rotation angles in degrees
        
        Raises:
            Exception: Input has to be length 6
        
        Returns:
            bool: whether movement is successful
        """
        if len(relative_angles) == 6:
            raise ValueError('Length of input needs to be 6.')

    @abstractmethod
    def moveJointTo(self, absolute_angles: tuple[float]) -> bool:
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
            raise ValueError('Length of input needs to be 6.')
    
    @abstractmethod
    def retractArm(self, target: Optional[tuple[float]] = None) -> bool:
        """
        Tuck in arm, rotate about base, then extend again.

        Args:
            target (tuple, optional): x,y,z coordinates of destination. Defaults to None.
        
        Returns:
            bool: whether movement is successful
        """
  
    # Properties
    @property
    def speed_angular(self) -> float:
        if self.verbose:
            print(f'Max speed: {self._speed_max}')
            print(f'Speed fraction: {self._speed_fraction}')
        return self._speed_angular_max * self._speed_fraction
    
    def home(self, safe:bool = True, tool_offset:bool = True) -> bool:
        """
        Return the robot to home

        Args:
            tool_offset (bool, optional): whether to consider the offset of the tooltip. Defaults to True.
        
        Returns:
            bool: whether movement is successful
        """
        success= []
        ret = False
        coordinates = self.home_coordinates - self.implement_offset if tool_offset else self.home_coordinates
        
        # Tuck arm in to avoid collision
        if self.flags.get('retract', False):
            ret = self.retractArm(coordinates)
            success.append(ret)
        
        # Go to home position
        if safe:
            coordinates = self._transform_out(coordinates=coordinates, tool_offset=tool_offset)
            ret = self.safeMoveTo(coordinates=coordinates, orientation=self.home_orientation)
        else:
            ret = self.moveCoordTo(coordinates, self.home_orientation)
        success.append(ret)
        print("Homed")
        return all(success)
    
    def moveBy(self, 
        vector: tuple[float] = (0,0,0), 
        angles: tuple[float] = (0,0,0), 
        **kwargs
    ) -> bool:
        """
        Move robot by specified vector and angles

        Args:
            vector (tuple, optional): x,y,z vector to move in. Defaults to None.
            angles (tuple, optional): a,b,c angles to move in. Defaults to None.

        Returns:
            bool: whether movement is successful
        """
        vector = self._transform_in(vector=vector)
        vector = np.array(vector)
        angles = np.array(angles)
        
        if len(angles) != 3:
            if len(angles) == 6:
                return self.moveJointBy(relative_angle=angles)
            return False
        return self.moveCoordBy(vector, angles)

    def moveTo(self, 
        coordinates: Optional[tuple[float]] = None, 
        orientation: Optional[tuple[float]] = None, 
        tool_offset: Optional[tuple[float]] = None, 
        retract: bool = False, 
        **kwargs
    ) -> bool:
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
        
        if self.flags['retract'] and retract:
            self.retractArm(coordinates)
        
        if len(orientation) != 3:
            if len(orientation) == 6:
                return self.moveJointTo(absolute_angle=orientation)
            return False
        return self.moveCoordTo(coordinates, orientation)
    
    def rotateBy(self, angles: tuple[float]) -> bool:
        """
        Relative effector rotation.

        Args:
            angles (tuple): a,b,c rotation angles in degrees
        
        Raises:
            Exception: Input has to be length 3
        
        Returns:
            bool: whether movement is successful
        """
        if not any(angles):
            return True
        if len(angles) == 3:
            return self.moveJointBy((0,0,0,*angles))
        if len(angles) != 6:
            return self.moveJointBy(angles)
        raise ValueError('Length of input needs to be 3 or 6.')

    def rotateTo(self, orientation: tuple[float]) -> bool:
        """
        Absolute effector rotation.

        Args:
            orientation (tuple): a,b,c orientation angles in degrees
        
        Raises:
            Exception: Input has to be length 3
        
        Returns:
            bool: whether movement is successful
        """
        if not any(orientation):
            return True
        if len(orientation) == 3:
            return self.moveJointTo((0,0,0,*orientation))
        if len(orientation) != 6:
            return self.moveJointTo(orientation)
        raise ValueError('Length of input needs to be 3 or 6.')
