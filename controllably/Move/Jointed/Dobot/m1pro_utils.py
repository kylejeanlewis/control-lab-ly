# %% -*- coding: utf-8 -*-
"""
This module holds the class for the M1Pro from Dobot.

Classes:
    M1Pro (Dobot)
"""
# Standard library imports
from __future__ import annotations
import logging
import math
import numpy as np
import time
from types import SimpleNamespace
from typing import Optional

# Local application imports
from .dobot_utils import Dobot

logger = logging.getLogger(__name__)
logger.debug(f"Import: OK <{__name__}>")

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
    - `moveBy`: relative Cartesian movement and tool orientation, using robot coordinates
    - `retractArm`: tuck in arm, rotate about base, then extend again (NOTE: not implemented)
    - `setHandedness`: set the handedness of the robot
    - `stretchArm`: extend the arm to full reach
    """
    
    _default_flags = SimpleNamespace(busy=False, connected=False, retract=False, right_handed=False, stretched=False)
    _default_speeds = dict(j1=180, j2=180, j3=1000, j4=1000)
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
        self._speed_max = self._default_speeds
        self.setHandedness(right_handed=right_handed, stretch=False)
        self.home()
        return
    
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
        if x >= 0:                                  # main working space
            r = (x**2 + y**2)**0.5
            if not (153 <= r <= 400):
                return False
        elif abs(y) < 230/2:                        # behind the robot
            return False
        elif (x**2 + (abs(y)-200)**2)**0.5 > 200:
            return False
        
        grad = abs(y/(x+1E-6))
        gradient_threshold = 0.25
        if grad > gradient_threshold or x < 0:
            right_handed = (y>0)
            self.setHandedness(right_handed=right_handed, stretch=True) 
        return not self.deck.isExcluded(self._transform_out(coordinates, tool_offset=True))

    def setHandedness(self, right_handed:bool, stretch:bool = False) -> bool:
        """
        Set the handedness of the robot

        Args:
            right_handed (bool): whether to select right-handedness
            stretch (bool, optional): whether to stretch the arm. Defaults to False.

        Returns:
            bool: whether movement is successful
        """
        if right_handed == self.flags.right_handed:
            return False
        
        try:
            # self.dashboard.SetArmOrientation(int(right_handed),1,1,1)
            self.device.SetArmOrientation(right_handed)
        except (AttributeError, OSError):
            if self.verbose:
                print("Not connected to arm!")
        else:
            # time.sleep(2/self.speed_factor)
            self._move_time_buffer = 2/self.speed_factor + self._default_move_time_buffer
            if stretch:
                # self.stretchArm()
                # time.sleep(1/self.speed_factor)
                self._move_time_buffer = 1/self.speed_factor + self._default_move_time_buffer
            self.setFlag(right_handed=right_handed)
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
        ret1 = self.moveTo(coordinates=(x,y,z_home))
        ret2 = self.moveTo(coordinates=(320,y_stretch,z_home))
        ret3 = self.moveTo(coordinates=(x,y,z_home))
        ret4 = self.moveTo(coordinates=(x,y,z))
        self.setFlag(stretched=True)
        return all([ret1,ret2,ret3,ret4])
   
    # Protected method(s)
    def _convert_cartesian_to_angles(self, src_point:np.ndarray, dst_point: np.ndarray) -> float:
        """
        Convert travel between two points into relevant rotation angles and/or distances

        Args:
            src_point (np.ndarray): (x,y,z) coordinates, orientation of starting point
            dst_point (np.ndarray): (x,y,z) coordinates, orientation of ending point

        Returns:
            float: relevant rotation angles (in degrees) and/or distances (in mm)
        """
        right_handed = 2*(int(self.flags['right_handed'])-0.5) # 1 if right-handed; -1 if left-handed
        x1,y1,z1 = src_point
        x2,y2,z2 = dst_point
        r1 = (x1**2 + y1**2)**0.5
        r2 = (x2**2 + y2**2)**0.5
        
        theta1 = math.degrees(math.atan2(y1, x1))
        theta2 = math.degrees(math.atan2(y2, x2))
        phi1 = math.degrees(math.acos(r1/400)) * (-right_handed)
        phi2 = math.degrees(math.acos(r2/400)) * (-right_handed)
        
        src_j1_angle = theta1 + phi1
        dst_j1_angle = theta2 + phi2
        j1_angle = abs(dst_j1_angle - src_j1_angle)
        
        src_j2_angle = 2*phi1 * right_handed
        dst_j2_angle = 2*phi2 * right_handed
        j2_angle = abs(dst_j2_angle - src_j2_angle)
        
        z_travel = abs(z2 - z1)
        coord_angles = (j1_angle, j2_angle, z_travel)
        print(coord_angles)
        return coord_angles
    
    def _get_move_wait_time(self, 
        distances: np.ndarray, 
        speeds: np.ndarray, 
        accels: Optional[np.ndarray] = None
    ) -> float:
        """
        Get the amount of time to wait to complete movement

        Args:
            distances (np.ndarray): array of distances to travel
            speeds (np.ndarray): array of axis speeds
            accels (Optional[np.ndarray], optional): array of axis accelerations. Defaults to None.

        Returns:
            float: wait time to complete travel
        """
        move_time = super()._get_move_wait_time(distances, speeds, accels)
        move_time += self._move_time_buffer
        self._move_time_buffer = self._default_move_time_buffer
        return move_time
