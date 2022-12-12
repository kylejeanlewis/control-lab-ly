# %% -*- coding: utf-8 -*-
"""
Created: Tue 2022/11/01 17:13:35
@author: Chang Jie

Notes / actionables:
-
"""
# Standard library imports
import math
import numpy as np
import time

# Local application imports
from .. import RobotArm
from .dobot_api import dobot_api_dashboard, dobot_api_feedback, MyType
from . import dobot_attachments as attachments
print(f"Import: OK <{__name__}>")

SCALE = True
MOVE_TIME = 0.5

def decodeDetails(details):
    """
    Decode JSON representation of keyword arguments for Dobot initialisation

    Args:
        details (dict): dictionary of keyword, value pairs.
    """
    for k,v in details.items():
        if type(v) != dict:
            continue
        if "tuple" in v.keys():
            details[k] = tuple(v['tuple'])
        elif "array" in v.keys():
            details[k] = np.array(v['array'])
    return details


class Dobot(RobotArm):
    """
    Dobot class.

    Args:
        ip_address (str, optional): IP address of arm. Defaults to '192.168.2.8'.
        home_position (tuple, optional): position to home in arm coordinates. Defaults to (0,300,0).
        home_orientation (tuple, optional): orientation to home. Defaults to (0,0,0).
        orientate_matrix (numpy.matrix, optional): matrix to transform arm axes to workspace axes. Defaults to np.identity(3).
        translate_vector (numpy.array, optional): vector to transform arm position to workspace position. Defaults to np.zeros(3).
        scale (int, optional): scale factor to transform arm scale to workspace scale. Defaults to 1.
    """
    def __init__(self, ip_address='192.168.2.8', home_position=(0,300,0), home_orientation=(0,0,0), **kwargs):
        super().__init__(home_position, home_orientation, **kwargs)
        self.ip_address = ip_address
        self._dashboard = None
        self._feedback = None
        
        self.attachment = None

        self._connect(ip_address)
        self.home()
        pass
    
    def _connect(self, ip_address):
        """
        Connect to robot hardware.

        Args:
            ip_address (string): IP address of robot
        """
        try:
            self._dashboard = dobot_api_dashboard(ip_address, 29999)
            self._feedback = dobot_api_feedback(ip_address, 30003)

            self.reset()
            self._dashboard.User(0)
            self._dashboard.Tool(0)
            self.setSpeed(speed=100)
        except Exception as e:
            print(f"Unable to connect to arm at {ip_address}")
            print(e)
        return

    def _freeze(self):
        """Halt and disable robot."""
        try:
            self._dashboard.ResetRobot()
            self._dashboard.DisableRobot()
        except (AttributeError, OSError):
            print("Not connected to arm!")
        return
      
    def _shutdown(self):
        """Halt robot and close conenctions."""
        self._freeze()
        try:
            self._dashboard.close()
            self._feedback.close()
        except (AttributeError, OSError):
            print("Not connected to arm!")

        self._dashboard = None
        self._feedback = None
        return

    def attachmentOn(self, attach_type):
        if attach_type not in attachments.ATTACHMENT_LIST:
            raise Exception(f"Please select valid attachment from: {', '.join(attachments.ATTACHMENT_LIST)}")
        attach_class = getattr(attachments, attach_type)
        self.attachment = attach_class(self._dashboard)
        self.implement_offset = self.attachment.implement_offset
        self.home()
        return
    
    def attachmentOff(self):
        self.attachment = None
        self.implement_offset = (0,0,0)
        self.home()
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
        super().calibrate(external_pt1, internal_pt1, external_pt2, internal_pt2)

        # Verify calibrated points
        for pt in [external_pt1, external_pt2]:
            self.home()
            self.moveTo( tuple(np.append(pt[:2],10)) )
            input("Press Enter to verify reference point")
        self.home()
        return

    def calibrationMode(self, on, tip_length=21):
        """
        Enter into calibration mode, with a sharp point implement for alignment.

        Args:
            on (bool): whether to activate calibration mode
            tip_length (int, optional): length of sharp point alignment implement. Defaults to 21.
        """
        if on:
            tip_length = int(input(f"Please swap to calibration tip and enter tip length in mm (Default: {tip_length}mm)") or str(tip_length))
            self.tool_offset = self.implement_offset
            self.setImplementOffset((0,0,tip_length))
        else:
            input("Please swap back to original tool")
            self.setImplementOffset(self.tool_offset)
            del self.tool_offset
        return
    
    def getSettings(self):
        """Read the arm configuration settings."""
        params = ["ip_address", "home_position", "home_orientation", "orientate_matrix", "translate_vector", "scale"]
        return super().getSettings(params)
    
    def home(self):
        """Home the robot arm."""
        # Tuck arm in to avoid collision
        if self._flags['tuck']:
            self.tuckArm(self.home_position)
        # Go to home position
        self.moveCoordTo(self.home_position, self.home_orientation)
        print("Homed")
        return

    def isFeasible(self, coord):
        """
        Checks if specified coordinates is a feasible position for robot to access.

        Args:
            coord (tuple): x,y,z coordinates

        Returns:
            bool: whether coordinates is a feasible position
        """
        return True
    
    def isConnected(self):
        if any([True for connect in (self._dashboard, self._feedback) if connect==None]):
            print(f"{self.__class__} ({self.ip_address}) not connected.")
            return False
        return True
    
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
        return self.moveBy(vector)

    def moveBy(self, vector, angles=(0,0,0), **kwargs):
        """
        Relative Cartesian movement, using workspace coordinates.

        Args:
            vector (tuple): displacement vector
            angles (tuple, optional): rotation angles in degrees. Defaults to (0,0,0).
        """
        vector = self._transform_vector_in(vector)
        return self.moveCoordBy(vector, angles)

    def moveTo(self, coord, orientation=(0,), tuck=False, **kwargs):
        """
        Absolute Cartesian movement, using workspace coordinates.

        Args:
            coord (tuple): position vector
            orientation (tuple, optional): orientation angles in degrees. Defaults to (0,).
            tuck (bool, optional): whether to tuck arm in. Defaults to False.
        """
        if len(orientation) == 1 and orientation[0] == 0:
            orientation = self.orientation
        coord = self._transform_vector_in(coord, offset=True)
        if self._flags['tuck'] and tuck:
            self.tuckArm(coord)
        return self.moveCoordTo(coord, orientation)

    def moveJointBy(self, relative_angle=(0,0,0,0,0,0)):
        """
        Relative joint movement.

        Args:
            relative_angle (tuple, optional): rotation angles in degrees. Defaults to (0,0,0,0,0,0).
        """
        relative_angle = relative_angle + (0,) * (6-len(relative_angle))
        try:
            self._feedback.RelMovJ(*relative_angle)
            time.sleep(MOVE_TIME)
        except (AttributeError, OSError):
            print("Not connected to arm!")
        return

    def moveJointTo(self, absolute_angle=(0,0,0,0,0,0)):
        """
        Absolute joint movement.

        Args:
            absolute_angle (tuple, optional): orientation angles in degrees. Defaults to (0,0,0,0,0,0).
        """
        absolute_angle = absolute_angle + (0,) * (6-len(absolute_angle))
        try:
            self._feedback.JointMovJ(*absolute_angle)
            time.sleep(MOVE_TIME)
        except (AttributeError, OSError):
            print("Not connected to arm!")
        return

    def moveCoordBy(self, vector=(0,0,0), angles=(0,0,0)):
        """
        Relative Cartesian movement and tool orientation, using robot coordinates.

        Args:
            vector (tuple, optional): displacement vector. Defaults to (0,0,0).
            angles (tuple, optional): rotation angles in degrees. Defaults to (0,0,0).
        """
        try:
            self._feedback.RelMovL(*vector)
            time.sleep(MOVE_TIME)
        except (AttributeError, OSError):
            print("Not connected to arm!")
        
        # Rotate to orientation
        if any(angles):
            self.moveJointBy((0,0,0,*angles))

        # Update values
        self.updatePosition(vector=vector, angles=angles)
        return

    def moveCoordTo(self, coord, orientation=(0,), offset=True):
        """
        Absolute Cartesian movement and tool orientation, using robot coordinates.

        Args:
            coord (tuple): position vector
            orientation (tuple, optional): orientatino angles in degrees. Defaults to (0,).
            offset (bool, optional): whether to consider implement offset. Defaults to True.
        """
        if len(orientation) == 1 and orientation[0] == 0:
            orientation = self.orientation
        absolute_arm_coord = tuple(np.array(coord) + np.array(self.implement_offset)) if offset else coord
        if not self.isFeasible(absolute_arm_coord):
            print(f"Infeasible coordinates! {absolute_arm_coord}")
            return
        
        try:
            self._feedback.MovJ(*absolute_arm_coord, *orientation)
            time.sleep(MOVE_TIME)
        except (AttributeError, OSError):
            print("Not connected to arm!")
        
        # Update values
        self.updatePosition(coord, orientation)
        return

    def reset(self):
        """Clear any errors and enable robot."""
        try:
            self._dashboard.ClearError()
            self._dashboard.EnableRobot()
        except (AttributeError, OSError):
            print("Not connected to arm!")
        return

    def rotateBy(self, angles):
        """
        Relative tool orientation.

        Args:
            angles (tuple): rotation angles in degrees
        """
        return self.moveCoordBy(angles=angles)

    def rotateTo(self, orientation):
        """
        Absolute tool orientation.

        Args:
            orientation (tuple): orientation angles in degrees
        """
        return self.moveCoordTo(self.coordinates, orientation)
    
    def setImplementOffset(self, implement_offset):
        """
        Set offset of implement.

        Args:
            implement_offset (tuple): x,y,z offset of implement
        """
        self.implement_offset = implement_offset
        self.home()
        return

    def setPosition(self, coord):
        """
        Set robot coordinates.

        Args:
            coord (tuple): x,y,z workspace coordinates
        """
        self.coordinates = self._transform_vector_in(coord, offset=True, stretch=SCALE)
        return

    def setSpeed(self, speed):
        """
        Setting the Global speed rate.

        Args:
            speed (int): rate value (value range: 1~100)
        """
        try:
            self._dashboard.SpeedFactor(speed)
        except (AttributeError, OSError):
            print("Not connected to arm!")
        return

    def tuckArm(self, target=None):
        """
        Tuck in arm, rotate about base, then extend again.

        Args:
            target (tuple, optional): x,y,z coordinates of destination. Defaults to None.
        """
        return


