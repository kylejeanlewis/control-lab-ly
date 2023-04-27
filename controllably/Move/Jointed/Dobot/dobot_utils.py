# %% -*- coding: utf-8 -*-
"""
This module holds the base class for movement tools from Dobot.

Classes:
    Dobot (RobotArm)

Other types:
    Device (namedtuple)

Other constants and variables:
    MOVE_TIME_BUFFER_S (float)
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
"""Device is a named tuple for a dashboard,feedback pair"""

class DobotAttachment(Protocol):
    implement_offset: tuple
    def setDashboard(self, dashboard):
        ...

class Dobot(RobotArm):
    """
    Abstract Base Class (ABC) for Dobot objects. Dobot provides controls for articulated robots from Dobot.
    ABC cannot be instantiated, and must be subclassed with abstract methods implemented before use.
    
    ### Constructor
    Args:
        `ip_address` (str): IP address of Dobot
        `attachment_name` (str, optional): name of attachment. Defaults to None.

    ### Attributes
    - `attachment` (DobotAttachment): attached Dobot tool
    
    ### Properties
    - `dashboard` (dobot_api_dashboard): connection to status and signal control
    - `feedback` (dobot_api_feedback): connection to movement controls
    - `ip_address` (str): IP address of Dobot
    
    ### Methods
    #### Abstract
    - `isFeasible`: checks and returns whether the target coordinate is feasible
    #### Public
    - `calibrate`: calibrate the internal and external coordinate systems, then verify points
    - `disconnect`: disconnect from device
    - `getConfigSettings`: retrieve the robot's configuration
    - `moveCoordBy`: relative Cartesian movement and tool orientation, using robot coordinates
    - `moveCoordTo`: absolute Cartesian movement and tool orientation, using robot coordinates
    - `moveJointBy`: relative joint movement
    - `moveJointTo`: absolute joint movement
    - `reset`: reset the robot
    - `setSpeed`: set the speed of the robot
    - `shutdown`: shutdown procedure for tool
    - `toggleAttachment`: couple or remove Dobot attachment that interfaces with Dobot's digital output
    - `toggleCalibration`: enter or exit calibration mode, with a sharp point implement for alignment
    """
    
    possible_attachments = ['TwoJawGrip', 'VacuumGrip']     ### FIXME: hard-coded
    max_actions = 5                                         ### FIXME: hard-coded
    def __init__(self, ip_address:str, attachment_name:str = None, **kwargs):
        """
        Instantiate the class

        Args:
            ip_address (str): IP address of Dobot
            attachment_name (str, optional): name of attachment. Defaults to None.
        """
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
        Calibrate the internal and external coordinate systems, then verify points.

        Args:
            external_pt1 (np.ndarray): x,y,z coordinates of physical point 1
            internal_pt1 (np.ndarray): x,y,z coordinates of robot point 1
            external_pt2 (np.ndarray): x,y,z coordinates of physical point 2
            internal_pt2 (np.ndarray): x,y,z coordinates of robot point 2
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
        """Disconnect from device"""
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
        Retrieve the robot's configuration
        
        Args:
            attributes (list[str]): list of attributes to retrieve values from
        
        Returns:
            dict: dictionary of robot class and configuration
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
        Relative Cartesian movement and tool orientation, using robot coordinates

        Args:
            vector (tuple[float], optional): x,y,z displacement vector. Defaults to (0,0,0).
            angles (tuple[float], optional): a,b,c rotation angles in degrees. Defaults to (0,0,0).

        Returns:
            bool: whether movement is successful
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
        Absolute Cartesian movement and tool orientation, using robot coordinates

        Args:
            coordinates (Optional[tuple[float]], optional): x,y,z position vector. Defaults to None.
            orientation (Optional[tuple[float]], optional): a,b,c orientation angles in degrees. Defaults to None.
        
        Returns:
            bool: whether movement is successful
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
            relative_angles (tuple[float]): j1~j6 rotation angles in degrees

        Raises:
            ValueError: Length of input needs to be 6.

        Returns:
            bool: whether movement is successful
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
            absolute_angles (tuple[float]): j1~j6 orientation angles in degrees

        Raises:
            ValueError: Length of input needs to be 6.

        Returns:
            bool: whether movement is successful
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
        """Reset the robot"""
        try:
            self.dashboard.ClearError()
            self.dashboard.EnableRobot()
        except (AttributeError, OSError):
            if self.verbose:
                print("Not connected to arm.")
        return

    # def retractArm(self, target: Optional[tuple[float]] = None) -> bool:
    #     """
    #     Tuck in arm, rotate about base, then extend again

    #     Args:
    #         target (Optional[tuple[float]], optional): x,y,z coordinates of destination. Defaults to None.

    #     Returns:
    #         bool: whether movement is successful
    #     """
    #     return super().retractArm(target)
    
    def setSpeed(self, speed:float) -> tuple[bool, float]:
        """
        Set the speed of the robot

        Args:
            speed (int): rate value (value range: 1~100)
        """
        speed_fraction = speed/self._speed_max
        if speed_fraction == self._speed_fraction:
            return False, self.speed
        prevailing_speed = self.speed
        try:
            self.dashboard.SpeedFactor(int(max(1, speed_fraction*100)))
        except (AttributeError, OSError):
            if self.verbose:
                print("Not connected to arm.")
            return False, self.speed
        self._speed_fraction = speed_fraction
        return True, prevailing_speed
    
    def shutdown(self):
        """Shutdown procedure for tool"""
        self._freeze()
        return super().shutdown()
    
    def toggleAttachment(self, on:bool, attachment_class:Optional[DobotAttachment] = None):
        """
        Couple or remove Dobot attachment that interfaces with Dobot's digital output

        Args:
            on (bool): whether to couple Dobot attachment
            attachment_class (Optional[DobotAttachment], optional): Dobot attachment to couple. Defaults to None.
        """
        if on: # Add attachment
            print("Please secure tool attachment.")
            self.attachment: DobotAttachment = attachment_class()
            self.attachment.setDashboard(dashboard=self.dashboard)
            self.setImplementOffset(self.attachment.implement_offset)
        else: # Remove attachment
            print("Please remove tool attachment.")
            self.attachment = None
            self.setImplementOffset((0,0,0))
        return
    
    def toggleCalibration(self, on:bool, tip_length:float):
        """
        Enter or exit calibration mode, with a sharp point implement for alignment

        Args:
            on (bool): whether to set to calibration mode
            tip_length (int, optional): length of sharp point alignment implement
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
        Connection procedure for tool

        Args:
            ip_address (str): IP address of robot
            timeout (int, optional): duration to wait before timeout. Defaults to 10.
        """
        self.connection_details = {
            'ip_address': ip_address,
            'timeout': timeout
        }
        self.device = Device(None,None)
        try:
            start_time = time.perf_counter()
            dashboard = dobot_api_dashboard(ip_address, 29999)
            if time.perf_counter() - start_time > timeout:
                raise Exception(f"Unable to connect to arm at {ip_address}")
            
            start_time = time.perf_counter()
            feedback = dobot_api_feedback(ip_address, 30003)
            if time.perf_counter() - start_time > timeout:
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
        """Halt and disable robot"""
        try:
            self.dashboard.ResetRobot()
            self.dashboard.DisableRobot()
        except (AttributeError, OSError):
            if self.verbose:
                print("Not connected to arm.")
        return
