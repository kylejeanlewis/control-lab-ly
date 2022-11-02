# %% -*- coding: utf-8 -*-
"""
Created: Tue 2022/11/01 17:13:35
@author: Chang Jie

Notes / actionables:
-
"""
# Local application imports
from . import CNC
print(f"Import: OK <{__name__}>")

class Ender(CNC):
    """
    XYZ controls for Ender platform.
    - port: serial port of cnc Arduino
    - xyz_bounds: range of motion of tool
    """
    def __init__(self, port, xyz_bounds=[(0,0,0), (240,235,210)], Z_safe=30, verbose=False, **kwargs):
        super().__init__(xyz_bounds, Z_safe, verbose, **kwargs)
        
        self._connect(port)
        self.home()
        return
    
    def _connect(self, port):
        """
        Establish serial connection to cnc controller.
        - port: serial port of cnc Arduino
        
        Return: serial.Serial object
        """
        return super()._connect(port, 115200)

    def heat(self, bed_temp):
        """
        Heat bed to temperature
        - bed_temp: bed temperature

        Return: bed_temp
        """
        bed_temp = round( min(max(bed_temp,0), 110) )
        try:
            self.cnc.write(bytes('M140 S{}\n'.format(bed_temp), 'utf-8'))
        except Exception as e:
            print('Unable to heat stage!')
            if self.verbose:
                print(e)
            bed_temp = 0
        return bed_temp

    def home(self):
        """
        Homing cycle for Ender platform
        """
        try:
            self.cnc.write(bytes("G90\n", 'utf-8'))
            print(self.cnc.readline())
            self.cnc.write(bytes("G0 " + f"Z{self.Z_safe}" + "\n", 'utf-8'))
            print(self.cnc.readline())
            self.cnc.write(bytes("G90\n", 'utf-8'))
            print(self.cnc.readline())

            self.cnc.write(bytes("G28\n", 'utf-8'))

            self.cnc.write(bytes("G90\n", 'utf-8'))
            print(self.cnc.readline())
            self.cnc.write(bytes("G0 " + f"Z{self.Z_safe}" + "\n", 'utf-8'))
            print(self.cnc.readline())
            self.cnc.write(bytes("G90\n", 'utf-8'))
            print(self.cnc.readline())
        except Exception as e:
            if self.verbose:
                print(e)
        
        self.updatePosition((0,0,self.Z_safe))
        try:
            self.cnc.write(bytes("G1 F10000\n", 'utf-8'))
            print(self.cnc.readline())
        except Exception as e:
            if self.verbose:
                print(e)
        return

# %%
