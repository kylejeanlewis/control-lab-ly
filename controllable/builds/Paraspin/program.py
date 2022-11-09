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
import pandas as pd
import pkgutil
import threading
import time
import yaml

# Third party imports

# Local application imports
from .routines import Setup
print(f"Import: OK <{__name__}>")

CONFIG_FILE = 'config.yaml'

class Program(object):
    def __init__(self, ignore_connections=False):
        self._config = self._readPlans(CONFIG_FILE)
        self.setup = Setup(self._config, ignore_connections)
        self.window = None
        
        self.reagents_df = None
        self.recipe_df = None
        return
    
    # GUI methods
    def _build_window(self):
        return
    def _disable_interface(self):
        return
    def _loop_gui(self):
        return
    
    # Main methods
    def assignSteps(self):
        return
    def _checkInputs(self):
        return
    def _checkOverrun(self):
        return
    def _checkVolumes(self):
        return
    def loadRecipe(self, reagents_file='', recipe_file='', reagents_df=None, recipe_df=None): # read recipe
        if type(reagents_df) == type(None):
            if len(reagents_file) == 0:
                raise Exception('Please input either filename or DataFrame for reagents.')
            columns = ['channel', 'reagent', 'volume']
            reagents_df = pd.read_csv(reagents_file)
            if set(reagents_df.columns) != set(columns):
                raise Exception(f"Ensure only these headers are present: {', '.join(columns)}")
        self.reagents_df = reagents_df
        
        if type(recipe_df) == type(None):
            if len(recipe_file) == 0:
                raise Exception('Please input either filename or DataFrame for recipe.')
            columns = ['channels', 'reagent', 'volume', 'soak_time', 'spin_speed', 'spin_time']
            recipe_df = pd.read_csv(recipe_file)
            if set(recipe_df.columns) != set(columns):
                raise Exception(f"Ensure only these headers are present: {', '.join(columns)}")
        self.recipe_df = recipe_df
        return
    def loadScheduler(self):
        return
    def prepareSetup(self, manual_fill=False):
        self.setup.fillLiquids(channels, reagents, vols, pause=manual_fill)
        return
    def queue(self): #give instructions
        return
    def _readPlans(self, config_file): # read config
        yml = pkgutil.get_data(__name__, config_file).decode('utf-8')
        config = yaml.full_load(yml)
        return config
    def runExperiment(self):
        return
    def saveState(self):
        return
    def start(self):
        return
    