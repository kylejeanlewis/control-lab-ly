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
    def __init__(self, config_file=CONFIG_FILE, ignore_connections=False, config_option=0):
        self._config = self._readPlans(config_file, config_option)
        self.setup = Setup(self._config, ignore_connections)
        self.window = None
        self.flags = {
            'force_stop': False
        }
        
        self._all_steps = {}
        self._default_folder = __name__.split('builds.')[1].replace('.', '/'),
        self._executed = []
        self._file_fields = {
            'folder': '',
            'name': '',
            'part': '',
            'run': 0,
            'ext': ''
        }
        self._file_template = '{folder}/{name}_{part}_{run}.{ext}'
        self._run = 0
        return
    
    # Main methods
    def _assignSteps(self):
        self._all_steps = {}
        for part,position in enumerate(self.setup.positions.get('sample')):
            self._all_steps[part] = [position]
        return
    
    def loadProgram(self, program, params={}):
        return self.setup.loadProgram(program, params)
    
    def getPositions(self, filename=''):
        self.setup.positions['sample'] = []
        
        return
    
    def loadScheduler(self):
        return
    
    def execute(self, part):
        position = self._all_steps[part].pop(0)
        self.setup.measure(position)
        self.saveData(part)
        self._executed.append((part, position))
        return
    
    def reset(self, hardware_only=True):
        self.setup.reset()
        if not hardware_only:
            self._all_steps = {}
            self._executed = []
            self._file_fields = {
                'folder': '',
                'name': '',
                'part': '',
                'run': 0,
                'ext': ''
            }
        return

    def runExperiment(self, timeout=None):
        return
    
    def saveData(self, part):
        folder = self._file_fields.get('folder')
        if not os.path.exists(folder):
            os.makedirs(folder)
        
        self._file_fields['part'] = part
        self._file_fields['ext'] = 'csv'
        csv_filename = self._file_template.format(**self._file_fields)
        while os.path.exists(csv_filename):
            self._file_fields['run'] += 1
            csv_filename = self._file_template.format(**self._file_fields)
        self.setup.saveData(csv_filename)
        return
    
    def start(self, sample_name, folder='', timeout=None):
        self._file_fields['folder'] = folder if len(folder) else self._default_folder
        self._file_fields['name'] = sample_name
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
    