# %% -*- coding: utf-8 -*-
"""
This module holds the classes for substrate gripper tools from Dobot.

Classes:
    DobotGripper (Gripper)
    TwoJawGrip (DobotGripper)
    VacuumGrip (DobotGripper)
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
        `channel_map` (Optional[dict], optional): mapping of digital I/O channel(s). Defaults to None.
    
    ### Attributes
    - `dashboard` (Callable): connection to status and signal control
    
    ### Properties
    - `channel_map` (dict): mapping of digital I/O channel(s)
    - `implement_offset` (np.ndarray): offset from attachment site to tooltip
    
    ### Methods
    #### Abstract
    - `drop`: releases an object
    - `grab`: picks up an object
    #### Public
    - `setDashboard`: set the dashboard object
    """
    
    _implement_offset: tuple[float] = (0,0,0)
    def __init__(self, dashboard:Optional[Callable] = None, channel_map:Optional[dict] = None):
        """
        Instantiate the class

        Args:
            dashboard (Optional[Callable], optional): connection to status and signal control. Defaults to None.
            channel_map (Optional[dict], optional): mapping of digital I/O channel(s). Defaults to None.
        """
        self.dashboard = None
        self._channel_map = {}
        self.setDashboard(dashboard=dashboard, channel_map=channel_map)
        return
    
    # Properties
    @property
    def channel_map(self) -> dict:
        return self._channel_map
    @channel_map.setter
    def channel_map(self, value:dict):
        if value is None:
            self._channel_map = {}
            return
        if all([(1<= v <=24) for v in value.values()]):
            self._channel_map = value
        else:
            raise ValueError("Please provide valid channel ids from 1 to 24.")
        return
    
    @property
    def implement_offset(self) -> np.ndarray:
        return np.array(self._implement_offset)
    
    def setDashboard(self, dashboard:Callable, channel_map:Optional[dict] = None):
        """
        Set the dashboard object

        Args:
            dashboard (Callable): connection to status and signal control
            channel_map (Optional[dict], optional): mapping of digital I/O channel(s). Defaults to None.
        """
        self.dashboard = dashboard
        self.channel_map = channel_map
        return
    
    
class TwoJawGrip(DobotGripper):
    """
    TwoJawGrip provides methods to operate the Dobot jaw gripper.
    Channel map labels: `grab`
    
    ### Constructor
    Args:
        `dashboard` (Optional[Callable], optional): connection to status and signal control. Defaults to None.
        `channel_map` (Optional[dict], optional): mapping of digital I/O channel(s). Defaults to None.
        
    ### Methods
    - `drop`: releases an object by opening the gripper
    - `grab`: picks up an object by closing the gripper
    """
    
    _implement_offset = (0,0,-95)
    def __init__(self, dashboard:Optional[Callable] = None, channel_map:Optional[dict] = None):
        """
        Instantiate the class

        Args:
            dashboard (Optional[Callable], optional): connection to status and signal control. Defaults to None.
            channel_map (Optional[dict], optional): mapping of digital I/O channel(s). Defaults to None.
        """
        super().__init__(dashboard=dashboard, channel_map=channel_map)
        return

    def drop(self) -> bool:
        """
        Releases an object by opening the gripper
        
        Returns:
            bool: whether action is successful
        """
        channel = self.channel_map.get("grab", 1)
        try:
            self.dashboard.DOExecute(channel, 1)
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
        channel = self.channel_map.get("grab", 1)
        try:
            self.dashboard.DOExecute(channel, 0)
        except (AttributeError, OSError):
            print('Tried to grab...')
            print("Not connected to arm.")
            return False
        return True


class VacuumGrip(DobotGripper):
    """
    VacuumGrip provides methods to operate the Dobot vacuum grip.
    Channel map labels: `pull`, `push`
    
    ### Constructor
    Args:
        `dashboard` (Optional[Callable], optional): connection to status and signal control. Defaults to None.
        `channel_map` (Optional[dict], optional): mapping of digital I/O channel(s). Defaults to None.
        
    ### Methods
    - `drop`: releases an object by pushing out air
    - `grab`: picks up an object by pulling in air
    - `pull`: activate pump to suck in air
    - `push`: activate pump to blow out air
    - `stop`: stop airflow
    """
    
    _implement_offset = (0,0,-60)
    def __init__(self, dashboard:Optional[Callable] = None, channel_map:Optional[dict] = None):
        """
        Instantiate the class

        Args:
            dashboard (Optional[Callable], optional): connection to status and signal control. Defaults to None.
            channel_map (Optional[dict], optional): mapping of digital I/O channel(s). Defaults to None.
        """
        super().__init__(dashboard=dashboard, channel_map=channel_map)
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
        channel = self.channel_map.get("pull", 1)
        try:
            self.dashboard.DOExecute(channel, 1)
        except (AttributeError, OSError):
            print('Tried to pull...')
            print("Not connected to arm.")
            return False
        else:
            if duration is not None:
                time.sleep(duration)
                self.dashboard.DOExecute(channel, 0)
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
        channel = self.channel_map.get("push", 2)
        try:
            self.dashboard.DOExecute(channel, 1)
        except (AttributeError, OSError):
            print('Tried to push...')
            print("Not connected to arm.")
            return False
        else:
            if duration is not None:
                time.sleep(duration)
                self.dashboard.DOExecute(channel, 0)
                time.sleep(1)
        return True
    
    def stop(self) -> bool:
        """
        Stop airflow
        
        Returns:
            bool: whether action is successful
        """
        channels = [v for v in self.channel_map.values()] if len(self.channel_map) else [1,2]
        try:
            for channel in channels:
                self.dashboard.DOExecute(channel, 0)
            time.sleep(1)
        except (AttributeError, OSError):
            print('Tried to stop...')
            print("Not connected to arm.")
            return False
        return True