class MG400(Dobot):
    """
    MG400 class.

    Args:
        ip_address (str, optional): IP address of arm. Defaults to '192.168.2.8'.
        home_position (tuple, optional): position to home in arm coordinates. Defaults to (0,300,0).
        home_orientation (tuple, optional): orientation to home. Defaults to (0,0,0).
        orientate_matrix (numpy.matrix, optional): matrix to transform arm axes to workspace axes. Defaults to np.identity(3).
        translate_vector (numpy.array, optional): vector to transform arm position to workspace position. Defaults to np.zeros(3).
        scale (int, optional): scale factor to transform arm scale to workspace scale. Defaults to 1.
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        return
    
    def isFeasible(self, coord):
        """
        Checks if specified coordinates is a feasible position for robot to access.

        Args:
            coord (tuple): x,y,z coordinates

        Returns:
            bool: whether coordinates is a feasible position
        """
        x,y,z = coord
        j1 = round(math.degrees(math.atan(x/(y + 1E-6))), 3)
        if y < 0:
            j1 += (180 * math.copysign(1, x))
        if abs(j1) > 160:
            return False
        if not (-150 < z < 230):
            return False
        return True
    
    def tuckArm(self, target=None):
        """
        Tuck in arm, rotate about base, then extend again.

        Args:
            target (tuple, optional): x,y,z coordinates of destination. Defaults to None.
        """
        safe_radius = 225
        safe_height = 75
        coordinates,_ = self.getPosition()
        x,y,_ = coordinates
        if any((x,y)):
            w = ( (safe_radius**2)/(x**2 + y**2) )**0.5
            x,y = (x*w,y*w)
        else:
            x,y = (0,safe_radius)
        self.moveCoordTo((x,y,safe_height), self.orientation, offset=False)

        if type(target) != type(None) and len(target) == 3:
            x1,y1,_ = target
            w1 = ( (safe_radius**2)/(x1**2 + y1**2) )**0.5
            self.moveCoordTo((x1*w1,y1*w1,75), self.orientation, offset=False)
        return

class M1Pro(Dobot):
    """
    M1 Pro class.

    Args:
        ip_address (str, optional): IP address of arm. Defaults to '192.168.2.8'.
        home_position (tuple, optional): position to home in arm coordinates. Defaults to (0,300,0).
        home_orientation (tuple, optional): orientation to home. Defaults to (0,0,0).
        orientate_matrix (numpy.matrix, optional): matrix to transform arm axes to workspace axes. Defaults to np.identity(3).
        translate_vector (numpy.array, optional): vector to transform arm position to workspace position. Defaults to np.zeros(3).
        scale (int, optional): scale factor to transform arm scale to workspace scale. Defaults to 1.
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._handedness = ''
        
        self.setHandedness('left')
        return
    
    def isFeasible(self, coord):
        """
        Checks if specified coordinates is a feasible position for robot to access.

        Args:
            coord (tuple): x,y,z coordinates

        Returns:
            bool: whether coordinates is a feasible position
        """
        x,y,z = coord
        
        if not (5 < z < 245):
            return False
        
        if x >= 0:
            r = (x**2 + y**2)**0.5
            if not (153 <= r <= 400):
                return False
        elif abs(y) < 230/2:
            return False
        elif (x**2 + (abs(y)-200)**2)**0.5 > 200:
            return False
        
        # x=4, y=3
        grad = abs(y/(x+1E-6))
        if grad > 0.75 or x < 0:
            hand = 'right' if y>0 else 'left'
            self.setHandedness(hand, stretch=True)
        return True
    
    def moveBy(self, vector, angles=(0, 0, 0), **kwargs):
        vector = self._transform_vector_in(vector)
        coord, orientation = self.getPosition()
        new_coord = np.array(coord) + np.array(vector)
        new_orientation = np.array(orientation) + np.array(angles)
        return self.moveTo(tuple(new_coord), tuple(new_orientation))

    def setHandedness(self, hand, stretch=False):
        set_hand = False
        if hand not in ['left','right']:
            raise Exception("Please select between 'left' or 'right'")
        if hand == 'left' and self._handedness != 'left': #0
            self._dashboard.SetArmOrientation(0,1,1,1)
            self._handedness = 'left'
            set_hand = True
        elif hand == 'right' and self._handedness != 'right': #1
            self._dashboard.SetArmOrientation(1,1,1,1)
            self._handedness = 'right'
            set_hand = True
        if set_hand and stretch:
            self.stretchArm()
        return
            
    def stretchArm(self):
        x,y,z = self.coordinates
        y = 240 * math.copysign(1, y)
        self.moveTo((320,y,z))
        time.sleep(MOVE_TIME)
        return
    