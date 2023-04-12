# %% -*- coding: utf-8 -*-
"""

"""
# Standard library imports

# Third party imports

# Local application imports
print(f"Import: OK <{__name__}>")

class Scheduler(object):
    """
    Base Scheduler class. Sequential dispatch
    """
    def __init__(self):
        self._flags = {}
        return
    
    def decideNext(self, statuses:dict, all_steps:dict):
        """
        Determine which step to perform next

        Args:
            statuses (dict): dictionary of statuses
            all_steps (dict): dictionary of all remaining steps

        Returns:
            int, or None: key/index of next client to be served
        """
        for key, steps in all_steps.items():
            if statuses[key]['busy']:
                return None
            if len(steps):
                return key
        return None
    
    def setFlags(self, name:str, value):
        """
        Set flags in scheduler

        Args:
            name (str): name of key
            value (bool): flag value
        """
        self._flags[name] = value
        return
    
    
class ScanningScheduler(Scheduler):
    """
    Scanning Scheduler class. Dispatches the next available client.
    """
    def __init__(self):
        super().__init__()
        return
        
    def decideNext(self, statuses:dict, all_steps:dict):
        """
        Determine which step to perform next

        Args:
            statuses (dict): dictionary of statuses
            all_steps (dict): dictionary of all remaining steps

        Returns:
            int, or None: key/index of next client to be served
        """
        for key, steps in all_steps.items():
            if statuses[key]['busy']:
                continue
            if len(steps):
                return key
        return None
