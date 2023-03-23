# %% -*- coding: utf-8 -*-
"""
Created: Tue 2022/11/01 17:13:35
@author: Chang Jie

Notes / actionables:
- 
"""
# Standard library imports
from __future__ import annotations
from collections import namedtuple
import numpy as np
import time
from typing import Optional, Protocol

# Local application imports
from ....misc import Factory, Helper
from ..jointed_utils import RobotArm
from .dobot_api import dobot_api_dashboard, dobot_api_feedback
print(f"Import: OK <{__name__}>")

MOVE_TIME_BUFFER_S = 0.5

Device = namedtuple('Device', ['dashboard', 'feedback'])

class DobotAttachment(Protocol):
    implement_offset: tuple
    def _set_dashboard(self, dashboard) -> None:
        ...

class Dobot(RobotArm):
    """
    Dobot class.
    
    Args:
        ip_address (str): IP address of arm
        attachment (str, optional): Dobot attachment. Defaults to None.

    Kwargs:
        home_coordinates (tuple, optional): position to home in arm coordinates. Defaults to (0,0,0).
        home_orientation (tuple, optional): orientation to home. Defaults to (0,0,0).
        orientate_matrix (numpy.matrix, optional): matrix to transform arm axes to workspace axes. Defaults to np.identity(3).
        translate_vector (numpy.ndarray, optional): vector to transform arm position to workspace position. Defaults to (0,0,0).
        implement_offset (tuple, optional): implement offset vector pointing from end of effector to tool tip. Defaults to (0,0,0).
        scale (int, optional): scale factor to transform arm scale to workspace scale. Defaults to 1.
        verbose (bool, optional): whether to print outputs. Defaults to False.
        safe_height (float, optional): safe height. Defaults to None.
    """
    possible_attachments = ['TwoJawGrip', 'VacuumGrip']     ### FIXME: hard-coded
    max_actions = 5                                         ### FIXME: hard-coded
    def __init__(self, ip_address:str, attachment_name:str = None, **kwargs):
        super().__init__(**kwargs)
        self.attachment = None
        self._speed_max = 100
        
        self._connect(ip_address)
        if attachment_name is not None:
            attachment_class = Factory.get_class(attachment_name)
            self.toggleAttachment(True, attachment_class)
        pass
    
    # Properties
    @property
    def dashboard(self) -> dobot_api_dashboard:
        return self.device.dashboard
    
    @property
    def feedback(self) -> dobot_api_feedback:
        return self.device.feedback
    
    @property
    def ip_address(self) -> str:
        return self.connection_details.get('ip_address', '')
    
    def calibrate(self, 
        external_pt1:np.ndarray, 
        internal_pt1:np.ndarray, 
        external_pt2:np.ndarray, 
        internal_pt2:np.ndarray
    ):
        """
        Calibrate internal and external coordinate systems, then verify points.

        Args:
            external_pt1 (numpy.ndarray): x,y,z coordinates of physical point 1
            internal_pt1 (numpy.ndarray): x,y,z coordinates of robot point 1
            external_pt2 (numpy.ndarray): x,y,z coordinates of physical point 2
            internal_pt2 (numpy.ndarray): x,y,z coordinates of robot point 2
        """
        super().calibrate(external_pt1, internal_pt1, external_pt2, internal_pt2)

        # Verify calibrated points
        for pt in [external_pt1, external_pt2]:
            self.home()
            self.moveTo( pt + np.array([0,0,10]) )
            input("Press Enter to verify reference point")
        self.home()
        return
    
    def disconnect(self):
        """
        Disconnect serial connection to robot
        
        Returns:
            None: None is successfully disconnected, else dict
        """
        self.reset()
        try:
            self.dashboard.close()
            self.feedback.close()
        except (AttributeError, OSError):
            if self.verbose:
                print("Not connected to arm.")
        self.setFlag(connected=False)
        return
    
    def getConfigSettings(self, attributes:Optional[list[str]] = None) -> dict:
        """
        Read the robot configuration settings
        
        Returns:
            dict: dictionary of robot class and settings
        """
        attributes = [
            "ip_address", 
            "home_coordinates", 
            "home_orientation", 
            "orientate_matrix", 
            "translate_vector", 
            "implement_offset",
            "scale"
        ] if attributes is None else attributes
        return super().getConfigSettings(attributes)

    @Helper.safety_measures
    def moveCoordBy(self, 
        vector: tuple[float] = (0,0,0), 
        angles: tuple[float] = (0,0,0)
    ) -> bool:
        """
        Relative Cartesian movement and tool orientation, using robot coordinates.

        Args:
            vector (tuple, optional): x,y,z displacement vector. Defaults to None.
            angles (tuple, optional): a,b,c rotation angles in degrees. Defaults to None.
        """
        vector = tuple(vector)
        angles = tuple(angles)
        try:
            self.feedback.RelMovL(*vector)
            self.rotateBy(angles)
        except (AttributeError, OSError):
            if self.verbose:
                print("Not connected to arm.")
            self.updatePosition(vector=vector, angles=angles)
            return False
        else:
            move_time = max(abs(np.array(vector))/self.speed) + max(abs(np.array(angles))/self.speed_angular)
            print(f'Move time: {move_time:.3f}s ({self._speed_fraction:.3f}x)')
            time.sleep(move_time+MOVE_TIME_BUFFER_S)
        self.updatePosition(vector=vector, angles=angles)
        return True

    @Helper.safety_measures
    def moveCoordTo(self, 
        coordinates: Optional[tuple[float]] = None, 
        orientation: Optional[tuple[float]] = None
    ) -> bool:
        """
        Absolute Cartesian movement and tool orientation, using robot coordinates.

        Args:
            coordinates (tuple): x,y,z position vector. Defaults to None.
            orientation (tuple, optional): a,b,c orientation angles in degrees. Defaults to None.
            tool_offset (bool, optional): whether to consider implement offset. Defaults to True.
        """
        coordinates = self.coordinates if coordinates is None else coordinates
        orientation = self.orientation if orientation is None else orientation
        coordinates = tuple(coordinates)
        orientation = tuple(orientation)
        if len(orientation) == 1 and orientation[0] == 0:
            orientation = self.orientation
        if not self.isFeasible(coordinates):
            print(f"Infeasible coordinates! {coordinates}")
            return
        
        try:
            self.feedback.MovJ(*coordinates, *orientation)
        except (AttributeError, OSError):
            if self.verbose:
                print("Not connected to arm.")
            self.updatePosition(coordinates=coordinates, orientation=orientation)
            return False
        else:
            position = self.position
            distances = abs(position[0] - np.array(coordinates))
            rotations = abs(position[1] - np.array(orientation))
            move_time = max([max(distances/self.speed),  max(rotations/self.speed_angular)])
            print(f'Move time: {move_time:.3f}s ({self._speed_fraction:.3f}x)')
            time.sleep(move_time+MOVE_TIME_BUFFER_S)
        self.updatePosition(coordinates=coordinates, orientation=orientation)
        return True

    @Helper.safety_measures
    def moveJointBy(self, relative_angles: tuple[float]) -> bool:
        """
        Relative joint movement

        Args:
            relative_angles (tuple): j1~j6 rotation angles in degrees
            
        Raises:
            Exception: Input has to be length 6
        """
        if len(relative_angles) != 6:
            raise ValueError('Length of input needs to be 6.')
        try:
            self.feedback.RelMovJ(*relative_angles)
        except (AttributeError, OSError):
            if self.verbose:
                print("Not connected to arm.")
            self.updatePosition(angles=relative_angles[3:])
            return False
        else:
            move_time = max(abs(np.array(relative_angles)) / self.speed_angular)
            print(f'Move time: {move_time:.3f}s ({self._speed_fraction:.3f}x)')
            time.sleep(move_time+MOVE_TIME_BUFFER_S)
        self.updatePosition(angles=relative_angles[3:])
        return True

    @Helper.safety_measures
    def moveJointTo(self, absolute_angles: tuple[float]) -> bool:
        """
        Absolute joint movement

        Args:
            absolute_angles (tuple): j1~j6 orientation angles in degrees
        
        Raises:
            Exception: Input has to be length 6
        """
        if len(absolute_angles) != 6:
            raise ValueError('Length of input needs to be 6.')
        try:
            self.feedback.JointMovJ(*absolute_angles)
        except (AttributeError, OSError):
            if self.verbose:
                print("Not connected to arm.")
            self.updatePosition(orientation=absolute_angles[3:])
            return False
        else:
            move_time = max(abs(np.array(absolute_angles)) / self.speed_angular)
            print(f'Move time: {move_time:.3f}s ({self._speed_fraction:.3f}x)')
            time.sleep(move_time+MOVE_TIME_BUFFER_S)
        self.updatePosition(orientation=absolute_angles[3:])
        return True

    def reset(self):
        """
        Clear any errors and enable robot
        """
        try:
            self.dashboard.ClearError()
            self.dashboard.EnableRobot()
        except (AttributeError, OSError):
            if self.verbose:
                print("Not connected to arm.")
        return

    def retractArm(self, target: Optional[tuple[float]] = None) -> bool:
        return super().retractArm(target)
    
    def setSpeed(self, speed:float) -> tuple[bool, float]:
        """
        Setting the Global speed rate.

        Args:
            speed (int): rate value (value range: 1~100)
        """
        speed_fraction = speed/self._speed_max
        if speed_fraction == self._speed_fraction:
            return False, self.speed
        prevailing_speed = self.speed.copy()
        try:
            self.dashboard.SpeedFactor(int(max(1, speed_fraction*100)))
        except (AttributeError, OSError):
            if self.verbose:
                print("Not connected to arm.")
            return False, self.speed
        self._speed_fraction = speed_fraction
        return True, prevailing_speed
    
    def shutdown(self):
        """Halt robot and close connections."""
        self._freeze()
        return super().shutdown()
    
    def toggleAttachment(self, on:bool, attachment_class:Optional[DobotAttachment] = None):
        """
        Add an attachment that interfaces with the Dobot's Digital Output (DO)

        Args:
            on (bool): whether to add attachment, False if removing attachment
            attachment_class (any, optional): attachment to load. Defaults to None.
        """
        if on: # Add attachment
            print("Please secure tool attachment.")
            self.attachment = attachment_class()
            self.attachment._set_dashboard(self.dashboard)
            self.setImplementOffset(self.attachment.implement_offset)
        else: # Remove attachment
            print("Please remove tool attachment.")
            self.attachment = None
            self.setImplementOffset((0,0,0))
        return
    
    def toggleCalibration(self, on:bool, tip_length:float):
        """
        Enter into calibration mode, with a sharp point implement for alignment.

        Args:
            on (bool): whether to set to calibration mode
            tip_length (int, optional): length of sharp point alignment implement. Defaults to 21.
        """
        if on: # Enter calibration mode
            input(f"Please swap to calibration tip.")
            self._temporary_tool_offset = self.implement_offset
            self.setImplementOffset((0,0,-tip_length))
        else: # Exit calibration mode
            input("Please swap back to original tool.")
            self.setImplementOffset(self._temporary_tool_offset)
            del self._temporary_tool_offset
        return

    # Protected method(s)
    def _connect(self, ip_address:str, timeout:int = 10):
        """
        Connect to robot hardware

        Args:
            ip_address (str): IP address of robot
            timeout (int, optional): duration to wait before timeout
            
        Returns:
            dict: dictionary of dashboard and feedback objects
        """
        self.connection_details = {
            'ip_address': ip_address,
            'timeout': timeout
        }
        self.device = Device(None,None)
        try:
            start_time = time.time()
            dashboard = dobot_api_dashboard(ip_address, 29999)
            if time.time() - start_time > timeout:
                raise Exception(f"Unable to connect to arm at {ip_address}")
            
            start_time = time.time()
            feedback = dobot_api_feedback(ip_address, 30003)
            if time.time() - start_time > timeout:
                raise Exception(f"Unable to connect to arm at {ip_address}")
        except Exception as e:
            print(e)
        else:
            self.device = Device(dashboard, feedback)
            self.reset()
            self.dashboard.User(0)
            self.dashboard.Tool(0)
            self.setSpeed(speed=100)
            self.setFlag(connected=True)
        return

    def _freeze(self):
        """
        Halt and disable robot
        """
        try:
            self.dashboard.ResetRobot()
            self.dashboard.DisableRobot()
        except (AttributeError, OSError):
            if self.verbose:
                print("Not connected to arm.")
        return
