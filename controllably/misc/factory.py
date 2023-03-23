# %% -*- coding: utf-8 -*-
"""
Created: Tue 2022/11/02 17:13:35
@author: Chang Jie

Notes / actionables:
-
"""
# Standard library imports
import importlib
import numpy as np
from typing import Callable, Optional

# Third party imports
import yaml # pip install pyyaml

# Local application imports
from . import helper
print(f"Import: OK <{__name__}>")

# packages = {}

def get_class(dot_notation:str) -> Callable:
    """
    Retrieve the relevant class from the sub-package

    Args:
        module (str): sub-package name
        dot_notation (str): dot notation of class / module / package

    Returns:
        class: relevant class
    """
    print('\n')
    top_package = __name__.split('.')[0]
    import_path = f'{top_package}.{dot_notation}'
    package = importlib.import_module('.'.join(import_path.split('.')[:-1]))
    _class = getattr(package, import_path.split('.')[-1])
    return _class

def get_details(configs:dict, addresses:dict = {}) -> dict:
    """
    Decode dictionary of configuration details to get np.ndarrays and tuples

    Args:
        configs (dict): dictionary of configuration details
        addresses (dict, optional): dictionary of registered addresses. Defaults to {}.

    Returns:
        dict: dictionary of configuration details
    """
    for name, details in configs.items():
        settings = details.get('settings', {})
        
        for key,value in settings.items():
            if key == 'component_config':
                value = get_details(value, addresses=addresses)
            if type(value) == str:
                if key in ['cam_index', 'port'] and value.startswith('__'):
                    settings[key] = addresses.get(key, {}).get(settings[key], value)
            if type(value) == dict:
                if "tuple" in value:
                    settings[key] = tuple(value['tuple'])
                elif "array" in value:
                    settings[key] = np.array(value['array'])

        configs[name] = details
    return configs

def get_machine_addresses(registry:dict) -> dict:
    """
    Get the appropriate addresses for current machine

    Args:
        registry (str): dictionary of yaml file with com port addresses and camera ids

    Returns:
        dict: dictionary of com port addresses and camera ids for current machine
    """
    node_id = helper.get_node()
    addresses = registry.get('machine_id',{}).get(node_id,{})
    if len(addresses) == 0:
        print("\nAppend machine id and camera ids/port addresses to registry file")
        print(yaml.dump(registry))
        raise Exception(f"Machine not yet registered. (Current machine id: {node_id})")
    return addresses

def get_plans(config_file:str, registry_file:Optional[str] = None, package:Optional[str] = None) -> dict:
    """
    Read configuration file (yaml) and get details

    Args:
        config_file (str): filename of configuration file
        registry_file (str, optional): filename of registry file. Defaults to None.
        package (str, optional): name of package to look in. Defaults to None.

    Returns:
        dict: dictionary of configuration parameters
    """
    configs = helper.read_yaml(config_file, package)
    registry = helper.read_yaml(registry_file, package)
    addresses = get_machine_addresses(registry=registry)
    configs = get_details(configs, addresses=addresses)
    return configs

def load_components(config:dict) -> dict:
    """
    Load components of compound tools

    Args:
        config (dict): dictionary of configuration parameters

    Returns:
        dict: dictionary of component tools
    """
    components = {}
    for name, details in config.items():
        _module = details.get('module')
        if _module is None:
            continue
        dot_notation = [_module, details.get('class', '')]
        _class = get_class('.'.join(dot_notation))
        settings = details.get('settings', {})
        components[name] = _class(**settings)
    return components

# def register(_class:Callable, dot_notation:str):
#     nesting = dot_notation.split('.')
#     package = packages
#     for nest in nesting:
#         if nest not in package:
#             package[nest] = {}
#         package = package.get(nest, {})
#     print(packages)
#     return
