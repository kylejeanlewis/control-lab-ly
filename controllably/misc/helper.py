# %% -*- coding: utf-8 -*-
"""
This module holds the helper functions in Control.lab.ly.

Functions:
    create_folder
    get_machine_addresses
    get_method_names
    get_node
    get_plans
    get_ports
    is_overrun
    pretty_print_duration
    read_json
    read_yaml
    safety_measures (decorator)
    zip_inputs

Other constants and variables:
    safety_countdown (int)
    safety_mode (Optional[str])
"""
# Standard library imports
from __future__ import annotations
from datetime import datetime
import json
import os
import pandas as pd
import pkgutil
import time
from typing import Callable, Optional
import uuid

# Third party imports
import serial.tools.list_ports      # pip install pyserial
import yaml                         # pip install pyyaml

# Local application imports
from . import decorators
from . import factory
print(f"Import: OK <{__name__}>")

safety_countdown = 3
"""Safety countdown before executing move, in seconds"""
safety_mode = None
"""Safety level (`'high'`, `'low'`, `None`)"""

def create_folder(parent_folder:Optional[str] = None, child_folder:Optional[str] = None) -> str:
    """
    Check and create folder if it does not exist

    Args:
        parent_folder (Optional[str], optional): parent folder directory. Defaults to None.
        child_folder (Optional[str], optional): child folder directory. Defaults to None.
    
    Returns:
        str: name of main folder
    """
    main_folder = datetime.now().strftime("%Y-%m-%d_%H%M")
    if parent_folder:
        main_folder = '/'.join([parent_folder, main_folder])
    folder = '/'.join([main_folder, child_folder]) if child_folder else main_folder
    if not os.path.exists(folder):
        os.makedirs(folder)
    return main_folder

def get_machine_addresses(registry:dict) -> dict:
    """
    Get the appropriate addresses for current machine

    Args:
        registry (str): dictionary of yaml file with com port addresses and camera ids

    Returns:
        dict: dictionary of com port addresses and camera ids for current machine
    """
    node_id = get_node()
    addresses = registry.get('machine_id',{}).get(node_id,{})
    if len(addresses) == 0:
        print("\nAppend machine id and camera ids/port addresses to registry file")
        print(yaml.dump(registry))
        raise Exception(f"Machine not yet registered. (Current machine id: {node_id})")
    return addresses
    
def get_method_names(obj:Callable) -> list[str]:
    """
    Get the names of the methods in Callable object (class/instance)

    Args:
        obj (Callable): object of interest

    Returns:
        list[str]: list of method names
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

def get_node() -> str:
    """
    Display the machine's unique identifier

    Returns:
        str: machine unique identifier
    """
    return str(uuid.getnode())

def get_plans(config_file:str, registry_file:Optional[str] = None, package:Optional[str] = None) -> dict:
    """
    Read configuration file (yaml) and get details

    Args:
        config_file (str): filename of configuration file
        registry_file (Optional[str], optional): filename of registry file. Defaults to None.
        package (Optional[str], optional): name of package to look in. Defaults to None.

    Returns:
        dict: dictionary of configuration parameters
    """
    configs = read_yaml(config_file, package)
    registry = read_yaml(registry_file, package)
    addresses = get_machine_addresses(registry=registry)
    configs = factory.get_details(configs, addresses=addresses)
    return configs

def get_ports() -> list[str]:
    """
    Get available ports

    Returns:
        list[str]: list of connected serial ports
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

def is_overrun(start_time:float, timeout:float) -> bool:
    """
    Checks and returns whether the process has overrun

    Args:
        start_time (float): start time in seconds since epoch
        timeout (float): timeout duration

    Returns:
        bool: whether the process has overrun
    """
    if timeout!=None and time.perf_counter() - start_time > timeout:
        return True
    return False

def pretty_print_duration(total_time:float) -> str:
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

def read_json(json_file:str, package:Optional[str] = None) -> dict:
    """
    Read JSON file

    Args:
        json_file (str): JSON filepath
        package (Optional[str], optional): name of package to look in. Defaults to None.

    Returns:
        dict: dictionary loaded from JSON file
    """
    if package is not None:
        jsn = pkgutil.get_data(package, json_file).decode('utf-8')
    else:
        with open(json_file) as file:
            jsn = file.read()
    return json.loads(jsn)

def read_yaml(yaml_file:str, package:Optional[str] = None) -> dict:
    """
    Read YAML file

    Args:
        yaml_file (str): YAML filepath
        package (Optional[str], optional): name of package to look in. Defaults to None.

    Returns:
        dict: dictionary loaded from YAML file
    """
    if package is not None:
        yml = pkgutil.get_data(package, yaml_file).decode('utf-8')
    else:
        with open(yaml_file) as file:
            yml = file.read()
    return yaml.safe_load(yml)

def safety_measures(func:Callable) -> Callable:
    """
    Decorator to implement safety measure to movement actions

    Args:
        func (Callable): function to be wrapped

    Returns:
        Callable: wrapped function
    """
    return decorators.safety_measures(mode=safety_mode, countdown=safety_countdown)(func=func)

def zip_inputs(primary_keyword:str, **kwargs) -> dict:
    """
    Checks and zips multiple keyword arguments of lists into dictionary
    
    Args:
        primary_keyword (str): primary keyword to be used as key
    
    Kwargs:
        key, list[...]: {keyword, list of values} pairs

    Raises:
        Exception: Ensure the lengths of inputs are the same

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

__where__ = "misc.Helper"
factory.include_this_module(get_local_only=True)