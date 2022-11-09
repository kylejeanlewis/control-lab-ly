# %% -*- coding: utf-8 -*-
"""
Adapted from @jaycecheng spinutils

Created: Tue 2022/11/01 17:13:35
@author: Chang Jie

Notes / actionables:
-
"""
# Standard library imports
import numpy as np
import threading
import time

# Third party imports

# Local application imports
from ... import Measure
from ... import Move
print(f"Import: OK <{__name__}>")

mover_class = Move.Cartesian.Primitiv
measure_class = Measure.Electrical.Keithley.Keithley

class Setup(object):
    def __init__(self, config, ignore_connections=False):
        self.mover = None
        self.measure = None
        self.flags = {}
        self.positions = {}
        
        self._config = config
        self._connect(ignore_connections=ignore_connections)
        pass
    
    def _checkInputs(self, **kwargs):
        return
    
    def _checkPositions(self, wait=2, pause=False):
        return
    
    def _connect(self, diagnostic=True, ignore_connections=False):
        return
    
    def align(self, offset, position):
        return
    
    def home(self):
        return self.mover.home()
    
    def labelPosition(self, name, coord, overwrite=False):
        return
    
    def labelPositions(self, names, coords, overwrite=False):
        return
    
    def rest(self, home=True):
        return

    def reset(self, home=True, wait=0, pause=False):
        return