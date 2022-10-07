# %% -*- coding: utf-8 -*-
"""
Created on Wed 2022 Jul 20 11:54:04

@author: cjleong

Notes:
"""
import os, sys
import time
import math
import numpy as np
from dobot.dobot_api import dobot_api_dashboard, dobot_api_feedback, MyType
print(f"Import: OK <{__name__}>")

SCALE = True
MOVE_TIME = 0.5

# %%
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


class Dobot(object):
    """
    Dobot class.

    Args:
        address (str, optional): IP address of arm. Defaults to '192.168.2.8'.
        home_position (tuple, optional): position to home in arm coordinates. Defaults to (0,300,0).
        home_orientation (tuple, optional): orientation to home. Defaults to (0,0,0).
        orientate_matrix (numpy.matrix, optional): matrix to transform arm axes to workspace axes. Defaults to np.identity(3).
        translate_vector (numpy.array, optional): vector to transform arm position to workspace position. Defaults to np.zeros(3).
        scale (int, optional): scale factor to transform arm scale to workspace scale. Defaults to 1.
    """
    def __init__(self, address='192.168.2.8', home_position=(0,300,0), home_orientation=(0,0,0), orientate_matrix=np.identity(3), translate_vector=np.zeros(3), scale=1):
        self.address = address
        self.dashboard = None
        self.feedback = None

        # Vector that points from implement tip to tool holder
        self.implement_offset = (0,0,0)
        self.home_position = home_position
        self.home_orientation = home_orientation
        self.orientate_matrix = orientate_matrix
        self.translate_vector = translate_vector
        self.scale = scale
        
        self.current_x = 0
        self.current_y = 0
        self.current_z = 0
        self.coordinates = (self.current_x, self.current_y, self.current_z)
        self.orientation = (0,0,0)

        self.connect(address)
        self.home()
        pass

    def __delete__(self):
        self.shutdown()
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
        self.orientate_matrix = rot_matrix #np.matmul(rot_matrix, self.orientate_matrix)
        self.translate_vector = (external_pt1 - internal_pt1) #+ self.translate_vector
        self.scale = (space_mag / robot_mag) #* self.scale
        
        print(f'Address: {self.address}')
        print(f'Orientate matrix:\n{self.orientate_matrix}')
        print(f'Translate vector: {self.translate_vector}')
        print(f'Scale factor: {self.scale}')
        print(f'Offset angle: {rot_angle/math.pi*180} degree')
        print(f'Offset vector: {(external_pt1 - internal_pt1)}')

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

    def connect(self, address):
        """
        Connect to robot hardware.

        Args:
            address (string): IP address of robot
        """
        try:
            self.dashboard = dobot_api_dashboard(address, 29999)
            self.feedback = dobot_api_feedback(address, 30003)

            self.reset()
            self.dashboard.User(0)
            self.dashboard.Tool(0)
            self.setSpeed(speed=100)
        except Exception as e:
            print(f"Unable to connect to arm at {address}")
            print(e)
        return
    
    def getOrientation(self):
        """Read the current position and orientation of arm."""
        # reply = self.feedback.WaitReply()
        # print(reply)
        return self.orientation

    def getPosition(self):
        """Read the current position and orientation of arm."""
        # reply = self.feedback.WaitReply()
        # print(reply)
        return self.coordinates
    
    def getSettings(self):
        """Read the arm configuration settings."""
        arm = str(type(self)).split("'")[1].split('.')[1]
        param = ["address", "home_position", "home_orientation", "orientate_matrix", "translate_vector", "scale"]
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
        return self.transform_vector_out(self.getPosition(), offset=offset)

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
        vector = self.transform_vector_in(vector)
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
        coord = self.transform_vector_in(coord, offset=True)
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
            self.feedback.RelMovJ(*relative_angle)
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
            self.feedback.JointMovJ(*absolute_angle)
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
            self.feedback.RelMovL(*relative_coord)
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
            self.feedback.MovJ(*absolute_arm_coord, *orientation)
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
            self.dashboard.ClearError()
            self.dashboard.EnableRobot()
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
        self.coordinates = self.transform_vector_in(coord, offset=True, stretch=SCALE)
        return

    def setSpeed(self, speed):
        """
        Setting the Global speed rate.

        Args:
            speed (int): rate value (value range: 1~100)
        """
        try:
            self.dashboard.SpeedFactor(speed)
        except (AttributeError, OSError):
            print("Not connected to arm!")
        return

    def shutdown(self):
        """Halt robot and close conenctions."""
        self.halt()
        try:
            self.dashboard.close()
            self.feedback.close()
        except (AttributeError, OSError):
            print("Not connected to arm!")

        self.dashboard = None
        self.feedback = None
        return

    def halt(self):
        """Halt and disable robot."""
        try:
            self.dashboard.ResetRobot()
            self.dashboard.DisableRobot()
        except (AttributeError, OSError):
            print("Not connected to arm!")
        return

    def transform_vector_in(self, coord, offset=False, stretch=SCALE):
        """
        Order of transformations (scale, rotate, translate).

        Args:
            coord (tuple): vector
            offset (bool, optional): whether to translate. Defaults to False.
            stretch (bool, optional): whether to scale. Defaults to SCALE.

        Returns:
            tuple: converted arm vector
        """
        translate = (-1*self.translate_vector) if offset else np.zeros(3)
        scale = (1/self.scale) if stretch else 1
        return tuple( translate + np.matmul(self.orientate_matrix.T, scale * np.array(coord)) )

    def transform_vector_out(self, coord, offset=False, stretch=SCALE):
        """
        Order of transformations (translate, rotate, scale).

        Args:
            coord (tuple): vector
            offset (bool, optional): whether to translate. Defaults to False.
            stretch (bool, optional): whether to scale. Defaults to SCALE.

        Returns:
            tuple: converted workspace vector
        """
        translate = self.translate_vector if offset else np.zeros(3)
        scale = self.scale if stretch else 1
        return tuple( scale * np.matmul(self.orientate_matrix, translate + np.array(coord)) )

    def tuck(self, target=None):
        """
        Tuck in arm, rotate about base, then extend again.

        Args:
            target (tuple, optional): x,y,z coordinates of destination. Defaults to None.
        """
        x,y,_ = self.getPosition()
        if any((x,y)):
            w = ( (225*225)/(x*x + y*y) )**0.5
            x,y = (x*w,y*w)
        else:
            x,y = (0,225)
        self.moveCoordTo((x,y,75), self.orientation, offset=False)

        if type(target) != type(None) and len(target) == 3:
            x1,y1,_ = target
            w1 = ( (225*225)/(x1*x1 + y1*y1) )**0.5
            self.moveCoordTo((x1*w1,y1*w1,75), self.orientation, offset=False)
        return


