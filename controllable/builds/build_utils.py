# %% -*- coding: utf-8 -*-
"""
Created: Tue 2022/11/01 17:13:35
@author: Chang Jie

Notes / actionables:
-
"""
# Standard library imports
import numpy as np
import pkgutil
import time
import yaml

# Third party imports

# Local application imports
print(f"Import: OK <{__name__}>")

class BaseSetup(object):
    def __init__(self, *args, **kwargs):
        self.flags = {}
        self.positions = {}
        self._config = {}
        pass
    
    def _checkInputs(self, **kwargs):
        keys = list(kwargs.keys())
        if any(len(kwargs[key]) != len(kwargs[keys[0]]) for key in keys):
            raise Exception(f"Ensure the lengths of these inputs are the same: {', '.join(keys)}")
        return
    
    def _connect(self, *args, **kwargs):
        return
    
    def _getClass(self, module, dot_notation):
        _class = module
        for child in dot_notation.split('.'):
            _class = getattr(_class, child)
        return _class
    
class BaseProgram(object):
    def __init__(self, *args, **kwargs):
        pass
    
    def _decodeDetails(self, details):
        """
        Decode JSON representation of keyword arguments for Dobot initialisation

        Args:
            details (dict): dictionary of keyword, value pairs.
        """
        for k,v in details.items():
            if type(v) != dict:
                continue
            if "tuple" in v.keys():
                details[k] = tuple(v['tuple'])
            elif "array" in v.keys():
                details[k] = np.array(v['array'])
        return details
    
    def _isOverrun(self, start_time, timeout):
        if timeout!=None and time.time() - start_time > timeout:
            return True
        return False
    
    def _readPlans(self, config_file, config_option):
        yml = pkgutil.get_data(__name__, config_file).decode('utf-8')
        configs = yaml.safe_load(yml)
        config = configs[config_option]
        for obj in config.keys():
            settings = config[obj]['settings']
            print(settings)
            config[obj]['settings'] = self._decodeDetails(settings)
        return config
    
    # GUI methods
    def _gui_build_window(self, *args, **kwargs):
        return
    def _gui_disable_interface(self, *args, **kwargs):
        return
    def _gui_loop(self, *args, **kwargs):
        return
    