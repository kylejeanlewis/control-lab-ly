# %% -*- coding: utf-8 -*-
"""
Created: Tue 2022/11/01 17:13:35
@author: Chang Jie

Notes / actionables:
-
"""
# Standard library imports
import os
import pandas as pd
import pkgutil
import time
import yaml

# Third party imports

# Local application imports
from ..build_utils import BaseProgram
from .routines import Setup
print(f"Import: OK <{__name__}>")

CONFIG_FILE = 'config.yaml'

class Program(BaseProgram):
    def __init__(self, ignore_connections=False, config_option=0):
        self._config = self._readPlans(CONFIG_FILE, config_option)
        self.setup = Setup(self._config, ignore_connections)
        self.window = None
        self.flags = {
            'force_stop': False
        }
        return
    
    # Main methods
    def _assignSteps(self):
        return
    
    def loadRecipe(self, reagents_file='', recipe_file='', reagents_df=None, recipe_df=None):
        return
    
    def loadScheduler(self):
        return
    
    def prepareSetup(self, fill_sequence=[], manual_fill=False):
        return
    
    def queue(self, maker_chn, rest=True, new_thread=True):
        return
    
    def reset(self, hardware_only=True):
        return

    def runExperiment(self, timeout=None):
        return
    
    def start(self, timeout=None):
        return
    
    # Component methods
    def labelHeight(self, name, z_height, overwrite=False):
        return self.setup.labelHeight(self, name, z_height, overwrite)
    def labelHeights(self, names, z_heights, overwrite=False):
        return self.setup.labelHeights(self, names, z_heights, overwrite)
    def labelPosition(self, name, coord, overwrite=False):
        return self.setup.labelPosition(name, coord, overwrite)
    def labelPositions(self, names, coords, overwrite=False):
        return self.setup.labelPositions(names, coords, overwrite)
    def loadProgram(self, program, params={}):
        return self.setup.measurer.loadProgram(program, params)

    # GUI methods
    def _gui_build_window(self):
        return
    def _gui_disable_interface(self):
        return
    def _gui_loop(self):
        return
    