# %% -*- coding: utf-8 -*-
"""
Created: Tue 2022/11/01 17:13:35
@author: Chang Jie

Notes / actionables:
-
"""
# Local application imports
from .cartesian_utils import Gantry
print(f"Import: OK <{__name__}>")

class Ender(Gantry):
    """
    Ender platform controls

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
    def __init__(self, port:str, limits=[(0,0,0), (240,235,210)], safe_height=30, **kwargs):
        super().__init__(port=port, limits=limits, safe_height=safe_height, **kwargs)
        return
    
    def _connect(self, port:str, baudrate=115200, timeout=None):
        """
        Connect to machine control unit

        Args:
            port (str): com port address
            baudrate (int): baudrate. Defaults to 115200.
            timeout (int, optional): timeout in seconds. Defaults to None.
            
        Returns:
            serial.Serial: serial connection to machine control unit if connection is successful, else None
        """
        self.port = port
        self._baudrate = baudrate
        self._timeout = timeout
        return super()._connect(self.port, self._baudrate, self._timeout)

    def heat(self, bed_temperature):
        """
        Heat bed to temperature

        Args:
            bed_temperature (int, or float): temperature of platform

        Returns:
            bool: whether setting bed temperature was successful
        """
        bed_temperature = round( min(max(bed_temperature,0), 110) )
        try:
            self.device.write(bytes(f'M140 S{bed_temperature}\n', 'utf-8'))
        except Exception as e:
            print('Unable to heat stage!')
            if self.verbose:
                print(e)
            return False
        return True

    def home(self):
        """
        Homing cycle for Ender platform
        """
        try:
            self.device.write(bytes("G90\n", 'utf-8'))
            print(self.device.readline())
            self.device.write(bytes(f"G0 Z{self.heights['safe']}\n", 'utf-8'))
            print(self.device.readline())
            self.device.write(bytes("G90\n", 'utf-8'))
            print(self.device.readline())

            self.device.write(bytes("G28\n", 'utf-8'))

            self.device.write(bytes("G90\n", 'utf-8'))
            print(self.device.readline())
            self.device.write(bytes(f"G0 Z{self.heights['safe']}\n", 'utf-8'))
            print(self.device.readline())
            self.device.write(bytes("G90\n", 'utf-8'))
            print(self.device.readline())
        except Exception as e:
            if self.verbose:
                print(e)
        
        self.coordinates = (0,0,self.heights['safe'])
        try:
            self.device.write(bytes("G1 F10000\n", 'utf-8'))
            print(self.device.readline())
        except Exception as e:
            if self.verbose:
                print(e)
        return
