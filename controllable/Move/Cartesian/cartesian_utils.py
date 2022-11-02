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
import serial.tools.list_ports

# Local application imports
print(f"Import: OK <{__name__}>")

class CNC(object):
    """
    Controller for cnc xyz-movements.
    - port: serial port of cnc Arduino
    """
    def __init__(self, xyz_bounds=[(0,0,0), (0,0,0)], Z_safe=np.nan, verbose=False, **kwargs):
        self.xyz_bounds = xyz_bounds
        self.Z_safe = Z_safe
        self.cnc = None
        
        self.current_x = 0
        self.current_y = 0
        self.current_z = 0
        
        self.verbose = verbose
        self._port = None
        self._baudrate = None
        self._timeout = None
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
        
        Return: serial.Serial object
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
        
        Return: serial.Serial object
        """
        return self._connect(self._port, self._baudrate, self._timeout)

    def heat(self):
        """EMPTY METHOD"""
        print(f"'{self.__class__.__name__}' class has no method 'heat'")
        return

    def home(self):
        """EMPTY METHOD"""
        print(f"'{self.__class__.__name__}' class has no method 'home'")
        return

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
        x, y, z = vector
        next_x = round(self.current_x + x, 2)
        next_y = round(self.current_y + y, 2)
        next_z = round(self.current_z + z, 2)
        next_pos = (next_x, next_y, next_z)
        return self.moveTo(next_pos, z_to_safe)
    
    def moveTo(self, coord, z_to_safe=True):
        """
        Move cnc to absolute position in 3D
        - coord: (X, Y, Z) coordinates of target
        """
        if z_to_safe and self.current_z < self.Z_safe:
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
            self.current_z = self.Z_safe
            print(f'{self.current_x}, {self.current_y}, {self.current_z}')
        
        x, y, z = coord
        z_first = True if self.current_z<z else False
        l_bound, u_bound = np.array(self.xyz_bounds)
        next_pos = np.array(coord)

        if all(np.greater_equal(next_pos, l_bound)) and all(np.less_equal(next_pos, u_bound)):
            pass
        else:
            print(f"Range limits reached! {self.xyz_bounds}")
            return

        positionXY = f'X{x}Y{y}'
        position_Z = f'Z{z}'
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

        self.current_x = x
        self.current_y = y
        self.current_z = z
        print(f'{self.current_x}, {self.current_y}, {self.current_z}')
        return
