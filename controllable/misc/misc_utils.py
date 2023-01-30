# %% -*- coding: utf-8 -*-
"""
Created: Tue 2022/11/02 17:13:35
@author: Chang Jie

Notes / actionables:
-
"""
# Standard library imports
from datetime import date, datetime
import importlib
import numpy as np
import os
import pandas as pd
import pkgutil
import time

# Third party imports
import serial.tools.list_ports # pip install pyserial
import yaml # pip install pyyaml

# Local application imports
print(f"Import: OK <{__name__}>")

class Helper(object):
    """
    Helper class with miscellaneous methods
    """
    def __init__(self):
        self.all_logs = []
        self.logs = {}
        pass
    
    # @staticmethod
    # def create_folder(parent_folder:str):
    #     now = datetime.now().strftime("%Y-%m-%d %H-%M-%S")
    #     folder_name = f"{parent_folder}/{now}"
    #     if not os.path.exists(folder_name):
    #         os.makedirs(folder_name)
    #     return
    
    @staticmethod
    def display_ports():
        """
        Displays available ports

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
    def get_class(module, dot_notation:str):
        """
        Retrieve the relevant class from the sub-package

        Args:
            package (module): sub-package
            dot_notation (str): dot notation of class / module / package

        Returns:
            class: relevant class
        """
        top_package = __name__.split('.')[0]
        import_path = f'{top_package}.{module}.{dot_notation}'
        package = importlib.import_module('.'.join(import_path.split('.')[:-1]))
        _class = getattr(package, import_path.split('.')[-1])
        return _class
    
    @staticmethod
    def get_details(details:dict):
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
    def is_overrun(start_time:float, timeout):
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
    
    @classmethod
    def read_plans(cls, config_file:str, config_option:int, package:str = None):
        """
        Read configuration file (yaml)

        Args:
            config_file (str): filename of configuration file
            config_option (int): option index to use
            package (str, optional): name of package to look in. Defaults to None.

        Returns:
            dict: dictionary of configuration parameters
        """
        try:
            yml = pkgutil.get_data(package, config_file).decode('utf-8')
        except AttributeError:
            with open(config_file) as file:
                yml = file.read()
        configs = yaml.safe_load(yml)
        config = configs[config_option]
        for obj in config.keys():
            if obj == 'labelled_positions':
                continue
            if obj == 'deck':
                continue
            settings = config[obj]['settings']
            config[obj]['settings'] = cls.get_details(settings)
        return config

    def log_now(self, message:str, group=None):
        """
        Add log with timestamp

        Args:
            message (str): message to be logged
            group (str, optional): message group. Defaults to None.

        Returns:
            str: log message with timestamp
        """
        log = time.strftime("%H:%M:%S", time.localtime()) + ' >> ' + message
        self.all_logs.append(log)
        if group:
            if group not in self.logs.keys():
                self.logs[group] = []
            self.logs[group].append(message)
        return log

    def reset_logs(self):
        """
        Reset all logs
        """
        self.all_logs = []
        self.logs = {}
        return

    def save_logs(self, groups=[], folder=''):
        """
        Write logs into txt files

        Args:
            groups (list, optional): list of log messages. Defaults to [].
            folder (str, optional): folder to save to. Defaults to ''.
        """
        dst_folder = '/'.join([folder, 'logs'])
        if not os.path.exists(dst_folder):
            os.makedirs(dst_folder)
        
        with open(f'{dst_folder}/activity_log.txt', 'w') as f:
            for line in self.all_logs:
                f.write(line + '\n')
        
        for group in groups:
            if group not in self.logs.keys():
                print(f"'{group}' not found in log groups!")
                continue
            with open(f'{dst_folder}/{group}_log.txt', 'w') as f:
                for line in self.logs[group]:
                    f.write(line + '\n')
        return

LOGGER = Helper() 
"""NOTE: importing LOGGER gives the same instance of the 'Helper' class wherever you import it"""
