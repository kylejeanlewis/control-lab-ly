# %% -*- coding: utf-8 -*-
"""
Created: Tue 2022/11/01 17:13:35
@author: Chang Jie

Notes / actionables:
-
"""
# Standard library imports
import numpy as np

# Third party imports
import serial # pip install pyserial

# Local application imports
from ..mover_utils import Mover
print(f"Import: OK <{__name__}>")

CNC_SPEED = 250
    
class Gantry(Mover):
    """
    Gantry robot controls

    Args:
        port (str): com port address
        limits (list, optional): lower and upper bounds of movement. Defaults to [(0,0,0), (0,0,0)].
        safe_height (float, optional): safe height. Defaults to None.
        move_speed (float, optional): movement speed. Defaults to 0.
    
    Kwargs:
        home_coordinates (tuple, optional): position to home in arm coordinates. Defaults to (0,0,0).
        home_orientation (tuple, optional): orientation to home. Defaults to (0,0,0).
        orientate_matrix (numpy.matrix, optional): matrix to transform arm axes to workspace axes. Defaults to np.identity(3).
        translate_vector (numpy.ndarray, optional): vector to transform arm position to workspace position. Defaults to (0,0,0).
        implement_offset (tuple, optional): implement offset vector pointing from end of effector to tool tip. Defaults to (0,0,0).
        scale (int, optional): scale factor to transform arm scale to workspace scale. Defaults to 1.
        verbose (bool, optional): whether to print outputs. Defaults to False.
    """
    def __init__(self, port:str, limits=[(0, 0, 0), (0, 0, 0)], safe_height=None, move_speed=-1, **kwargs):
        super().__init__(**kwargs)
        self._limits = [(0, 0, 0), (0, 0, 0)]
        
        self.device = None
        self.limits = limits
        
        self.port = ''
        self._baudrate = None
        self._timeout = None
        # self._movement_speed = move_speed
        
        if safe_height is not None:
            self.setHeight('safe', safe_height)
        self._connect(port)
        self.home()
        return
    
    @property
    def limits(self):
        return np.array(self._limits)
    @limits.setter
    def limits(self, value:list):
        if len(value) != 2 or any([len(row)!=3 for row in value]):
            raise Exception('Please input a list of [lower_xyz_limit, upper_xyz_limit]')
        self._limits = ( tuple(value[0]), tuple(value[1]) )
        return
    
    def _connect(self, port:str, baudrate:int, timeout=None):
        """
        Connect to machine control unit

        Args:
            port (str): com port address
            baudrate (int): baudrate
            timeout (int, optional): timeout in seconds. Defaults to None.
            
        Returns:
            serial.Serial: serial connection to machine control unit if connection is successful, else None
        """
        self.port = port
        self._baudrate = baudrate
        self._timeout = timeout
        device = None
        try:
            device = serial.Serial(port, baudrate, timeout=timeout)
            print(f"Connection opened to {port}")
        except Exception as e:
            if self.verbose:
                print(f"Could not connect to {port}")
                print(e)
        self.device = device
        return self.device
    
    def _shutdown(self):
        """
        Close serial connection and shutdown
        """
        self.home()
        self.disconnect()
        return

    def connect(self):
        """
        Reconnect to robot using existing port and baudrate
        
        Returns:
            serial.Serial: serial connection to machine control unit if connection is successful, else None
        """
        return self._connect(self.port, self._baudrate, self._timeout)
    
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
        self.device = None
        return self.device

    def isConnected(self):
        """
        Check whether machine control unit is connected

        Returns:
            bool: whether machine control unit is connected
        """
        if self.device is None:
            print(f"{self.__class__} ({self.port}) not connected.")
            return False
        return True
    
    def isFeasible(self, coordinates, transform=False, tool_offset=False, **kwargs):
        """
        Checks if specified coordinates is a feasible position for robot to access

        Args:
            coordinates (tuple): x,y,z coordinates
            transform (bool, optional): whether to transform the coordinates. Defaults to False.
            tool_offset (bool, optional): whether to consider tooltip offset. Defaults to False.

        Returns:
            bool: whether coordinates is a feasible position
        """
        if transform:
            coordinates = self._transform_in(coordinates=coordinates, tool_offset=tool_offset)
        coordinates = np.array(coordinates)
        l_bound, u_bound = self.limits
        
        if all(np.greater_equal(coordinates, l_bound)) and all(np.less_equal(coordinates, u_bound)):
            return True
        print(f"Range limits reached! {self.limits}")
        return False

    def moveBy(self, vector, to_safe_height=False, **kwargs):
        """
        Move robot by specified vector

        Args:
            vector (tuple): x,y,z vector to move in
            to_safe_height (bool, optional): whether to return to safe height first. Defaults to False.

        Returns:
            bool: whether movement is successful
        """
        return super().moveBy(vector=vector, to_safe_height=to_safe_height)
    
    def moveTo(self, coordinates, to_safe_height=True, jump_height=None, tool_offset=True, **kwargs):
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
        coordinates = self._transform_in(coordinates=coordinates, tool_offset=tool_offset)
        coordinates = np.array(coordinates)
        if not self.isFeasible(coordinates):
            return
        
        # Retreat to safe height first
        if jump_height is None:
            jump_height = self.heights['safe']
        if to_safe_height and self.coordinates[2] < jump_height:
            try:
                self.device.write(bytes("G90\n", 'utf-8'))
                print(self.device.readline())
                self.device.write(bytes(f"G0 Z{jump_height}\n", 'utf-8'))
                print(self.device.readline())
                self.device.write(bytes("G90\n", 'utf-8'))
                print(self.device.readline())
            except Exception as e:
                if self.verbose:
                    print(e)
            self.coordinates = (*self.coordinates[0:2], jump_height)
        
        z_first = True if self.coordinates[2]<coordinates[2] else False
        positionXY = f'X{coordinates[0]}Y{coordinates[1]}'
        position_Z = f'Z{coordinates[2]}'
        moves = [position_Z, positionXY] if z_first else [positionXY, position_Z]
        try:
            self.device.write(bytes("G90\n", 'utf-8'))
            print(self.device.readline())
            for move in moves:
                self.device.write(bytes(f"G0 {move}\n", 'utf-8'))
                print(self.device.readline())
            self.device.write(bytes("G90\n", 'utf-8'))
            print(self.device.readline())
        except Exception as e:
            if self.verbose:
                print(e)

        self.updatePosition(coordinates=coordinates)
        return
    