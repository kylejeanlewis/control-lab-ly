# %% -*- coding: utf-8 -*-
"""
This module holds the classes for substrate gripper tools from Dobot.

Classes:
    DobotGripper (Gripper)
    TwoJawGrip (DobotGripper)
    VacuumGrip (DobotGripper)

Other constants and variables:
    ATTACHMENT_NAMES (list)
    METHODS_SET (list)
"""
# Standard library imports
from __future__ import annotations
import numpy as np
import time
from typing import Callable, Optional

# Local application imports
from ....misc import Helper
from ..substrate_utils import Gripper
print(f"Import: OK <{__name__}>")

class DobotGripper(Gripper):
    """
    Abstract Base Class (ABC) for Dobot Gripper objects.
    ABC cannot be instantiated, and must be subclassed with abstract methods implemented before use.

    ### Constructor
    Args:
        `dashboard` (Optional[Callable], optional): connection to status and signal control. Defaults to None.
        `channel` (int, optional): digital I/O channel. Defaults to 1.
    
    ### Attributes
    - `dashboard` (Callable): connection to status and signal control
    
    ### Methods
    #### Abstract
    - `drop`: releases an object
    - `grab`: picks up an object
    #### Public
    - `setDashboard`: set the dashboard object
    """
    
    _implement_offset: tuple[float] = (0,0,0)
    def __init__(self, dashboard:Optional[Callable] = None, channel:int = 1):
        """
        Instantiate the class

        Args:
            dashboard (Optional[Callable], optional): connection to status and signal control. Defaults to None.
            channel (int, optional): digital I/O channel. Defaults to 1.
        """
        self.dashboard = None
        self._channel = 0
        self.setDashboard(dashboard=dashboard, channel=channel)
        return
    
    # Properties
    @property
    def channel(self) -> int:
        return self._channel
    @channel.setter
    def channel(self, value:int):
        if 1<= value <= 24:
            self._channel = value
        else:
            raise ValueError("Please provide a valid channel id from 1 to 24.")
        return
    @property
    def implement_offset(self) -> np.ndarray:
        return np.array(self._implement_offset)
    
    def setDashboard(self, dashboard:Callable, channel:int = 1):
        """
        Set the dashboard object

        Args:
            dashboard (Callable): connection to status and signal control
            channel (int, optional): digital I/O channel. Defaults to 1.
        """
        self.dashboard = dashboard
        self.channel= channel
        return
    
    
class TwoJawGrip(DobotGripper):
    """
    TwoJawGrip provides methods to operate the Dobot jaw gripper
    
    ### Constructor
    Args:
        `dashboard` (Optional[Callable], optional): connection to status and signal control. Defaults to None.
        `channel` (int, optional): digital I/O channel. Defaults to 1.
        
    ### Methods
    - `drop`: releases an object by opening the gripper
    - `grab`: picks up an object by closing the gripper
    """
    
    _implement_offset = (0,0,-95)
    def __init__(self, dashboard:Optional[Callable] = None, channel:int = 1):
        """
        Instantiate the class

        Args:
            dashboard (Optional[Callable], optional): connection to status and signal control. Defaults to None.
            channel (int, optional): digital I/O channel. Defaults to 1.
        """
        super().__init__(dashboard=dashboard, channel=channel)
        return

    def drop(self) -> bool:
        """
        Releases an object by opening the gripper
        
        Returns:
            bool: whether action is successful
        """
        try:
            self.dashboard.DOExecute(1,1)
        except (AttributeError, OSError):
            print('Tried to drop...')
            print("Not connected to arm.")
            return False
        return True
    
    def grab(self) -> bool:
        """
        Picks up an object by closing the gripper
        
        Returns:
            bool: whether action is successful
        """
        try:
            self.dashboard.DOExecute(1,0)
        except (AttributeError, OSError):
            print('Tried to grab...')
            print("Not connected to arm.")
            return False
        return True


class VacuumGrip(DobotGripper):
    """
    VacuumGrip provides methods to operate the Dobot vacuum grip
    
    ### Constructor
    Args:
        `dashboard` (Optional[Callable], optional): connection to status and signal control. Defaults to None.
        `channel` (int, optional): digital I/O channel. Defaults to 1.
        
    ### Methods
    - `drop`: releases an object by pushing out air
    - `grab`: picks up an object by pulling in air
    - `pull`: activate pump to suck in air
    - `push`: activate pump to blow out air
    - `stop`: stop airflow
    """
    
    _implement_offset = (0,0,-60)
    def __init__(self, dashboard:Optional[Callable] = None, channel:int = 1):
        """
        Instantiate the class

        Args:
            dashboard (Optional[Callable], optional): connection to status and signal control. Defaults to None.
            channel (int, optional): digital I/O channel. Defaults to 1.
        """
        super().__init__(dashboard=dashboard, channel=channel)
        return

    def drop(self) -> bool:
        """
        Releases an object by pushing out air
        
        Returns:
            bool: whether action is successful
        """
        print('Tried to drop...')
        return self.push(0.5)
    
    def grab(self) -> bool:
        """
        Picks up an object by pulling in air
        
        Returns:
            bool: whether action is successful
        """
        print('Tried to grab...')
        return self.pull(3)
    
    def pull(self, duration:Optional[int] = None) -> bool:
        """
        Activate pump to suck in air
        
        Args:
            duration (Optional[int], optional): number of seconds to pull air. Defaults to None.
        
        Returns:
            bool: whether action is successful
        """
        try:
            self.dashboard.DOExecute(1,1)
        except (AttributeError, OSError):
            print('Tried to pull...')
            print("Not connected to arm.")
            return False
        else:
            if duration is not None:
                time.sleep(duration)
                self.dashboard.DOExecute(1,0)
                time.sleep(1)
        return True
    
    def push(self, duration:Optional[int] = None) -> bool:
        """
        Activate pump to blow out air
        
        Args:
            duration (Optional[int], optional): number of seconds to push air. Defaults to None.
            
        Returns:
            bool: whether action is successful
        """
        try:
            self.dashboard.DOExecute(2,1)
        except (AttributeError, OSError):
            print('Tried to push...')
            print("Not connected to arm.")
            return False
        else:
            if duration is not None:
                time.sleep(duration)
                self.dashboard.DOExecute(2,0)
                time.sleep(1)
        return True
    
    def stop(self) -> bool:
        """
        Stop airflow
        
        Returns:
            bool: whether action is successful
        """
        try:
            self.dashboard.DOExecute(2,0)
            self.dashboard.DOExecute(1,0)
            time.sleep(1)
        except (AttributeError, OSError):
            print('Tried to stop...')
            print("Not connected to arm.")
            return False
        return True


# FIXME: Do away with these objects below
ATTACHMENTS = [TwoJawGrip, VacuumGrip]
METHODS = [Helper.get_method_names(attachment) for attachment in ATTACHMENTS]
ATTACHMENT_NAMES = [att.__name__ for att in ATTACHMENTS]
"""List of attachment names"""
METHODS_SET = sorted( list(set([item for sublist in METHODS for item in sublist])) )
"""Sorted list of method names"""
