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

CNC_SPEED = 250

class Cartesian(Mover):
    """
    Cartesian controls

    Args:
        xyz_bounds (list, optional): lower and upper bounds of movement. Defaults to [(0,0,0), (0,0,0)].
        Z_safe (float, optional): safe height. Defaults to np.nan.
        move_speed (float, optional): movement speed. Defaults to 0.
        verbose (bool, optional): whether to print outputs. Defaults to False.
    """
    def __init__(self, xyz_bounds=[(0,0,0), (0,0,0)], Z_safe=None, move_speed=0, implement_offset=(0,0,0), verbose=False, **kwargs):
        self.xyz_bounds = [tuple(xyz_bounds[0]), tuple(xyz_bounds[1])]
        self.mcu = None
        self.heights = {
            'safe': Z_safe
        }
        
        self.implement_offset = implement_offset
        self.coordinates = (0,0,0)
        self.orientation = (0,0,0)
        
        self.verbose = verbose
        self._flags = {}
        
        self._port = ''
        self._baudrate = None
        self._timeout = None
        # self._movement_speed = move_speed
        return

    def __delete__(self):
        self._shutdown()
        return

    def calibrate(self, external_pt1, internal_pt1, external_pt2, internal_pt2):
        """
        Calibrate internal and external coordinate systems.

        Args:
            external_pt1 (tuple): x,y,z coordinates of physical point 1
            internal_pt1 (tuple): x,y,z coordinates of robot point 1
            external_pt2 (tuple): x,y,z coordinates of physical point 2
            internal_pt2 (tuple): x,y,z coordinates of robot point 2
        """
        space_vector = external_pt2 - external_pt1
        robot_vector = internal_pt2 - internal_pt1
        space_mag = np.linalg.norm(space_vector)
        robot_mag = np.linalg.norm(robot_vector)

        space_unit_vector = space_vector / space_mag
        robot_unit_vector = robot_vector / robot_mag
        dot_product = np.dot(robot_unit_vector, space_unit_vector)
        cross_product = np.cross(robot_unit_vector, space_unit_vector)

        cos_theta = dot_product
        sin_theta = math.copysign(np.linalg.norm(cross_product), cross_product[2])
        rot_angle = math.acos(cos_theta) if sin_theta>0 else 2*math.pi - math.acos(cos_theta)
        rot_matrix = np.array([[cos_theta,-sin_theta,0],[sin_theta,cos_theta,0],[0,0,1]])
        
        self.orientate_matrix = rot_matrix
        self.translate_vector = (external_pt1 - internal_pt1)
        self.scale = (space_mag / robot_mag)
        
        print(f'Orientate matrix:\n{self.orientate_matrix}')
        print(f'Translate vector: {self.translate_vector}')
        print(f'Scale factor: {self.scale}')
        print(f'Offset angle: {rot_angle/math.pi*180} degree')
        print(f'Offset vector: {(external_pt1 - internal_pt1)}')
        return
    
    def getConfigSettings(self, params:list):
        """
        Read the arm configuration settings.
        
        Args:
            params (list): list of attributes to retrieve values from
        
        Returns:
            dict: dictionary of arm class and details/attributes
        """
        arm = str(type(self)).split("'")[1].split('.')[1]
        details = {k: v for k,v in self.__dict__.items() if k in params}
        for k,v in details.items():
            if type(v) == tuple:
                details[k] = {"tuple": list(v)}
            elif type(v) == np.ndarray:
                details[k] = {"array": v.tolist()}
        settings = {"arm": arm, "details": details}
        return settings

    def getPosition(self):
        """Get coordinates."""
        return self.coordinates, (0,0,0)
    
    def getToolPosition(self):
        """
        Retrieve coordinates of tool tip/end of implement.

        Returns:
            tuple, tuple: x,y,z coordinates; a,b,g angles
        """
        return self.getPosition()
    
    def getUserPosition(self):
        """
        Retrieve user-defined workspace coordinates.

        Returns:
            tuple, tuple: x,y,z coordinates; a,b,g angles
        """
        return self.getPosition()
    
    def getWorkspacePosition(self):
        return self.getUserPosition()
    
    def setImplementOffset(self, implement_offset):
        """
        Set offset of implement.

        Args:
            implement_offset (tuple): x,y,z offset of implement (i.e. vector pointing from end of effector to tooltip)
        """
        self.implement_offset = tuple(implement_offset)
        self.home()
        return
    
    def setPosition(self, coord):
        """
        Set robot coordinates.

        Args:
            coord (tuple): x,y,z workspace coordinates
        """
        self.coordinates = self._transform_vector_in(coord, offset=True, stretch=True)
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


