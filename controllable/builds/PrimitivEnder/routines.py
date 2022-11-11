# %% -*- coding: utf-8 -*-
"""
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
from ..build_utils import BaseSetup
print(f"Import: OK <{__name__}>")

CNC_SPEED = 200

class Setup(BaseSetup):
    def __init__(self, config, ignore_connections=False, **kwargs):
        super().__init__(**kwargs)
        self.mover = None
        self.measurer = None
        self.viewer = None
        self.flags = {}
        self.positions = {}
        self.tool_offset = (0,0,0)
        
        self._config = config
        self._connect(ignore_connections=ignore_connections)
        pass
    
    def _connect(self, ignore_connections=False):
        mover_class = self._getClass(Move, self._config['mover']['class'])
        measurer_class = self._getClass(Measure, self._config['measurer']['class'])
        
        self.mover = mover_class(**self._config['mover']['settings'])
        self.measurer = measurer_class(**self._config['measurer']['settings'])
        
        try:
            self.labelHeights(**self._config['height']['settings'])
        except KeyError:
            print('Heights not set.')
        return
    
    def align(self, offset, position, jump_height='safe'):
        coord = np.array(position) - np.array(offset)
        if not self.mover.isFeasible(coord):
            raise Exception("Selected position is not feasible.")
        jump_z_height = self.mover.heights.get(jump_height)
        self.mover.moveTo(coord, jump_z_height=jump_z_height)
        
        # Time the wait
        distance = np.linalg.norm(coord - np.array(self.mover.coordinates))
        t_align = distance / CNC_SPEED + 2
        time.sleep(t_align)
        return
    
    def checkPositions(self, positions, wait=2, pause=False):
        for position in positions:
            self.align(self.tool_offset, position, safe_height=False)
            time.sleep(wait)
            if pause:
                input("Press 'Enter' to proceed.")
        return
    
    def getData(self):
        return self.measurer.getData()
    
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
            self.labelHeight(name, z_height, overwrite)
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

    def loadProgram(self, program, params={}):
        return self.measurer.loadProgram(program, params)

    def measure(self, position):
        self.align(self.tool_offset, position, safe_height='up')
        self.measurer.measure()
        return

    def reset(self):
        self.mover.home()
        self.measurer.reset()
        return
    
    def saveData(self, filename):
        return self.measurer.saveData(filename)
    