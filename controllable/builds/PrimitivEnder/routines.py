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
measurer_class = Measure.Electrical.Keithley.Keithley

CNC_SPEED = 200

class Setup(object):
    def __init__(self, config, ignore_connections=False):
        self.mover = None
        self.measurer = None
        self.flags = {}
        self.positions = {}
        
        self._config = config
        self._connect(ignore_connections=ignore_connections)
        pass
    
    def _checkInputs(self, **kwargs):
        keys = list(kwargs.keys())
        if any(len(kwargs[key]) != len(kwargs[keys[0]]) for key in keys):
            raise Exception(f"Ensure the lengths of these inputs are the same: {', '.join(keys)}")
        return
    
    def _checkPositions(self, wait=2, pause=False):
        return
    
    def _connect(self, ignore_connections=False):
        self.mover = mover_class(**self._config['mover_settings'])
        self.measurer = measurer_class(**self._config['measurer_settings'])
        
        try:
            self.labelHeights(**self._config['height_settings'])
        except KeyError:
            print('Heights not set.')
        return
    
    def align(self, offset, position):
        coord = np.array(position) - np.array(offset)
        if not self.mover.isFeasible(coord):
            raise Exception("Selected position is not feasible.")
        self.mover.moveTo(coord)
        
        # Time the wait
        distance = np.linalg.norm(coord - np.array(self.mover.coordinates))
        t_align = distance / CNC_SPEED + 2
        time.sleep(t_align)
        return
    
    def home(self):
        return self.mover.home()
    
    def labelHeight(self, name, z_height, overwrite=False):
        if name not in self.positions.keys() or overwrite:
            self.mover.heights[name] = z_height
        else:
            raise Exception(f"The height '{name}' has already been defined at: {self.mover.heights[name]}")
        return
    
    def labelHeights(self, names, z_heights, overwrite=False):
        self._checkInputs(names=names, z_heights=z_heights)
        for name,z_height in zip(names, z_heights):
            self.labelPosition(name, z_height, overwrite)
        return
    
    def labelPosition(self, name, coord, overwrite=False):
        if name not in self.positions.keys() or overwrite:
            self.positions[name] = coord
        else:
            raise Exception(f"The position '{name}' has already been defined at: {self.positions[name]}")
        return
    
    def labelPositions(self, names, coords, overwrite=False):
        self._checkInputs(names=names, coords=coords)
        for name,coord in zip(names, coords):
            self.labelPosition(name, coord, overwrite)
        return

    def reset(self, home=True, wait=0, pause=False):
        return
    
    