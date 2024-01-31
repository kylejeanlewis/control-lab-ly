# %% -*- coding: utf-8 -*-
"""
This module holds the class for the M1Pro from Dobot.

Classes:
    M1Pro (Dobot)
"""
# Standard library imports
from __future__ import annotations
import math
import numpy as np
import time
from typing import Optional

# Local application imports
from .dobot_utils import Dobot
print(f"Import: OK <{__name__}>")

class M1Pro(Dobot):
    """
    M1Pro provides methods to control Dobot's M1 Pro arm
    
    ### Constructor
    Args:
        `ip_address` (str): IP address of Dobot
        `right_handed` (bool, optional): whether the robot is in right-handed mode (i.e elbow bends to the right). Defaults to True.
        `safe_height` (float, optional): height at which obstacles can be avoided. Defaults to 100.
        `home_coordinates` (tuple[float], optional): home coordinates for the robot. Defaults to (0,300,100).
    
    ### Methods
    - `home`: make the robot go home
    - `isFeasible`: checks and returns whether the target coordinate is feasible
    - `moveCoordBy`: relative Cartesian movement and tool orientation, using robot coordinates
    - `retractArm`: tuck in arm, rotate about base, then extend again (NOTE: not implemented)
    - `setHandedness`: set the handedness of the robot
    - `stretchArm`: extend the arm to full reach
    """
    
    _default_flags = {
        'busy': False,
        'connected': False,
        'retract': False, 
        'right_handed': False,
        'stretched': False
    }
    def __init__(self, 
        ip_address: str, 
        right_handed: bool = True, 
        safe_height: float = 100,
        home_coordinates: tuple[float] = (0,300,100), 
        **kwargs
    ):
        """
        Instantiate the class

        Args:
            ip_address (str): IP address of Dobot
            right_handed (bool, optional): whether the robot is in right-handed mode (i.e elbow bends to the right). Defaults to True.
            safe_height (float, optional): height at which obstacles can be avoided. Defaults to 100.
            home_coordinates (tuple[float], optional): home coordinates for the robot. Defaults to (0,300,100).
        """
        super().__init__(
            ip_address=ip_address, 
            safe_height=safe_height,
            home_coordinates=home_coordinates, 
            **kwargs
        )
        self._speed_max = dict(j1=180, j2=180, j3=1000, j4=1000)
        self.setHandedness(right_hand=right_handed, stretch=False)
        self.home()
        return
    
    def home(self, safe:bool = True, tool_offset:bool = False) -> bool:
        """
        Make the robot go home

        Args:
            safe (bool, optional): whether to use `safeMoveTo()`. Defaults to True.
            tool_offset (bool, optional): whether to consider tooltip offset. Defaults to False.
        
        Returns:
            bool: whether movement is successful
        """
        return super().home(safe=safe, tool_offset=tool_offset)
    
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
        x,y,z = coordinates
        
        # Z-axis
        if not (5 <= z <= 245):
            return False
        # XY-plane
        if x >= 0:
            r = (x**2 + y**2)**0.5
            if not (153 <= r <= 400):
                return False
        elif abs(y) < 230/2:
            return False
        elif (x**2 + (abs(y)-200)**2)**0.5 > 200:
            return False
        
        # Space constraints
        # if x > 344: # front edge
        #     return False
        # if x < 76 and abs(y) < 150: # elevated structure
        #     return False
        
        grad = abs(y/(x+1E-6))
        gradient_threshold = 0.25
        if grad > gradient_threshold or x < 0:
            right_hand = (y>0)
            self.setHandedness(right_hand=right_hand, stretch=True) 
        return not self.deck.isExcluded(self._transform_out(coordinates, tool_offset=True))
    
    def moveCoordBy(self, 
        vector: tuple[float] = (0,0,0), 
        angles: tuple[float] = (0,0,0),
        **kwargs
    ) -> bool:
        """
        Relative Cartesian movement and tool orientation, using robot coordinates

        Args:
            vector (tuple[float], optional): x,y,z displacement vector. Defaults to (0,0,0).
            angles (tuple[float], optional): a,b,c rotation angles in degrees. Defaults to (0,0,0).

        Returns:
            bool: whether movement is successful
        """
        if vector is None:
            vector = (0,0,0)
        if angles is None:
            angles = (0,0,0)
        coordinates, orientation = self.position
        new_coordinates = np.array(coordinates) + np.array(vector)
        new_orientation = np.array(orientation) + np.array(angles)
        return self.moveCoordTo(new_coordinates, new_orientation, **kwargs)
    
    def retractArm(self, target:Optional[tuple[float]] = None) -> bool:         # NOTE: not implemented
        """
        Tuck in arm, rotate about base, then extend again

        Args:
            target (Optional[tuple[float]], optional): x,y,z coordinates of destination. Defaults to None.

        Returns:
            bool: whether movement is successful
        """    
        return super().retractArm()
    
    def setHandedness(self, right_hand:bool, stretch:bool = False) -> bool:
        """
        Set the handedness of the robot

        Args:
            right_hand (bool): whether to select right-handedness
            stretch (bool, optional): whether to stretch the arm. Defaults to False.

        Returns:
            bool: whether movement is successful
        """
        if right_hand == self.flags['right_handed']:
            return False
        
        try:
            self.dashboard.SetArmOrientation(int(right_hand),1,1,1)
        except (AttributeError, OSError):
            if self.verbose:
                print("Not connected to arm!")
        else:
            time.sleep(2)
            if stretch:
                # self.stretchArm()
                time.sleep(1)
            self.setFlag(right_handed=right_hand)
        return True
            
    def stretchArm(self) -> bool:
        """
        Extend the arm to full reach
        
        Returns:
            bool: whether movement is successful
        """
        if self.flags['stretched']:
            return False
        x,y,z = self.coordinates
        y_stretch = math.copysign(240, y)
        z_home = self.home_coordinates[2]
        ret1 = self.moveCoordTo(coordinates=(x,y,z_home))
        ret2 = self.moveCoordTo(coordinates=(320,y_stretch,z_home))
        ret3 = self.moveCoordTo(coordinates=(x,y,z_home))
        ret4 = self.moveCoordTo(coordinates=(x,y,z))
        self.setFlag(stretched=True)
        return all([ret1,ret2,ret3,ret4])
   
   # Protected method(s)
    def _get_move_wait_time(self, 
        distances: np.ndarray, 
        speeds: np.ndarray, 
        accels: Optional[np.ndarray] = None,
        cartesian_to_angles: bool = False
    ) -> float:
        """
        Get the amount of time to wait to complete movement

        Args:
            distances (np.ndarray): array of distances to travel
            speeds (np.ndarray): array of axis speeds
            accels (Optional[np.ndarray], optional): array of axis accelerations. Defaults to None.
            cartesian_to_angles (bool, optional): whether from coordinates to joint rotations angles. Defaults to False.

        Returns:
            float: wait time to complete travel
        """
        if cartesian_to_angles is None:
            return super()._get_move_wait_time(distances=distances, speeds=speeds, accels=accels)
        
        dx,dy,dz = distances[:3]
        rotation_1 = abs( math.degrees(math.atan2(dy, dx)) )                    # joint 1
        distance_z = abs(dz)
        
        distances = np.array([rotation_1, distance_z, *distances[3:]])
        speeds = np.array([speeds[0], speeds[2], *speeds[3:]])
        accels = np.zeros(len(speeds)) if accels is None else accels
        
        times = [self._calculate_travel_time(d,s,a,a) for d,s,a in zip(distances, speeds, accels)]
        move_time = max(times[2:]) + times[0] + times[1]
        if self.verbose:
            print(distances)
            print(speeds)
            print(accels)
            print(times)
        return move_time
