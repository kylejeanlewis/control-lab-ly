# %% -*- coding: utf-8 -*-
"""
Created: Tue 2022/12/12 13:13:00
@author: Chang Jie

Notes / actionables:
-
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
    Dobot first part implement attachments

    Args:
        dashboard (any): Dashboard object
    """
    _implement_offset: tuple[float] = (0,0,0)
    def __init__(self, dashboard:Optional[Callable] = None, channel:int = 1):
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
        self.dashboard = dashboard
        self.channel= channel
        return
    
    
class TwoJawGrip(DobotGripper):
    """
    TwoJawGrip class
    
    Args:
        dashboard (dobot_api.dobot_api_dashboard): Dobot API Dashboard object
    """
    _implement_offset = (0,0,-95)
    def __init__(self, dashboard:Optional[Callable] = None, channel:int = 1):
        super().__init__(dashboard=dashboard, channel=channel)
        return

    def drop(self) -> bool:
        """
        Open gripper, let go of object
        
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
        Close gripper, pick object up
        
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
    VacuumGrip class

    Args:
        dashboard (dobot_api.dobot_api_dashboard): Dobot API Dashboard object
    """
    _implement_offset = (0,0,-60)
    def __init__(self, dashboard:Optional[Callable] = None, channel:int = 1):
        super().__init__(dashboard=dashboard, channel=channel)
        return

    def drop(self) -> bool:
        """
        Let go of object
        
        Returns:
            bool: whether action is successful
        """
        print('Tried to drop...')
        return self.push(0.5)
    
    def grab(self) -> bool:
        """
        Pick up object
        
        Returns:
            bool: whether action is successful
        """
        print('Tried to grab...')
        return self.pull(3)
    
    def pull(self, duration:Optional[int] = None) -> bool:
        """
        Inhale air

        Args:
            duration (int, optional): number of seconds to inhale air. Defaults to None.
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
        Expel air

        Args:
            duration (int, optional): number of seconds to expel air. Defaults to None.
            
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


# FIXME
ATTACHMENTS = [TwoJawGrip, VacuumGrip]
ATTACHMENT_NAMES = ['TwoJawGrip', 'VacuumGrip']
METHODS = [Helper.get_method_names(attachment) for attachment in ATTACHMENTS]
METHODS_SET = sorted( list(set([item for sublist in METHODS for item in sublist])) )
