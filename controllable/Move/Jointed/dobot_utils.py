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
import os
import sys
import time

# Local application imports
from . import RobotArm
from .Dobot.dobot_api import dobot_api_dashboard, dobot_api_feedback, MyType
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
    def __init__(self, ip_address='192.168.2.8', home_position=(0,300,0), home_orientation=(0,0,0), orientate_matrix=np.identity(3), translate_vector=np.zeros(3), scale=1, **kwargs):
        super().__init__(home_position, home_orientation, orientate_matrix, translate_vector, scale, **kwargs)
        self._ip_address = ip_address
        self._dashboard = None
        self._feedback = None

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
        arm = str(type(self)).split("'")[1].split('.')[1]
        param = ["ip_address", "home_position", "home_orientation", "orientate_matrix", "translate_vector", "scale"]
        details = {k: v for k,v in self.__dict__.items() if k in param}
        for k,v in details.items():
            if type(v) == tuple:
                details[k] = {"tuple": list(v)}
            elif type(v) == np.ndarray:
                details[k] = {"array": v.tolist()}
        settings = {"arm": arm, "details": details}
        return settings
    
    def getWorkspacePosition(self, offset=True):
        """
        Retrieve physcial coordinates.

        Args:
            offset (bool, optional): whether to consider offset of implement. Defaults to True.

        Returns:
            tuple: position vector
        """
        return self._transform_vector_out(self.getPosition(), offset=offset)

    def home(self):
        """Home the robot arm."""
        # Tuck arm in to avoid collision
        self.tuck(self.home_position)
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
            bool: whether coordinates is a feaible position
        """
        coord = tuple(np.array(coord) + np.array(self.implement_offset))
        x,y,z = coord

        j1 = round(math.degrees(math.atan(x/(y + 1E-6))), 3)
        if y < 0:
            j1 += (180 * math.copysign(1, x))
        if abs(j1) > 160:
            return False

        # if not -150 < z < 230:
        #     return False
        return True

    def moveBy(self, vector, angles=(0,0,0)):
        """
        Relative Cartesian movement, using workspace coordinates.

        Args:
            vector (tuple): displacement vector
            angles (tuple, optional): rotation angles in degrees. Defaults to (0,0,0).
        """
        vector = self._transform_vector_in(vector)
        return self.moveCoordBy(vector, angles)

    def moveTo(self, coord, orientation=(0,), tuck=False):
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
        if tuck:
            self.tuck(coord)
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

    def moveCoordBy(self, relative_coord=(0,0,0), orientation=(0,0,0)):
        """
        Relative Cartesian movement and tool orientation, using robot coordinates.

        Args:
            relative_coord (tuple, optional): displacement vector. Defaults to (0,0,0).
            orientation (tuple, optional): rotation angles in degrees. Defaults to (0,0,0).
        """
        try:
            self._feedback.RelMovL(*relative_coord)
            time.sleep(MOVE_TIME)
        except (AttributeError, OSError):
            print("Not connected to arm!")
        
        # Rotate to orientation
        if any(orientation):
            self.moveJointBy((0,0,0,*orientation))

        # Update values
        self.current_x += relative_coord[0]
        self.current_y += relative_coord[1]
        self.current_z += relative_coord[2]
        self.coordinates = (self.current_x, self.current_y, self.current_z)
        self.orientation = tuple(np.array(orientation) + np.array(self.orientation))
        return

    def moveCoordTo(self, absolute_coord, orientation=(0,), offset=True):
        """
        Absolute Cartesian movement and tool orientation, using robot coordinates.

        Args:
            absolute_coord (tuple): position vector
            orientation (tuple, optional): orientatino angles in degrees. Defaults to (0,).
            offset (bool, optional): whether to consider implement offset. Defaults to True.
        """
        if len(orientation) == 1 and orientation[0] == 0:
            orientation = self.orientation
        absolute_arm_coord = tuple(np.array(absolute_coord) + np.array(self.implement_offset)) if offset else absolute_coord
        if not self.isFeasible(absolute_arm_coord):
            print(f"Infeasible coordinates! {absolute_arm_coord}")
            return
        
        try:
            self._feedback.MovJ(*absolute_arm_coord, *orientation)
            time.sleep(MOVE_TIME)
        except (AttributeError, OSError):
            print("Not connected to arm!")
        
        # Update values
        self.current_x, self.current_y, self.current_z = absolute_coord
        self.coordinates = absolute_coord
        self.orientation = orientation
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
        return self.moveCoordBy(orientation=angles)

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

    def tuck(self, target=None):
        """
        Tuck in arm, rotate about base, then extend again.

        Args:
            target (tuple, optional): x,y,z coordinates of destination. Defaults to None.
        """
        safe_radius = 225
        safe_height = 75
        x,y,_ = self.getPosition()
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

# First-party implement attachments
class JawGripper(Dobot):
    """
    JawGripper class.
    
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
        self.implement_offset = (0,0,95)
        self.home()
        return

    def drop(self):
        """Open gripper"""
        try:
            self._dashboard.DOExecute(1,1)
        except (AttributeError, OSError):
            print("Not connected to arm!")
        return
    
    def grab(self):
        """Close gripper"""
        try:
            self._dashboard.DOExecute(1,0)
        except (AttributeError, OSError):
            print("Not connected to arm!")
        return


class VacuumGrip(Dobot):
    """
    VacuumGrip class.

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
        self.implement_offset = (0,0,60)
        self.home()
        return

    def blow(self, duration=0):
        """
        Expel air.

        Args:
            duration (int, optional): number of seconds to expel air. Defaults to 0.
        """
        try:
            self._dashboard.DOExecute(2,1)
            if duration > 0:
                time.sleep(duration)
                self._dashboard.DOExecute(2,0)
                time.sleep(1)
        except (AttributeError, OSError):
            print("Not connected to arm!")
        return

    def drop(self):
        """Let go of object."""
        self.blow(0.5)
        return
    
    def grab(self):
        """Pick up object."""
        self.suck(3)
        return
    
    def stop(self):
        """Stop airflows."""
        try:
            self._dashboard.DOExecute(2,0)
            self._dashboard.DOExecute(1,0)
            time.sleep(1)
        except (AttributeError, OSError):
            print("Not connected to arm!")
        return
    
    def suck(self, duration=0):
        """
        Inhale air.

        Args:
            duration (int, optional): number of seconds to inhale air. Defaults to 0.
        """
        try:
            self._dashboard.DOExecute(1,1)
            if duration > 0:
                time.sleep(duration)
                self._dashboard.DOExecute(1,0)
                time.sleep(1)
        except (AttributeError, OSError):
            print("Not connected to arm!")
        return


# Third-party implement attachments, connected though Dobot ports
class Instrument(Dobot):
    """
    Instrument class.

    Args:
        ip_address (str, optional): IP address of arm. Defaults to '192.168.2.8'.
        home_position (tuple, optional): position to home in arm coordinates. Defaults to (0,300,0).
        home_orientation (tuple, optional): orientation to home. Defaults to (0,0,0).
        orientate_matrix (numpy.matrix, optional): matrix to transform arm axes to workspace axes. Defaults to np.identity(3).
        translate_vector (numpy.array, optional): vector to transform arm position to workspace position. Defaults to np.zeros(3).
        scale (int, optional): scale factor to transform arm scale to workspace scale. Defaults to 1.
    """
    def __init__(self, address_sensor=None, **kwargs):
        super().__init__(**kwargs)
        self.sensor = None
        self.connect_sensor(address_sensor)
        return

    def connect_sensor(self, address_sensor):
        return

