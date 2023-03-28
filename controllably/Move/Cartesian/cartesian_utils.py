# %% -*- coding: utf-8 -*-
"""
Created: Tue 2022/11/01 17:13:35
@author: Chang Jie

Notes / actionables:
-
"""
# Standard library imports
from __future__ import annotations
import numpy as np
import time
from typing import Optional

# Third party imports
import serial # pip install pyserial

# Local application imports
from ...misc import Helper
from ..move_utils import Mover
print(f"Import: OK <{__name__}>")
    
class Gantry(Mover):
    """
    Gantry robot controls

    Args:
        port (str): com port address
        limits (list, optional): lower and upper bounds of movement. Defaults to [(0,0,0), (0,0,0)].
        safe_height (float, optional): safe height. Defaults to None.
        max_speed (float, optional): maximum movement speed. Defaults to 250.
    
    Kwargs:
        home_coordinates (tuple, optional): position to home in arm coordinates. Defaults to (0,0,0).
        home_orientation (tuple, optional): orientation to home. Defaults to (0,0,0).
        orientate_matrix (numpy.matrix, optional): matrix to transform arm axes to workspace axes. Defaults to np.identity(3).
        translate_vector (numpy.ndarray, optional): vector to transform arm position to workspace position. Defaults to (0,0,0).
        implement_offset (tuple, optional): implement offset vector pointing from end of effector to tool tip. Defaults to (0,0,0).
        scale (int, optional): scale factor to transform arm scale to workspace scale. Defaults to 1.
        verbose (bool, optional): whether to print outputs. Defaults to False.
    """
    def __init__(self, 
        port: str, 
        limits: tuple[tuple[float]] = ((0, 0, 0), (0, 0, 0)), 
        safe_height: Optional[float] = None, 
        max_speed: float = 250, # [mm/s]
        **kwargs
    ):
        super().__init__(**kwargs)
        self._limits = ((0, 0, 0), (0, 0, 0))
        
        self.limits = limits
        self._speed_max = max_speed
        if safe_height is not None:
            self.setHeight(safe=safe_height)
        
        self._connect(port)
        self.home()
        return
    
    # Properties
    @property
    def limits(self) -> np.ndarray:
        return np.array(self._limits)
    @limits.setter
    def limits(self, value:list):
        if len(value) != 2 or any([len(row)!=3 for row in value]):
            raise Exception('Please input a sequence of (lower_xyz_limit, upper_xyz_limit)')
        self._limits = ( tuple(value[0]), tuple(value[1]) )
        return
    
    @property
    def port(self) -> str:
        return self.connection_details.get('port', '')

    def disconnect(self):
        """
        Disconnect serial connection to robot
        
        Returns:
            None: None is successfully disconnected, else serial.Serial
        """
        try:
            self.device.close()
        except Exception as e:
            if self.verbose:
                print(e)
        self.setFlag(connected=False)
        return
    
    def isFeasible(self, 
        coordinates: tuple[float], 
        transform_in: bool = False, 
        tool_offset: bool = False, 
        **kwargs
    ) -> bool:
        """
        Checks if specified coordinates is a feasible position for robot to access

        Args:
            coordinates (tuple): x,y,z coordinates
            transform (bool, optional): whether to transform the coordinates. Defaults to False.
            tool_offset (bool, optional): whether to consider tooltip offset. Defaults to False.

        Returns:
            bool: whether coordinates is a feasible position
        """
        if transform_in:
            coordinates = self._transform_in(coordinates=coordinates, tool_offset=tool_offset)
        coordinates = np.array(coordinates)
        l_bound, u_bound = self.limits
        
        if all(np.greater_equal(coordinates, l_bound)) and all(np.less_equal(coordinates, u_bound)):
            return not self.deck.is_excluded(self._transform_out(coordinates, tool_offset=True))
        print(f"Range limits reached! {self.limits}")
        return False

    def moveBy(self, vector:tuple[float], **kwargs) -> bool:
        """
        Move robot by specified vector

        Args:
            vector (tuple): x,y,z vector to move in
            to_safe_height (bool, optional): whether to return to safe height first. Defaults to False.

        Returns:
            bool: whether movement is successful
        """
        return super().moveBy(vector=vector)
    
    @Helper.safety_measures
    def moveTo(self, coordinates, tool_offset=True, **kwargs) -> bool:
        """
        Move robot to specified coordinates and orientation

        Args:
            coordinates (tuple): x,y,z coordinates to move to. Defaults to None.
            to_safe_height (bool, optional): whether to return to safe height first. Defaults to True.
            jump_height (int, or float): height value to jump to. Defaults to None.
            tool_offset (bool, optional): whether to consider tooltip offset. Defaults to True.
            
        Returns:
            bool: whether movement is successful
        """
        coordinates = np.array(self._transform_in(coordinates=coordinates, tool_offset=tool_offset))
        if not self.isFeasible(coordinates):
            return False
            
        z_first = True if (self.coordinates[2] < coordinates[2]) else False
        positionXY = f'X{coordinates[0]}Y{coordinates[1]}'
        position_Z = f'Z{coordinates[2]}'
        moves = [position_Z, positionXY] if z_first else [positionXY, position_Z]
        
        self._query("G90\n")
        for move in moves:
            self._query(f"G0 {move}\n")
        self._query("G90\n")
        
        distances = abs(self.coordinates - coordinates)
        times = distances / self.speed
        move_time = max(times[:2]) + times[2]
        time.sleep(move_time)
        self.updatePosition(coordinates=coordinates)
        return True
    
    def reset(self):
        return super().reset()
    
    def setSpeed(self, speed: int): # NOTE: waiting for PR #48
        return super().setSpeed(speed)
    
    def shutdown(self):
        """
        Close serial connection and shutdown
        """
        # self.home()
        return super().shutdown()
    
    # Protected method(s)
    def _connect(self, port:str, baudrate:int, timeout:int = None):
        """
        Connect to machine control unit

        Args:
            port (str): com port address
            baudrate (int): baudrate
            timeout (int, optional): timeout in seconds. Defaults to None.
            
        Returns:
            serial.Serial: serial connection to machine control unit if connection is successful, else None
        """
        self.connection_details = {
            'port': port,
            'baudrate': baudrate,
            'timeout': timeout
        }
        device = None
        try:
            device = serial.Serial(port, baudrate, timeout=timeout)
        except Exception as e:
            print(f"Could not connect to {port}")
            if self.verbose:
                print(e)
        else:
            print(f"Connection opened to {port}")
            self.setFlag(connected=True)
        self.device = device
        return

    def _query(self, command:str) -> str:
        response = ''
        self._write(command)
        try:
            response = self.device.readline()
        except Exception as e:
            if self.verbose:
                print(e)
        else:
            print(response)
        return response

    def _write(self, command:str):
        try:
            self.device.write(command.encode('utf-8'))
        except Exception as e:
            if self.verbose:
                print(e)
            return False
        return True

    # def safeMoveTo(self, coordinates, jump_height=None, tool_offset=True, **kwargs) -> bool:
    #     """
    #     Safe version of moveTo

    #     Args:
    #         coordinates (tuple): x,y,z coordinates to move to. Defaults to None.
    #         jump_height (int, or float): height value to jump to. Defaults to None.
    #         tool_offset (bool, optional): whether to consider tooltip offset. Defaults to True.
            
    #     Returns:
    #         bool: whether movement is successful
    #     """
    #     coordinates = self._transform_in(coordinates=coordinates, tool_offset=tool_offset)
    #     coordinates = np.array(coordinates)
    #     if not self.isFeasible(coordinates):
    #         return False
        
    #     # Retreat to safe height first
    #     if jump_height is None:
    #         jump_height = self.heights['safe']
    #     if self.coordinates[2] < jump_height:
    #         try:
    #             self._query("G90\n")
    #             self._query(f"G0 Z{jump_height}\n")
    #             self._query("G90\n")
    #         except Exception as e:
    #             if self.verbose:
    #                 print(e)
    #         self.coordinates = (*self.coordinates[0:2], jump_height)
    
    #     z_first = True if self.coordinates[2]<coordinates[2] else False
    #     positionXY = f'X{coordinates[0]}Y{coordinates[1]}'
    #     position_Z = f'Z{coordinates[2]}'
    #     moves = [position_Z, positionXY] if z_first else [positionXY, position_Z]
    #     try:
    #         self._query("G90\n")
    #         for move in moves:
    #             self._query(f"G0 {move}\n")
    #         self._query("G90\n")
    #     except Exception as e:
    #         if self.verbose:
    #             print(e)
    #     distances = abs(self.coordinates - coordinates)
    #     times = distances / self.speed
    #     move_time = max(times[:2]) + times[2]
    #     time.sleep(move_time)
    #     self.updatePosition(coordinates=coordinates)
    #     return True