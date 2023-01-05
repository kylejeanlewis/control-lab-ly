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
print(f"Import: OK <{__name__}>")

class Attachment(object):
    """
    Dobot first part implement attachments

    Args:
        dashboard (any): Dashboard object
    """
    def __init__(self, dashboard):
        self.dashboard = dashboard
        self.implement_offset = (0,0,0)
        return
    
    
class TwoJawGrip(Attachment):
    """
    TwoJawGrip class
    
    Args:
        dashboard (dobot_api.dobot_api_dashboard): Dobot API Dashboard object
    """
    def __init__(self, dashboard):
        super().__init__(dashboard)
        self.implement_offset = (0,0,-95)
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
            print("Not connected to arm!")
            return False
        return True


class VacuumGrip(Attachment):
    """
    VacuumGrip class

    Args:
        dashboard (dobot_api.dobot_api_dashboard): Dobot API Dashboard object
    """
    def __init__(self, dashboard):
        super().__init__(dashboard)
        self.implement_offset = (0,0,-60)
        return

    def push(self, duration=0):
        """
        Expel air

        Args:
            duration (int, optional): number of seconds to expel air. Defaults to 0.
            
        Returns:
            bool: whether action is successful
        """
        try:
            self.dashboard.DOExecute(2,1)
            if duration > 0:
                time.sleep(duration)
                self.dashboard.DOExecute(2,0)
                time.sleep(1)
        except (AttributeError, OSError):
            print("Not connected to arm!")
            return False
        return True

    def drop(self):
        """
        Let go of object
        
        Returns:
            bool: whether action is successful
        """
        return self.push(0.5)
    
    def grab(self):
        """
        Pick up object
        
        Returns:
            bool: whether action is successful
        """
        return self.pull(3)
    
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
            print("Not connected to arm!")
            return False
        return True
    
    def pull(self, duration=0):
        """
        Inhale air

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
            return False
        return True


ATTACHMENTS = [TwoJawGrip, VacuumGrip]
ATTACHMENT_NAMES = ['TwoJawGrip', 'VacuumGrip']
