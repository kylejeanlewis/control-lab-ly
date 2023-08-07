# %% -*- coding: utf-8 -*-
"""
This module holds the base class for jointed mover tools.

Classes:
    RobotArm (Mover)
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
    Abstract Base Class (ABC) for Robot Arm objects. RobotArm provides controls for jointed robots with articulated arms.
    ABC cannot be instantiated, and must be subclassed with abstract methods implemented before use.
    
    ### Constructor
    Args:
        `safe_height` (Optional[float], optional): height at which obstacles can be avoided. Defaults to None.
        `retract` (bool, optional): whether to retract arm before movement. Defaults to False.
    
    ### Properties
    - `speed_angular` (float): angular speed of the robot

    ### Methods
    #### Abstract
    - `disconnect`: disconnect from device
    - `isFeasible`: checks and returns whether the target coordinate is feasible
    - `moveCoordBy`: relative Cartesian movement and tool orientation, using robot coordinates
    - `moveCoordTo`: absolute Cartesian movement and tool orientation, using robot coordinates
    - `moveJointBy`: relative joint movement
    - `moveJointTo`: absolute joint movement
    - `reset`: reset the robot
    - `retractArm`: tuck in arm, rotate about base, then extend again
    - `setSpeed`: set the speed of the robot
    - `shutdown`: shutdown procedure for tool
    - `_connect`: connection procedure for tool
    #### Public
    - `home`: make the robot go home
    - `moveBy`: move the robot by target direction, by specified vector and angles
    - `moveTo`: move the robot to target position, using workspace coordinates
    - `rotateBy`: relative end effector rotation
    - `rotateTo`: absolute end effector rotation
    """
    
    _default_flags = {
        'busy': False,
        'connected': False,
        'retract': False
    }
    _place: str = '.'.join(__name__.split('.')[1:-1])
    def __init__(self, safe_height:Optional[float] = None, retract:bool = False, **kwargs):
        """
        Instantiate the class

        Args:
            safe_height (Optional[float], optional): height at which obstacles can be avoided. Defaults to None.
            retract (bool, optional): whether to retract arm before movement. Defaults to False.
        """
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
        Relative Cartesian movement and tool orientation, using robot coordinates

        Args:
            vector (tuple[float], optional): x,y,z displacement vector. Defaults to (0,0,0).
            angles (tuple[float], optional): a,b,c rotation angles in degrees. Defaults to (0,0,0).

        Returns:
            bool: whether movement is successful
        """

    @abstractmethod
    def moveCoordTo(self, 
        coordinates: Optional[tuple[float]] = None, 
        orientation: Optional[tuple[float]] = None
    ) -> bool:
        """
        Absolute Cartesian movement and tool orientation, using robot coordinates

        Args:
            coordinates (Optional[tuple[float]], optional): x,y,z position vector. Defaults to None.
            orientation (Optional[tuple[float]], optional): a,b,c orientation angles in degrees. Defaults to None.
        
        Returns:
            bool: whether movement is successful
        """

    @abstractmethod
    def moveJointBy(self, relative_angles: tuple[float]) -> bool:
        """
        Relative joint movement

        Args:
            relative_angles (tuple[float]): j1~j6 rotation angles in degrees

        Raises:
            ValueError: Length of input needs to be 6.

        Returns:
            bool: whether movement is successful
        """
        if len(relative_angles) == 6:
            raise ValueError('Length of input needs to be 6.')

    @abstractmethod
    def moveJointTo(self, absolute_angles: tuple[float]) -> bool:
        """
        Absolute joint movement

        Args:
            absolute_angles (tuple[float]): j1~j6 orientation angles in degrees

        Raises:
            ValueError: Length of input needs to be 6.

        Returns:
            bool: whether movement is successful
        """
        if len(absolute_angles) != 6:
            raise ValueError('Length of input needs to be 6.')
    
    @abstractmethod
    def retractArm(self, target: Optional[tuple[float]] = None) -> bool:
        """
        Tuck in arm, rotate about base, then extend again

        Args:
            target (Optional[tuple[float]], optional): x,y,z coordinates of destination. Defaults to None.

        Returns:
            bool: whether movement is successful
        """
  
    # Properties
    @property
    def speed_angular(self) -> float:
        if self.verbose:
            print(f'Max speed: {self._speed_angular_max}')
            print(f'Speed fraction: {self._speed_fraction}')
        return self._speed_angular_max * self._speed_fraction
    
    def home(self, safe:bool = True, tool_offset:bool = True) -> bool:
        """
        Make the robot go home

        Args:
            safe (bool, optional): whether to use `safeMoveTo()`. Defaults to True.
            tool_offset (bool, optional): whether to consider tooltip offset. Defaults to True.
        
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
            ret = self.safeMoveTo(coordinates=coordinates, orientation=self.home_orientation, tool_offset=tool_offset)
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
        Move the robot by target direction, by specified vector and angles

        Args:
            vector (tuple[float], optional): x,y,z vector to move in. Defaults to (0,0,0).
            angles (tuple[float], optional): a,b,c angles to move in. Defaults to (0,0,0).

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
        tool_offset: bool = True, 
        retract: bool = False, 
        **kwargs
    ) -> bool:
        """
        Move the robot to target position, using workspace coordinates

        Args:
            coordinates (Optional[tuple[float]], optional): x,y,z coordinates to move to. Defaults to None.
            orientation (Optional[tuple[float]], optional): a,b,c orientation to move to. Defaults to None.
            tool_offset (bool, optional): whether to consider tooltip offset. Defaults to True.
            retract (bool, optional): whether to retract arm before movement. Defaults to False.

        Returns:
            bool: whether movement is successful
        """
        if coordinates is None:
            coordinates,_ = self.tool_position if tool_offset else self.user_position
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
        Relative effector rotation

        Args:
            angles (tuple[float]): a,b,c rotation angles in degrees
        
        Raises:
            Exception: Length of input needs to be 3 or 6
        
        Returns:
            bool: whether movement is successful
        """
        if not any(angles):
            return True
        if len(angles) == 3:
            return self.moveJointBy((0,0,0,*angles))
        if len(angles) == 6:
            return self.moveJointBy(angles)
        raise ValueError('Length of input needs to be 3 or 6.')

    def rotateTo(self, orientation: tuple[float]) -> bool:
        """
        Absolute end effector rotation

        Args:
            orientation (tuple[float]): a,b,c orientation angles in degrees
        
        Raises:
            Exception: Length of input needs to be 3 or 6
        
        Returns:
            bool: whether movement is successful
        """
        if not any(orientation):
            return True
        if len(orientation) == 3:
            return self.rotateBy(orientation - self.orientation)
        if len(orientation) == 6:
            return self.moveJointTo(orientation)
        raise ValueError('Length of input needs to be 3 or 6.')
