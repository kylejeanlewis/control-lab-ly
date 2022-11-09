# %% -*- coding: utf-8 -*-
"""
Adapted from @jaycecheng spinutils

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
from .routines import Setup
print(f"Import: OK <{__name__}>")

CONFIG_FILE = 'config.yaml'

class Program(object):
    def __init__(self, ignore_connections=False, recover_state_from_file=''):
        self._config = self._readPlans(CONFIG_FILE)
        self.setup = Setup(self._config, ignore_connections)
        self.window = None
        self.flags = {
            'force_stop': False
        }
        return
    
    # Main methods
    def _assignSteps(self):
        return
    
    def _isOverrun(self, start_time, timeout):
        if timeout!=None and time.time() - start_time > timeout:
            # log_now(f'Exceeded runtime of {timeout}s', True)
            return True
        return False
    
    def _readPlans(self, config_file):
        yml = pkgutil.get_data(__name__, config_file).decode('utf-8')
        config = yaml.full_load(yml)
        return config
    
    def _readState(self, filename=''):
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
    
    def saveState(self, filename=''):
        return
    
    def start(self, timeout=None):
        return
    
    # Component methods
    def getReagents(self, channels=[]):
        return self.setup.liquid.getReagents(channels=channels)
    def getVolumes(self, channels=[]):
        return self.setup.liquid.getVolumes(channels=channels)
    def labelPosition(self, name, coord, overwrite=False):
        return self.setup.labelPosition(name, coord, overwrite)
    def labelPositions(self, names, coords, overwrite=False):
        return self.setup.labelPositions(names, coords, overwrite)

    # GUI methods
    def _gui_build_window(self):
        return
    def _gui_disable_interface(self):
        return
    def _gui_loop(self):
        return
    