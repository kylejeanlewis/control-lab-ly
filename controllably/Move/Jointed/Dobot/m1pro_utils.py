# %% -*- coding: utf-8 -*-
"""

"""
# Standard library imports
from __future__ import annotations
import math
import numpy as np
import time

# Local application imports
from .dobot_utils import Dobot
print(f"Import: OK <{__name__}>")

class M1Pro(Dobot):
    """
    M1Pro provides methods to control Dobot's M1 Pro arm
    
    ### Constructor
    Args:
        `ip_address` (str, optional): IP address of Dobot. Defaults to '192.168.2.21'.
        `right_handed` (bool, optional): whether the robot is in right-handed mode (i.e elbow bends to the right). Defaults to True.
        `safe_height` (float, optional): height at which obstacles can be avoided. Defaults to 100.
        `home_coordinates` (tuple[float], optional): home coordinates for the robot. Defaults to (0,300,100).
    
    ## Methods
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
        'right_handed': None
    }
    def __init__(self, 
        ip_address: str = '192.168.2.21', 
        right_handed: bool = True, 
        safe_height: float = 100,
        home_coordinates: tuple[float] = (0,300,100), 
        **kwargs
    ):
        """
        Instantiate the class

        Args:
            ip_address (str, optional): IP address of Dobot. Defaults to '192.168.2.21'.
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
        self._speed_angular_max = 180
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
        if not (5 < z < 245):
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
        if grad > 0.75 or x < 0:
            right_hand = (y>0)
            self.setHandedness(right_hand=right_hand, stretch=True) 
        return not self.deck.is_excluded(self._transform_out(coordinates, tool_offset=True))
    
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
        if vector is None:
            vector = (0,0,0)
        if angles is None:
            angles = (0,0,0)
        coordinates, orientation = self.position
        new_coordinates = np.array(coordinates) + np.array(vector)
        new_orientation = np.array(orientation) + np.array(angles)
        return self.moveCoordTo(new_coordinates, new_orientation)
    
    def retractArm(self, *args, **kwargs) -> bool:      # NOTE: not implemented
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
        set_value = None
        if not right_hand and self.flags['right_handed'] != False:  # Set to left-handed: 0
            set_value = 0
        elif right_hand and self.flags['right_handed'] != True:     # Set to right-handed: 1
            set_value = 1
        else:
            return False
        
        try:
            self.dashboard.SetArmOrientation(set_value,1,1,1)
        except (AttributeError, OSError):
            if self.verbose:
                print("Not connected to arm!")
        else:
            time.sleep(2)
            if stretch:
                self.stretchArm()
                time.sleep(1)
        self.setFlag(right_handed=bool(set_value))
        return True
            
    def stretchArm(self) -> bool:
        """
        Extend the arm to full reach
        
        Returns:
            bool: whether movement is successful
        """
        _,y,z = self.coordinates
        y = 240 * math.copysign(1, y)
        return self.moveCoordTo(coordinates=(320,y,z))
   