class CNC(Cartesian):
    def __init__(self, xyz_bounds=[(0, 0, 0), (0, 0, 0)], Z_safe=None, move_speed=0, implement_offset=(0, 0, 0), verbose=False, **kwargs):
        super().__init__(xyz_bounds, Z_safe, move_speed, implement_offset, verbose, **kwargs)
        return
    
    def _connect(self, port, baudrate, timeout=None):
        """
        Connect to machine control unit

        Args:
            port (str): com port address
            baudrate (int): baudrate
            timeout (int, optional): timeout in seconds. Defaults to None.
        """
        self._port = port
        self._baudrate = baudrate
        self._timeout = timeout
        mcu = None
        try:
            mcu = serial.Serial(port, baudrate, timeout=timeout)
            print(f"Connection opened to {port}")
        except Exception as e:
            if self.verbose:
                print(e)
        self.mcu = mcu
        return
    
    def _shutdown(self):
        """
        Close serial connection
        """
        self.home()
        try:
            self.mcu.close()
        except Exception as e:
            if self.verbose:
                print(e)
        self.mcu = None
        return

    def connect(self):
        """
        Re-stablish serial connection to cnc controller using existing port and baudrate.
        """
        return self._connect(self._port, self._baudrate, self._timeout)

    def isConnected(self):
        """
        Check whether machine control unit is connected

        Returns:
            bool: whether machine control unit is connected
        """
        if self.mcu == None:
            print(f"{self.__class__} ({self._port}) not connected.")
            return False
        return True
    
    def isFeasible(self, coord, transform=False):
        """
        Checks if specified coordinates is a feasible position for robot to access.

        Args:
            coord (tuple): x,y,z coordinates

        Returns:
            bool: whether coordinates is a feasible position
        """
        l_bound, u_bound = np.array(self.xyz_bounds)
        coord = np.array(coord)
        if all(np.greater_equal(coord, l_bound)) and all(np.less_equal(coord, u_bound)):
            return True
        print(f"Range limits reached! {self.xyz_bounds}")
        return False

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

    def moveBy(self, vector, z_to_safe=True, **kwargs):
        """
        Move cnc in all axes and displacement
        - vector: vector in mm
        """
        new_coord = np.round( np.array(self.coordinates) + np.array(vector) , 2)
        return self.moveTo(new_coord, z_to_safe)
    
    def moveTo(self, coord, z_to_safe=True, jump_z_height=None, **kwargs):
        """
        Move cnc to absolute position in 3D
        - coord: (X, Y, Z) coordinates of target
        """
        coord = np.array(coord)
        if not self.isFeasible(coord):
            return
        if jump_z_height == None:
            jump_z_height = self.heights['safe']
        if z_to_safe and self.coordinates[2] < jump_z_height:
            try:
                self.mcu.write(bytes("G90\n", 'utf-8'))
                print(self.mcu.readline())
                self.mcu.write(bytes(f"G0 Z{jump_z_height}\n", 'utf-8'))
                print(self.mcu.readline())
                self.mcu.write(bytes("G90\n", 'utf-8'))
                print(self.mcu.readline())
            except Exception as e:
                if self.verbose:
                    print(e)
            self.updatePosition((*self.coordinates[0:2], jump_z_height))
        
        z_first = True if self.coordinates[2]<coord[2] else False
        positionXY = f'X{coord[0]}Y{coord[1]}'
        position_Z = f'Z{coord[2]}'
        moves = [position_Z, positionXY] if z_first else [positionXY, position_Z]
        try:
            self.mcu.write(bytes("G90\n", 'utf-8'))
            print(self.mcu.readline())
            for move in moves:
                self.mcu.write(bytes(f"G0 {move}\n", 'utf-8'))
                print(self.mcu.readline())
            self.mcu.write(bytes("G90\n", 'utf-8'))
            print(self.mcu.readline())
        except Exception as e:
            if self.verbose:
                print(e)

        self.updatePosition(coord)
        return
    