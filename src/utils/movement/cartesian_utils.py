# %%
# -*- coding: utf-8 -*-
"""
Created on Fri 2022/03/18 09:00:00

@author: Chang Jie
"""
import time
import numpy as np
import serial
import serial.tools.list_ports
print(f"Import: OK <{__name__}>")

# %%
class CNC(object):
    """
    Controller for cnc xyz-movements.
    - address: serial address of cnc Arduino
    """
    def __init__(self, address):
        self.address = address
        self.current_x = 0
        self.current_y = 0
        self.current_z = 0
        self.space_range = [(0,0,0), (0,0,0)]
        self.Z_safe = np.nan
        self.cnc = None
        return

    def __delete__(self):
        self.shutdown()
        return

    def connect(self, address):
        return

    def home(self):
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
            except:
                pass
            self.current_z = self.Z_safe
            print(f'{self.current_x}, {self.current_y}, {self.current_z}')
        
        x, y, z = coord
        z_first = True if self.current_z<z else False
        l_bound, u_bound = np.array(self.space_range)
        next_pos = np.array(coord)

        if all(np.greater_equal(next_pos, l_bound)) and all(np.less_equal(next_pos, u_bound)):
            pass
        else:
            print(f"Range limits reached! {self.space_range}")
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
        except:
            pass

        self.current_x = x
        self.current_y = y
        self.current_z = z
        print(f'{self.current_x}, {self.current_y}, {self.current_z}')
        return

    def shutdown(self):
        self.home()
        try:
            self.cnc.close()
        except:
            pass
        self.cnc = None
        return


class Ender(CNC):
    """
    XYZ controls for Ender platform.
    - address: serial address of cnc Arduino
    - space_range: range of motion of tool
    """
    def __init__(self, address, space_range=[(0,0,0), (240,235,210)], Z_safe=30):
        super().__init__(address)
        self.cnc = self.connect(address)
        self.space_range = space_range
        self.Z_safe = Z_safe
        self.home()
        return
    
    def connect(self, address):
        """
        Establish serial connection to cnc controller.
        - address: port address

        Return: serial.Serial object
        """
        cnc = None
        try:
            cnc = serial.Serial(address, 115200)
        except Exception as e:
            print(e)
            pass
        return cnc

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
            print(e)
            bed_temp = np.nan
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
        except:
            pass
        self.current_x = 0
        self.current_y = 0
        self.current_z = self.Z_safe
        try:
            self.cnc.write(bytes("G1 F10000\n", 'utf-8'))
            print(self.cnc.readline())
        except:
            pass
        return

    
class Primitiv(CNC):
    """
    XYZ controls for Primitiv platform.
    - address: serial address of cnc Arduino
    - space_range: range of motion of tool
    """
    def __init__(self, address, space_range=[(-410,-290,-120), (0,0,0)], Z_safe=-80, Z_updown=(-94,-104)):
        super().__init__(address)
        self.cnc = self.connect(address)
        self.space_range = space_range
        self.selected_position = ''
        self.Z_safe = Z_safe
        self.Z_up, self.Z_down = Z_updown
        return
    
    def connect(self, address):
        """
        Establish serial connection to cnc controller.
        - address: port address

        Return: serial.Serial object
        """
        cnc = None
        try:
            cnc = serial.Serial(address, 115200, timeout=1) 
            cnc.close()
            cnc.open()

            # Start grbl 
            cnc.write(bytes("\r\n\r\n", 'utf-8'))
            time.sleep(2)
            cnc.flushInput()

            # Homing cycle
            cnc.write(bytes("$H\n", 'utf-8'))
            print(cnc.readline())
            print("CNC ready")
        except:
            pass
        return cnc
    
    def home(self):
        """XYZ-zero"""
        try:
            self.cnc.write(bytes("$H\n", 'utf-8'))
            print(self.cnc.readline())
        except:
            pass
        
        self.current_x = 0
        self.current_y = 0
        self.current_z = 0
        print(f'{self.current_x}, {self.current_y}, {self.current_z}')