# First-party implement attachments
class JawGripper(Dobot):
    """
    JawGripper class.
    
    Args:
        address (str, optional): IP address of arm. Defaults to '192.168.2.8'.
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
            self.dashboard.DOExecute(1,1)
        except (AttributeError, OSError):
            print("Not connected to arm!")
        return
    
    def grab(self):
        """Close gripper"""
        try:
            self.dashboard.DOExecute(1,0)
        except (AttributeError, OSError):
            print("Not connected to arm!")
        return


class VacuumGrip(Dobot):
    """
    VacuumGrip class.

    Args:
        address (str, optional): IP address of arm. Defaults to '192.168.2.8'.
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
            self.dashboard.DOExecute(2,1)
            if duration > 0:
                time.sleep(duration)
                self.dashboard.DOExecute(2,0)
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
            self.dashboard.DOExecute(2,0)
            self.dashboard.DOExecute(1,0)
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
            self.dashboard.DOExecute(1,1)
            if duration > 0:
                time.sleep(duration)
                self.dashboard.DOExecute(1,0)
                time.sleep(1)
        except (AttributeError, OSError):
            print("Not connected to arm!")
        return


# Third-party implement attachments
class Instrument(Dobot):
    """
    Instrument class.

    Args:
        address (str, optional): IP address of arm. Defaults to '192.168.2.8'.
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


# %%
