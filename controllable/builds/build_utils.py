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

# Third party imports
import yaml # pip install pyyaml

# Local application imports
print(f"Import: OK <{__name__}>")

class Setup(object):
    """
    Base Setup class
    """
    def __init__(self, *args, **kwargs):
        self.positions = {}
        self._config = {}
        self._flags = {}
        pass
    
    def _connect(self, *args, **kwargs):
        """
        Connect setup components
        """
        return
    
    def _get_class(self, module, dot_notation:str):
        """
        Retrieve the relevant class from the module

        Args:
            module (module): module / package
            dot_notation (str): dot notation of class / module / package

        Returns:
            class: relevant class
        """
        _class = module
        for child in dot_notation.split('.'):
            _class = getattr(_class, child)
        return _class


class Controller(object):
    """
    Base Controller class
    """
    def __init__(self, *args, **kwargs):
        pass
    
    def _decodeDetails(self, details:dict):
        """
        Decode dictionary of configuration details to get np.ndarrays and tuples

        Args:
            details (dict): dictionary of configuration details

        Returns:
            dict: dictionary of configuration details
        """
        for k,v in details.items():
            if type(v) != dict:
                continue
            if "tuple" in v.keys():
                details[k] = tuple(v['tuple'])
            elif "array" in v.keys():
                details[k] = np.array(v['array'])
        return details
    
    def _isOverrun(self, start_time:float, timeout):
        """
        Check whether the process has timed out

        Args:
            start_time (float): start time in seconds since epoch
            timeout (float): timeout duration

        Returns:
            bool: whether process has overrun
        """
        if timeout!=None and time.time() - start_time > timeout:
            return True
        return False
    
    def _readPlans(self, config_file:str, config_option:int):
        """
        Read configuration file (yaml)

        Args:
            config_file (str): filename of configuration file
            config_option (int): option index to use

        Returns:
            dict: dictionary of configuration parameters
        """
        yml = pkgutil.get_data(__name__, config_file).decode('utf-8')
        configs = yaml.safe_load(yml)
        config = configs[config_option]
        for obj in config.keys():
            if obj == 'labelled_positions':
                continue
            settings = config[obj]['settings']
            config[obj]['settings'] = self._decodeDetails(settings)
        return config
    
    # GUI methods
    def _gui_build_window(self, *args, **kwargs):
        return
    def _gui_disable_interface(self, *args, **kwargs):
        return
    def _gui_loop(self, *args, **kwargs):
        return
    