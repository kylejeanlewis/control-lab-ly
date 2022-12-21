# %% -*- coding: utf-8 -*-
"""
Created: Tue 2022/12/13 10:30:00
@author: Chang Jie

Notes / actionables:
- 
"""
# Standard library imports
import time

# Third party imports

# Local application imports
print(f"Import: OK <{__name__}>")

class Scheduler(object):
    def __init__(self):
        self._flags = {}
        return
    
    def decideNext(self, statuses, all_steps):
        for key, steps in all_steps.items():
            if statuses[key]['busy']:
                return None
            if len(steps):
                return key
        return None
    
    def setFlags(self, name, value):
        self._flags[name] = value
        return
    
    
class ScanningScheduler(Scheduler):
    def __init__(self):
        super().__init__()
        return
        
    def decideNext(self, statuses, all_steps):
        for key, steps in all_steps.items():
            if statuses[key]['busy']:
                continue
            if len(steps):
                return key
        return None
