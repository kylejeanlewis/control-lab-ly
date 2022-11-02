# %% -*- coding: utf-8 -*-
"""
Created: Tue 2022/11/01 17:13:35
@author: Chang Jie

Notes / actionables:
-
"""
# Standard library imports
import time

# Local application imports
from . import CNC
print(f"Import: OK <{__name__}>")

class Primitiv(CNC):
    """
    XYZ controls for Primitiv platform.
    - port: serial port of cnc Arduino
    - xyz_bounds: range of motion of tool
    """
    def __init__(self, port, xyz_bounds=[(-410,-290,-120), (0,0,0)], Z_safe=-80, Z_updown=(-94,-104), verbose=False):
        super().__init__(port, xyz_bounds, Z_safe, verbose)
        self.Z_up, self.Z_down = Z_updown
        self.selected_position = ''
        
        self.cnc = self._connect(port)
        return
    
    def _connect(self, port):
        """
        Establish serial connection to cnc controller.
        - port: serial port of cnc Arduino

        Return: serial.Serial object
        """
        cnc = super()._connect(port, 115200, timeout=1)
        try:
            cnc.close()
            cnc.open()

            # Start grbl 
            cnc.write(bytes("\r\n\r\n", 'utf-8'))
            time.sleep(2)
            cnc.flushInput()
        except Exception as e:
            if self.verbose:
                print(e)
        self.home()
        print("CNC ready")
        return cnc
    
    def home(self):
        """
        Homing cycle for Primitiv platform
        """
        try:
            self.cnc.write(bytes("$H\n", 'utf-8'))
            print(self.cnc.readline())
        except Exception as e:
            if self.verbose:
                print(e)
        
        self.current_x = 0
        self.current_y = 0
        self.current_z = 0
        print(f'{self.current_x}, {self.current_y}, {self.current_z}')
        return

# %%
