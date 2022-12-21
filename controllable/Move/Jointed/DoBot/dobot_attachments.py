# %% -*- coding: utf-8 -*-
"""
Created: Tue 2022/12/12 13:13:00
@author: Chang Jie

Notes / actionables:
-
"""
# Standard library imports
import time

# Local application imports
from .. import RobotArm
from .dobot_api import dobot_api_dashboard, dobot_api_feedback, MyType
print(f"Import: OK <{__name__}>")

ATTACHMENT_LIST = ['JawGripper', 'VacuumGrip']

# First-party implement attachments
class JawGripper(object):
    """
    JawGripper class.
    
    Args:
        dashboard (str, optional): 
    """
    def __init__(self, dashboard):
        self._dashboard = dashboard
        self.implement_offset = (0,0,-95)
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


class VacuumGrip(object):
    """
    VacuumGrip class.

    Args:
        dashboard (str, optional): 
    """
    def __init__(self, dashboard):
        self._dashboard = dashboard
        self.implement_offset = (0,0,-60)
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
