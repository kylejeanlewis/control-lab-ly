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
from ...misc import Helper
print(f"Import: OK <{__name__}>")

class Attachment(object):
    """
    Dobot first part implement attachments

    Args:
        dashboard (any): Dashboard object
    """
    implement_offset = (0,0,0)
    def __init__(self, dashboard):
        self.dashboard = dashboard
        return
    
    
class TwoJawGrip(Attachment):
    """
    TwoJawGrip class
    
    Args:
        dashboard (dobot_api.dobot_api_dashboard): Dobot API Dashboard object
    """
    implement_offset = (0,0,-95)
    def __init__(self, dashboard):
        super().__init__(dashboard)
        return

    def drop(self):
        """
        Open gripper, let go of object
        
        Returns:
            bool: whether action is successful
        """
        try:
            self.dashboard.DOExecute(1,1)
        except (AttributeError, OSError):
            print('Tried to drop...')
            print("Not connected to arm!")
            return False
        return True
    
    def grab(self):
        """
        Close gripper, pick object up
        
        Returns:
            bool: whether action is successful
        """
        try:
            self.dashboard.DOExecute(1,0)
        except (AttributeError, OSError):
            print('Tried to grab...')
            print("Not connected to arm!")
            return False
        return True


class VacuumGrip(Attachment):
    """
    VacuumGrip class

    Args:
        dashboard (dobot_api.dobot_api_dashboard): Dobot API Dashboard object
    """
    implement_offset = (0,0,-60)
    def __init__(self, dashboard):
        super().__init__(dashboard)
        return

    def drop(self):
        """
        Let go of object
        
        Returns:
            bool: whether action is successful
        """
        print('Tried to drop...')
        return self.push(0.5)
    
    def grab(self):
        """
        Pick up object
        
        Returns:
            bool: whether action is successful
        """
        print('Tried to grab...')
        return self.pull(3)
    
    def pull(self, duration=None):
        """
        Inhale air

        Args:
            duration (int, optional): number of seconds to inhale air. Defaults to None.
        """
        try:
            self.dashboard.DOExecute(1,1)
            if duration is not None:
                time.sleep(duration)
                self.dashboard.DOExecute(1,0)
                time.sleep(1)
        except (AttributeError, OSError):
            print('Tried to pull...')
            print("Not connected to arm!")
            return False
        return True
    
    def push(self, duration=None):
        """
        Expel air

        Args:
            duration (int, optional): number of seconds to expel air. Defaults to None.
            
        Returns:
            bool: whether action is successful
        """
        try:
            self.dashboard.DOExecute(2,1)
            if duration is not None:
                time.sleep(duration)
                self.dashboard.DOExecute(2,0)
                time.sleep(1)
        except (AttributeError, OSError):
            print('Tried to push...')
            print("Not connected to arm!")
            return False
        return True
    
    def stop(self):
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
            print("Not connected to arm!")
            return False
        return True


ATTACHMENTS = [TwoJawGrip, VacuumGrip]
ATTACHMENT_NAMES = ['TwoJawGrip', 'VacuumGrip']
METHODS = [Helper.get_method_names(attachment) for attachment in ATTACHMENTS]
METHODS_SET = sorted( list(set([item for sublist in METHODS for item in sublist])) )
