# %% -*- coding: utf-8 -*-
"""
Created: Tue 2022/11/01 17:13:35
@author: Chang Jie

Notes / actionables:
-
"""
# Standard library imports
import numpy as np
import time

# Third party imports

# Local application imports
from ...misc import Helper
from ... import Measure
from ... import Move
print(f"Import: OK <{__name__}>")

CNC_SPEED = 200
CONFIG_FILE = "config.yaml"

class PrimitivSetup(object):
    def __init__(self, config=CONFIG_FILE, config_option=0, ignore_connections=False, **kwargs):
        self.components = {}
        self.tool_offset = (0,0,0)
        self.positions = {}
        self._config = Helper.read_plans(__name__, config, config_option)
        self._flags = {}
        self._connect(ignore_connections=ignore_connections)
        pass
    
    @property
    def measurer(self):
        return self.components.get('measure')

    @property
    def mover(self):
        return self.components.get('move')
    
    @property
    def viewer(self):
        return self.components.get('view')
    
    def _connect(self, ignore_connections=False):
        for component in self._config:
            if component not in ['measure','move']:
                continue
            component_module = component.split('_')[0].title()
            component_class = Helper.get_class(component_module, self._config[component]['class'])
            self.components[component] = component_class(**self._config[component]['settings'])
            
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

    def measureAt(self, position):
        self.align(self.tool_offset, position, safe_height='up')
        self.measurer.measure()
        return

    def reset(self):
        self.mover.home()
        self.measurer.reset()
        return
    
    # Measure methods
    def getData(self):
        return self.measurer.getData()
    def loadProgram(self, program, params={}):
        return self.measurer.loadProgram(program, params)
    def saveData(self, filename):
        return self.measurer.saveData(filename)
    
    # Move methods
    def home(self):
        return self.mover.home()
    
    # TODO: Deprecate
    def labelHeight(self, name, z_height, overwrite=False):
        if name not in self.positions.keys() or overwrite:
            self.mover.heights[name] = z_height
        else:
            raise Exception(f"The height '{name}' has already been defined at: {self.mover.heights[name]}")
        return
    def labelHeights(self, names, z_heights, overwrite=False):
        properties = Helper.zip_inputs('names', names=names, z_heights=z_heights)
        for name,z_height in properties.values():
            self.labelHeight(name, z_height, overwrite)
        return
    def labelPosition(self, name, coord, overwrite=False):
        if name not in self.positions.keys() or overwrite:
            self.positions[name] = coord
        else:
            raise Exception(f"The position '{name}' has already been defined at: {self.positions[name]}")
        return
    def labelPositions(self, names, coords, overwrite=False):
        properties = Helper.zip_inputs('names', names=names, coords=coords)
        for name,coord in properties.values():
            self.labelPosition(name, coord, overwrite)
        return
