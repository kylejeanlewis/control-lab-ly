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
from ..jointed_utils import RobotArm
from .dobot_api import dobot_api_dashboard, dobot_api_feedback
from . import dobot_attachments as attachments
print(f"Import: OK <{__name__}>")

CONNECTION_TIMEOUT = 20
SCALE = True
MOVE_TIME_S = 0.5

class Dobot(RobotArm):
    """
    Dobot class.
    
    Args:
        ip_address (str): IP address of arm

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
    def __init__(self, ip_address:str, **kwargs):
        super().__init__(**kwargs)
        self.ip_address = ip_address
        self.attachment = None
        
        self.setFlag('retract', True)
        self._connect(ip_address)
        self.home()
        pass
    
    @property
    def dashboard(self):
        if type(self.device) != dict:
            return None
        return self.device.get('dashboard')
    @dashboard.setter
    def dashboard(self, value):
        if type(self.device) != dict:
            self.device = {}
        self.device['dashboard'] = value
        return
    
    @property
    def feedback(self):
        if type(self.device) != dict:
            return None
        return self.device.get('feedback')
    @feedback.setter
    def feedback(self, value):
        if type(self.device) != dict:
            self.device = {}
        self.device['feedback'] = value
        return
    
    def _connect(self, ip_address:str, timeout=CONNECTION_TIMEOUT):
        """
        Connect to robot hardware

        Args:
            ip_address (str): IP address of robot
            timeout (int, optional): duration to wait before timeout
            
        Returns:
            dict: dictionary of dashboard and feedback objects
        """
        self.device = {
            'dashboard': None,
            'feedback': None
        }
        try:
            start_time = time.time()
            dashboard = dobot_api_dashboard(ip_address, 29999)
            if time.time() - start_time > timeout:
                self.device == None
                raise Exception(f"Unable to connect to arm at {ip_address}")
            
            start_time = time.time()
            feedback = dobot_api_feedback(ip_address, 30003)
            if time.time() - start_time > timeout:
                self.device == None
                raise Exception(f"Unable to connect to arm at {ip_address}")

            self.device['dashboard'] = dashboard
            self.device['feedback'] = feedback
            self.reset()
            self.dashboard.User(0)
            self.dashboard.Tool(0)
            self.setSpeed(speed=100)
        except Exception as e:
            print(e)
        return self.device

    def _freeze(self):
        """
        Halt and disable robot
        """
        try:
            self.dashboard.ResetRobot()
            self.dashboard.DisableRobot()
        except (AttributeError, OSError):
            print("Not connected to arm!")
        return
      
    def _shutdown(self):
        """Halt robot and close connections."""
        self._freeze()
        self.disconnect()
        return

    def addAttachment(self, on:bool, attachment_class_name=''):
        """
        Add an attachment that interfaces with the Dobot's Digital Output (DO)

        Args:
            on (bool): whether to add attachment, False if removing attachment
            attachment_class (str, optional): class name of attachment. Defaults to ''.
        """
        if on: # Add attachment
            if attachment_class_name not in attachments.ATTACHMENT_LIST:
                raise Exception(f"Please select valid attachment from: {', '.join(attachments.ATTACHMENT_LIST)}")
            input("Please secure tool attachment")
            attach_class = getattr(attachments, attachment_class_name)
            self.attachment = attach_class(self.dashboard)
            self.setImplementOffset(self.attachment.implement_offset)
        else: # Remove attachment
            input("Please remove tool attachment")
            self.attachment = None
            self.setImplementOffset((0,0,0))
        return

    def calibrate(self, external_pt1:np.ndarray, internal_pt1:np.ndarray, external_pt2:np.ndarray, internal_pt2:np.ndarray):
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

    def calibrationMode(self, on:bool, tip_length=21):
        """
        Enter into calibration mode, with a sharp point implement for alignment.

        Args:
            on (bool): whether to set to calibration mode
            tip_length (int, optional): length of sharp point alignment implement. Defaults to 21.
        """
        if on: # Enter calibration mode
            tip_length = int(input(f"Please swap to calibration tip and enter tip length in mm (Default: {tip_length}mm)") or str(tip_length))
            self._temporary_tool_offset = self.implement_offset
            self.setImplementOffset((0,0,-tip_length))
        else: # Exit calibration mode
            input("Please swap back to original tool")
            self.setImplementOffset(self._temporary_tool_offset)
            del self._temporary_tool_offset
        return
    
    def connect(self):
        """
        Reconnect to robot using existing IP address
        
        Returns:
            dict: dictionary of dashboard and feedback objects
        """
        return self._connect(self.ip_address)
    
    def disconnect(self):
        """
        Disconnect serial connection to robot
        
        Returns:
            None: None is successfully disconnected, else dict
        """
        try:
            self.dashboard.close()
            self.feedback.close()
        except (AttributeError, OSError):
            print("Not connected to arm!")

        self.device = None
        return self.device
    
    def getConfigSettings(self):
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
        ]
        return super().getConfigSettings(attributes)

    def isConnected(self):
        """
        Check whether machine control unit is connected

        Returns:
            bool: whether machine control unit is connected
        """
        if self.device == None:
            print(f"{self.__class__} ({self.ip_address}) not connected.")
            return False
        return True

    def moveCoordBy(self, vector=None, angles=None):
        """
        Relative Cartesian movement and tool orientation, using robot coordinates.

        Args:
            vector (tuple, optional): x,y,z displacement vector. Defaults to None.
            angles (tuple, optional): a,b,c rotation angles in degrees. Defaults to None.
        """
        if vector == None:
            vector = (0,0,0)
        if angles == None:
            angles = (0,0,0)
        vector = tuple(vector)
        angles = tuple(angles)
        try:
            self.feedback.RelMovL(*vector)
            self.rotateBy(angles)
            time.sleep(MOVE_TIME_S)
        except (AttributeError, OSError):
            print("Not connected to arm!")
            return False
        self.updatePosition(vector=vector, angles=angles)
        return True

    def moveCoordTo(self, coordinates=None, orientation=None):
        """
        Absolute Cartesian movement and tool orientation, using robot coordinates.

        Args:
            coordinates (tuple): x,y,z position vector. Defaults to None.
            orientation (tuple, optional): a,b,c orientation angles in degrees. Defaults to None.
            tool_offset (bool, optional): whether to consider implement offset. Defaults to True.
        """
        if coordinates == None:
            coordinates = self.coordinates
        if orientation == None:
            orientation = self.orientation
        coordinates = tuple(coordinates)
        orientation = tuple(orientation)
        if len(orientation) == 1 and orientation[0] == 0:
            orientation = self.orientation
        if not self.isFeasible(coordinates):
            print(f"Infeasible coordinates! {coordinates}")
            return
        
        try:
            self.feedback.MovJ(*coordinates, *orientation)
            time.sleep(MOVE_TIME_S)
        except (AttributeError, OSError):
            print("Not connected to arm!")
            return False
        self.updatePosition(coordinates=coordinates, orientation=orientation)
        return True

    def moveJointBy(self, relative_angles):
        """
        Relative joint movement

        Args:
            relative_angles (tuple): j1~j6 rotation angles in degrees
            
        Raises:
            Exception: Input has to be length 6
        """
        if len(relative_angles) != 6:
            raise Exception('Length of input needs to be 6')
        relative_angles = tuple(relative_angles)
        try:
            self.feedback.RelMovJ(*relative_angles)
            time.sleep(MOVE_TIME_S)
        except (AttributeError, OSError):
            print("Not connected to arm!")
            return False
        self.updatePosition(angles=relative_angles[3:])
        return True

    def moveJointTo(self, absolute_angles):
        """
        Absolute joint movement

        Args:
            absolute_angles (tuple): j1~j6 orientation angles in degrees
        
        Raises:
            Exception: Input has to be length 6
        """
        if len(absolute_angles) != 6:
            raise Exception('Length of input needs to be 6')
        absolute_angles = tuple(absolute_angles)
        try:
            self.feedback.JointMovJ(*absolute_angles)
            time.sleep(MOVE_TIME_S)
        except (AttributeError, OSError):
            print("Not connected to arm!")
            return False
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
            print("Not connected to arm!")
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


class MG400(Dobot):
    """
    MG400 class.

    Args:
        ip_address (str, optional): IP address of arm. Defaults to '192.168.2.8'.
        retract (bool, optional): whether to tuck arm before each movement. Defaults to True.
        
    Kwargs:
        home_coordinates (tuple, optional): position to home in arm coordinates. Defaults to (0,300,0).
        home_orientation (tuple, optional): orientation to home. Defaults to (0,0,0).
        orientate_matrix (numpy.matrix, optional): matrix to transform arm axes to workspace axes. Defaults to np.identity(3).
        translate_vector (numpy.ndarray, optional): vector to transform arm position to workspace position. Defaults to (0,0,0).
        implement_offset (tuple, optional): implement offset vector pointing from end of effector to tool tip. Defaults to (0,0,0).
        scale (int, optional): scale factor to transform arm scale to workspace scale. Defaults to 1.
        verbose (bool, optional): whether to print outputs. Defaults to False.
        safe_height (float, optional): safe height. Defaults to None.
    """
    def __init__(self, ip_address='192.168.2.8', retract=True, home_coordinates=(0,300,0), **kwargs):
        super().__init__(ip_address=ip_address, home_coordinates=home_coordinates, **kwargs)
        self.setFlag('retract', retract)
        self.setHeight('safe', 75)
        return
    
    def isFeasible(self, coordinates, transform=False, tool_offset=False):
        """
        Checks if specified coordinates is a feasible position for robot to access.

        Args:
            coordinates (tuple): x,y,z coordinates
            transform (bool, optional): whether to transform the coordinates. Defaults to False.
            tool_offset (bool, optional): whether to consider tooltip offset. Defaults to False.

        Returns:
            bool: whether coordinates is a feasible position
        """
        if transform:
            coordinates = self._transform_in(coordinates=coordinates, offset=True, tool_offset=tool_offset)
        x,y,z = coordinates
        j1 = round(math.degrees(math.atan(x/(y + 1E-6))), 3)
        if y < 0:
            j1 += (180 * math.copysign(1, x))
        if abs(j1) > 160:
            return False
        if not (-150 < z < 230):
            return False
        return True
    
    def retractArm(self, target=None):
        """
        Tuck in arm, rotate about base, then extend again.

        Args:
            target (tuple, optional): x,y,z coordinates of destination. Defaults to None.
        
        Returns:
            bool: whether movement is successful
        """
        return_values= []
        safe_radius = 225
        safe_height = self.heights.get('safe', 75)
        x,y,_ = self.coordinates
        if any((x,y)):
            w = ( (safe_radius**2)/(x**2 + y**2) )**0.5
            x,y = (x*w,y*w)
        else:
            x,y = (0,safe_radius)
        ret = self.moveCoordTo((x,y,safe_height), self.orientation)
        return_values.append(ret)

        if target != None and len(target) == 3:
            x1,y1,_ = target
            w1 = ( (safe_radius**2)/(x1**2 + y1**2) )**0.5
            ret = self.moveCoordTo((x1*w1,y1*w1,75), self.orientation)
            return_values.append(ret)
        return all(return_values)


class M1Pro(Dobot):
    """
    M1 Pro class.
    
    Args:
        ip_address (str, optional): IP address of arm. Defaults to '192.168.2.21'.
        retract (bool, optional): whether to tuck arm before each movement. Defaults to False.
        handedness (str, optional): handedness of robot (i.e. left or right). Defaults to 'left'.

    Kwargs:
        home_coordinates (tuple, optional): position to home in arm coordinates. Defaults to (0,300,100).
        home_orientation (tuple, optional): orientation to home. Defaults to (0,0,0).
        orientate_matrix (numpy.matrix, optional): matrix to transform arm axes to workspace axes. Defaults to np.identity(3).
        translate_vector (numpy.ndarray, optional): vector to transform arm position to workspace position. Defaults to (0,0,0).
        implement_offset (tuple, optional): implement offset vector pointing from end of effector to tool tip. Defaults to (0,0,0).
        scale (int, optional): scale factor to transform arm scale to workspace scale. Defaults to 1.
        verbose (bool, optional): whether to print outputs. Defaults to False.
        safe_height (float, optional): safe height. Defaults to None.
    """
    def __init__(self, ip_address='192.168.2.21', handedness='right', home_coordinates=(0,300,100), **kwargs):
        super().__init__(ip_address=ip_address, home_coordinates=home_coordinates, **kwargs)
        self.setFlag('right_handed', None)
        self.setHandedness(handedness)
        return
    
    def home(self, tool_offset=False):
        """
        Return the robot to home

        Args:
            tool_offset (bool, optional): whether to consider the offset of the tooltip. Defaults to False.
        
        Returns:
            bool: whether movement is successful
        """
        return super().home(tool_offset)
    
    def isFeasible(self, coordinates, transform=False, tool_offset=False):
        """
        Checks if specified coordinates is a feasible position for robot to access.

        Args:
            coordinates (tuple): x,y,z coordinates
            transform (bool, optional): whether to transform the coordinates. Defaults to False.
            tool_offset (bool, optional): whether to consider tooltip offset. Defaults to False.

        Returns:
            bool: whether coordinates is a feasible position
        """
        if transform:
            coordinates = self._transform_in(coordinates=coordinates, tool_offset=tool_offset)
        x,y,z = coordinates
        
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
        
        # Space constraints
        # if x > 344: # front edge
        #     return False
        # if x < 76 and abs(y) < 150: # elevated structure
        #     return False
                
        # x=4, y=3
        grad = abs(y/(x+1E-6))
        if grad > 0.75 or x < 0:
            hand = 'right' if y>0 else 'left'
            self.setHandedness(hand, stretch=True)
        return True
    
    def moveCoordBy(self, vector=None, angles=None):
        """
        Relative Cartesian movement and tool orientation, using robot coordinates.

        Args:
            vector (tuple, optional): x,y,z displacement vector. Defaults to None.
            angles (tuple, optional): a,b,c rotation angles in degrees. Defaults to None.
        """
        if vector == None:
            vector = (0,0,0)
        if angles == None:
            angles = (0,0,0)
        coordinates, orientation = self.position
        new_coordinates = np.array(coordinates) + np.array(vector)
        new_orientation = np.array(orientation) + np.array(angles)
        return self.moveCoordTo(new_coordinates, new_orientation)

    def setHandedness(self, hand, stretch=False):
        """
        Set handedness of robot arm

        Args:
            hand (str): handedness
            stretch (bool, optional): whether to stretch the arm. Defaults to False.

        Raises:
            Exception: The parameter 'hand' has to be either 'left' or 'right'
        """
        set_hand = False
        handedness = None
        if self._flags['right_handed'] != None:
            handedness = 'right' if self._flags['right_handed'] else 'left'
        if hand not in ['left','l','L','right','r','R']:
            raise Exception("Please select between 'left' or 'right'")
        if hand in ['left','l','L'] and handedness != 'left': #0
            try:
                self.dashboard.SetArmOrientation(0,1,1,1)
            except (AttributeError, OSError):
                print("Not connected to arm!")
            finally:
                self.setFlag('right_handed', False)
                set_hand = True
        elif hand in ['right','r','R'] and handedness != 'right': #1
            try:
                self.dashboard.SetArmOrientation(1,1,1,1)
            except (AttributeError, OSError):
                print("Not connected to arm!")
            finally:
                self.setFlag('right_handed', True)
                set_hand = True
        if set_hand and stretch:
            self.stretchArm()
        return
            
    def stretchArm(self):
        """
        Stretch arm to switch handedness
        
        Returns:
            bool: whether movement is successful
        """
        _,y,z = self.coordinates
        y = 240 * math.copysign(1, y)
        return self.moveCoordTo(coordinates=(320,y,z))
    