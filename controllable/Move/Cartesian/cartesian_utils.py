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
from .. import Mover
print(f"Import: OK <{__name__}>")

class CNC(Mover):
    """
    Controller for cnc xyz-movements.
    - port: serial port of cnc Arduino
    """
    def __init__(self, port, xyz_bounds=[(0,0,0), (0,0,0)], Z_safe=np.nan, move_speed=0, verbose=False, **kwargs):
        self.xyz_bounds = [tuple(xyz_bounds[0]), tuple(xyz_bounds[1])]
        self.Z_safe = Z_safe
        self.cnc = None
        
        self.coordinates = (0,0,0)
        
        self.verbose = verbose
        self._port = port
        self._baudrate = None
        self._timeout = None
        # self._movement_speed = move_speed
        return

    def __delete__(self):
        self._shutdown()
        return

    def _connect(self, port, baudrate, timeout=None):
        """
        Establish serial connection to cnc controller.
        - port: serial port of cnc Arduino
        - baudrate: 
        - timeout:
        """
        self._port = port
        self._baudrate = baudrate
        self._timeout = timeout
        cnc = None
        try:
            cnc = serial.Serial(port, baudrate, timeout=timeout)
        except Exception as e:
            if self.verbose:
                print(e)
        self.cnc = cnc
        return
    
    def _shutdown(self):
        """
        Close serial connection
        """
        self.home()
        try:
            self.cnc.close()
        except Exception as e:
            if self.verbose:
                print(e)
        self.cnc = None
        return

    def connect(self):
        """
        Re-stablish serial connection to cnc controller using exisiting port and baudrate.
        """
        return self._connect(self._port, self._baudrate, self._timeout)

    def isConnected(self):
        if self.cnc == None:
            print(f"{self.__class__} ({self._port}) not connected.")
            return False
        return True
    
    def isFeasible(self, coord):
        """
        Checks if specified coordinates is a feasible position for robot to access.

        Args:
            coord (tuple): x,y,z coordinates

        Returns:
            bool: whether coordinates is a feaible position
        """
        l_bound, u_bound = np.array(self.xyz_bounds)
        coord = np.array(coord)
        if all(np.greater_equal(coord, l_bound)) and all(np.less_equal(coord, u_bound)):
            return True
        print(f"Range limits reached! {self.xyz_bounds}")
        return False

    def getPosition(self):
        """Get coordinates."""
        return self.coordinates, None
    
    def move(self, axis, displacement):
        """
        Move cnc in one axis and displacement
        - axis: X, Y, or Z
        - displacement: displacement in mm
        """
        axis = axis.upper()
        vector = (0,0,0)    
        if axis == 'X':
            vector = (displacement,0,0) 
        elif axis == 'Y':
            vector = (0,displacement,0) 
        elif axis =='Z':
            vector = (0,0,displacement) 
        return self.moveBy(vector, z_to_safe=True)

    def moveBy(self, vector, z_to_safe=True):
        """
        Move cnc in all axes and displacement
        - vector: vector in mm
        """
        new_coord = np.round( np.array(self.coordinates) + np.array(vector) , 2)
        return self.moveTo(new_coord, z_to_safe)
    
    def moveTo(self, coord, z_to_safe=True):
        """
        Move cnc to absolute position in 3D
        - coord: (X, Y, Z) coordinates of target
        """
        coord = np.array(coord)
        if not self.isFeasible(coord):
            return
        
        if z_to_safe and self.coordinates[2] < self.Z_safe:
            try:
                self.cnc.write(bytes("G90\n", 'utf-8'))
                print(self.cnc.readline())
                self.cnc.write(bytes(f"G0 Z{self.Z_safe}\n", 'utf-8'))
                print(self.cnc.readline())
                self.cnc.write(bytes("G90\n", 'utf-8'))
                print(self.cnc.readline())
            except Exception as e:
                if self.verbose:
                    print(e)
            self.updatePosition((*self.coordinates[0:2], self.Z_safe))
        
        z_first = True if self.coordinates[2]<coord[2] else False
        positionXY = f'X{coord[0]}Y{coord[1]}'
        position_Z = f'Z{coord[2]}'
        moves = [position_Z, positionXY] if z_first else [positionXY, position_Z]
        try:
            self.cnc.write(bytes("G90\n", 'utf-8'))
            print(self.cnc.readline())
            for move in moves:
                self.cnc.write(bytes(f"G0 {move}\n", 'utf-8'))
                print(self.cnc.readline())
            self.cnc.write(bytes("G90\n", 'utf-8'))
            print(self.cnc.readline())
        except Exception as e:
            if self.verbose:
                print(e)

        self.updatePosition(coord)
        return
    
    def updatePosition(self, coord=(0,), vector=(0,0,0)):
        """Update to current position"""
        if len(coord) == 1:
            new_coord = np.round( np.array(self.coordinates) + np.array(vector) , 2)
            self.coordinates = tuple(new_coord)
        else:
            self.coordinates = tuple(coord)
        print(f'{self.coordinates}')
        return
