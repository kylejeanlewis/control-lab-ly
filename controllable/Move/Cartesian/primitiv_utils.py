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
    def __init__(self, port, xyz_bounds=[(-410,-290,-120), (0,0,0)], Z_safe=-80, Z_updown=(-94,-104), **kwargs):
        super().__init__(xyz_bounds, Z_safe, **kwargs)
        self.Z_up, self.Z_down = Z_updown
        self.selected_position = ''
        
        self._connect(port)
        self.home()
        return
    
    def _connect(self, port):
        """
        Establish serial connection to cnc controller.
        - port: serial port of cnc Arduino

        Return: serial.Serial object
        """
        super()._connect(port, 115200, timeout=1)
        cnc= self.cnc
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
        return
    
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
        
        self.updatePosition((0,0,0))
        return

# %%
