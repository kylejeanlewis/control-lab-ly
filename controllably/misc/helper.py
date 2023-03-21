# %% -*- coding: utf-8 -*-
"""
Created: Tue 2022/11/02 17:13:35
@author: Chang Jie

Notes / actionables:
-
"""
# Standard library imports
from datetime import datetime
import importlib
import json
import numpy as np
import os
import pandas as pd
import pkgutil
import time
import uuid

# Third party imports
import serial.tools.list_ports # pip install pyserial
import yaml # pip install pyyaml

# Local application imports
from . import decorators
print(f"Import: OK <{__name__}>")

class Helper:
    """
    Helper class with miscellaneous methods
    """
    def __init__(self):
        self.safety_countdown = 3
        self.safety_mode = None
        pass
    
    # Static methods
    @staticmethod
    def create_folder(parent_folder:str = None, child_folder:str = None):
        """
        Check and create folder if it does not exist

        Args:
            parent_folder (str, optional): parent folder directory. Defaults to None.
            child_folder (str, optional): child folder directory. Defaults to None.
        """
        main_folder = datetime.now().strftime("%Y-%m-%d_%H%M")
        if parent_folder:
            main_folder = '/'.join([parent_folder, main_folder])
        folder = '/'.join([main_folder, child_folder]) if child_folder else main_folder
        if not os.path.exists(folder):
            os.makedirs(folder)
        return main_folder
    
    # @staticmethod
    # def get_class(dot_notation:str):
    #     """
    #     Retrieve the relevant class from the sub-package

    #     Args:
    #         module (str): sub-package name
    #         dot_notation (str): dot notation of class / module / package

    #     Returns:
    #         class: relevant class
    #     """
    #     print('\n')
    #     top_package = __name__.split('.')[0]
    #     import_path = f'{top_package}.{dot_notation}'
    #     package = importlib.import_module('.'.join(import_path.split('.')[:-1]))
    #     _class = getattr(package, import_path.split('.')[-1])
    #     return _class
        
    @staticmethod
    def get_method_names(obj):
        """
        Get the names of the methods in object (class/instance)

        Args:
            obj (any): object of interest

        Returns:
            list: list of method names
        """
        method_list = []
        # attribute is a string representing the attribute name
        for attribute in dir(obj):
            # Get the attribute value
            attribute_value = getattr(obj, attribute)
            # Check that it is callable; Filter all dunder (__ prefix) methods
            if callable(attribute_value) and not attribute.startswith('__'):
                method_list.append(attribute)
        return method_list
    
    @staticmethod
    def get_node():
        """
        Display the machine's unique identifier

        Returns:
            str: machine unique identifier
        """
        return str(uuid.getnode())
    
    @staticmethod
    def get_ports():
        """
        Get available ports

        Returns:
            list: list of connected serial ports
        """
        com_ports = []
        ports = serial.tools.list_ports.comports()
        for port, desc, hwid in sorted(ports):
            com_ports.append(str(port))
            print(f"{port}: {desc} [{hwid}]")
        if len(ports) == 0:
            print("No ports detected!")
            return ['']
        return com_ports
    
    @staticmethod
    def is_overrun(start_time:float, timeout:float):
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
    
    @staticmethod
    def pretty_print_duration(total_time:float):
        """
        Display time duration (s) as HH:MM:SS text

        Args:
            total_time (float): duration in seconds

        Returns:
            str: formatted time string
        """
        m, s = divmod(total_time, 60)
        h, m = divmod(m, 60)
        return f'{int(h)}hr {int(m)}min {int(s):02}sec'
    
    @staticmethod
    def read_json(json_file:str, package:str = None):
        """
        Read JSON file

        Args:
            json_file (str): JSON filepath
            package (str, optional): name of package to look in. Defaults to None.

        Returns:
            dict: dictionary loaded from JSON file
        """
        if package is not None:
            jsn = pkgutil.get_data(package, json_file).decode('utf-8')
        else:
            with open(json_file) as file:
                jsn = file.read()
        return json.loads(jsn)
    
    @staticmethod
    def read_yaml(yaml_file:str, package:str = None):
        """
        Read YAML file

        Args:
            yaml_file (str): YAML filepath
            package (str, optional): name of package to look in. Defaults to None.

        Returns:
            dict: dictionary loaded from YAML file
        """
        if package is not None:
            yml = pkgutil.get_data(package, yaml_file).decode('utf-8')
        else:
            with open(yaml_file) as file:
                yml = file.read()
        return yaml.safe_load(yml)
    
    @staticmethod
    def zip_inputs(primary_keyword:str, **kwargs):
        """
        Checks and zips multiple keyword arguments of lists into dictionary

        Args:
            primary_keyword (str): primary keyword to be used as key

        Raises:
            Exception: Inputs have to be of the same length

        Returns:
            dict: dictionary of (primary keyword, kwargs)
        """
        input_length = len(kwargs[primary_keyword])
        keys = list(kwargs.keys())
        for key, value in kwargs.items():
            if type(value) != list:
                if type(value) in [tuple, set]:
                    kwargs[key] = list(value)
                else:
                    value = [value]
                    kwargs[key] = value * input_length
        if not all(len(kwargs[key]) == input_length for key in keys):
            raise Exception(f"Ensure the lengths of these inputs are the same: {', '.join(keys)}")
        kwargs_df = pd.DataFrame(kwargs)
        kwargs_df.set_index(primary_keyword, drop=False, inplace=True)
        return kwargs_df.to_dict('index')
    
    # Class methods
    # @classmethod
    # def get_details(cls, configs:dict, addresses:dict = {}):
    #     """
    #     Decode dictionary of configuration details to get np.ndarrays and tuples

    #     Args:
    #         configs (dict): dictionary of configuration details
    #         addresses (dict, optional): dictionary of registered addresses. Defaults to {}.

    #     Returns:
    #         dict: dictionary of configuration details
    #     """
    #     for name, details in configs.items():
    #         settings = details.get('settings', {})
            
    #         for key,value in settings.items():
    #             if key == 'component_config':
    #                 value = cls.get_details(value, addresses=addresses)
    #             if type(value) == str:
    #                 if key in ['cam_index', 'port'] and value.startswith('__'):
    #                     settings[key] = addresses.get(key, {}).get(settings[key], value)
    #             if type(value) == dict:
    #                 if "tuple" in value:
    #                     settings[key] = tuple(value['tuple'])
    #                 elif "array" in value:
    #                     settings[key] = np.array(value['array'])

    #         configs[name] = details
    #     return configs
    
    # @classmethod
    # def get_machine_addresses(cls, registry:dict):
    #     """
    #     Get the appropriate addresses for current machine

    #     Args:
    #         registry (str): dictionary of yaml file with com port addresses and camera ids

    #     Returns:
    #         dict: dictionary of com port addresses and camera ids for current machine
    #     """
    #     node_id = cls.get_node()
    #     addresses = registry.get('machine_id',{}).get(node_id,{})
    #     if len(addresses) == 0:
    #         print("\nAppend machine id and camera ids/port addresses to registry file")
    #         print(yaml.dump(registry))
    #         raise Exception(f"Machine not yet registered. (Current machine id: {node_id})")
    #     return addresses
    
    # @classmethod
    # def get_plans(cls, config_file:str, registry_file:str = None, package:str = None):
    #     """
    #     Read configuration file (yaml) and get details

    #     Args:
    #         config_file (str): filename of configuration file
    #         registry_file (str, optional): filename of registry file. Defaults to None.
    #         package (str, optional): name of package to look in. Defaults to None.

    #     Returns:
    #         dict: dictionary of configuration parameters
    #     """
    #     configs = cls.read_yaml(config_file, package)
    #     registry = cls.read_yaml(registry_file, package)
    #     addresses = cls.get_machine_addresses(registry=registry)
    #     configs = cls.get_details(configs, addresses=addresses)
    #     return configs
    
    # @classmethod
    # def load_components(cls, config:dict):
    #     """
    #     Load components of compound tools

    #     Args:
    #         config (dict): dictionary of configuration parameters

    #     Returns:
    #         dict: dictionary of component tools
    #     """
    #     components = {}
    #     for name, details in config.items():
    #         _module = details.get('module')
    #         if _module is None:
    #             continue
    #         dot_notation = [_module, details.get('class', '')]
    #         _class = cls.get_class('.'.join(dot_notation))
    #         settings = details.get('settings', {})
    #         components[name] = _class(**settings)
    #     return components
    
    # Instance methods
    def safety_measures(self, func):
        return decorators.safety_measures(mode=self.safety_mode, countdown=self.safety_countdown)(func=func)
    
    # NOTE: DEPRECATE
    @classmethod
    def display_ports(cls):
        """
        Get available ports

        Returns:
            list: list of connected serial ports
        """
        print("'display_ports' method to be deprecated. Use 'get_ports' instead.")
        return cls.get_ports()


HELPER = Helper() 
"""NOTE: importing HELPER gives the same instance of the 'Helper' class wherever you import it"""
