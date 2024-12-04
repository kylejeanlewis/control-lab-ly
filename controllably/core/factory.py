# -*- coding: utf-8 -*-
""" 
This module contains functions to create and manage objects.

## Functions:
    `dict_to_named_tuple`: Creating named tuple from dictionary
    `dict_to_simple_namespace`: Convert dictionary to SimpleNamespace
    `get_class`: Retrieve the relevant class from the sub-package
    `get_imported_modules`: Get all imported modules
    `get_method_names`: Get the names of the methods in Callable object (Class/Instance)
    `get_plans`: Get available configurations
    `get_setup`: Load setup from files and return as NamedTuple or Platform
    `load_parts`: Load all parts of compound tools from configuration
    `load_setup_from_files`: Load and initialise setup
    `parse_configs`: Decode dictionary of configuration details to get tuples and `numpy.ndarray`
    `zip_kwargs_to_dict`: Checks and zips multiple keyword arguments of lists into dictionary

<i>Documentation last updated: 2024-11-16</i>
"""
# Standard library imports
import importlib
import inspect
import json
import logging
from pathlib import Path
import pprint
import sys
from types import SimpleNamespace
from typing import Callable, Sequence, NamedTuple, Type, Any

# Third party imports
import numpy as np

# Local application imports
from . import connection
from . import file_handler

_logger = logging.getLogger("controllably.core")
_logger.debug(f"Import: OK <{__name__}>")

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
logger.addHandler(handler)

def dict_to_named_tuple(d:dict, tuple_name:str = 'Setup') -> tuple:
    """
    Creating named tuple from dictionary

    Args:
        d (dict): dictionary to be transformed
        tuple_name (str, optional): name of new namedtuple type. Defaults to 'Setup'.

    Returns:
        tuple: named tuple from dictionary
    """
    field_list = []
    object_list = []
    for k,v in d.items():
        field_list.append((k, type(v)))
        object_list.append(v)
    
    # named_tuple = namedtuple(tuple_name, field_list)
    named_tuple = NamedTuple(tuple_name, field_list)
    logger.info(f"\nObjects created: {', '.join([f[0] for f in field_list])}")
    return named_tuple(*object_list)

def dict_to_simple_namespace(d:dict) -> SimpleNamespace:
    """
    Convert dictionary to SimpleNamespace

    Args:
        d (dict): dictionary to be transformed

    Returns:
        SimpleNamespace: SimpleNamespace object
    """
    return json.loads(json.dumps(d), object_hook=lambda item: SimpleNamespace(**item))

def get_class(module_name:str, class_name:str) -> Type[object]:
    """
    Retrieve the relevant class from the sub-package

    Args:
        module_name (str): name of the module using dot notation
        class_name (str): name of the class

    Returns:
        Type: target Class
    """
    _module = importlib.import_module(module_name)
    _class = getattr(_module, class_name)
    return _class

def get_imported_modules(interested_modules:str|Sequence[str]|None = None) -> dict:
    """
    Get all imported modules

    Args:
        interested_modules (str | Sequence[str] | None, optional): interested module(s). Defaults to None.

    Returns:
        dict: dictionary of imported modules
    """
    if isinstance(interested_modules, str):
        interested_modules = [interested_modules]
    elif isinstance(interested_modules, Sequence):
        interested_modules = list(interested_modules)
    else:
        interested_modules = []
    modules_of_interest = ['controllably', 'library'] + interested_modules
    def is_of_interest(module_name:str) -> bool:
        return any([module in module_name for module in set(modules_of_interest)])
    imports = {name:mod for name,mod in sys.modules.items() if is_of_interest(name)}
    
    objects = {}
    for mod in imports.values():
        members = dict(mem for mem in inspect.getmembers(mod) if not mem[0].startswith('_'))
        for name,obj in members.items():
            if not hasattr(obj, '__module__'):
                continue
            parent = obj.__module__
            if is_of_interest(parent):
                objects[name] = (obj,parent)
                
    modules = dict()
    for obj_name, (obj,mod) in objects.items():
        _temp = modules
        for level in mod.split('.'):
            if level not in _temp:
                _temp[level] = dict()
            _temp = _temp[level]
        _temp[obj_name] = obj
    return modules

def get_method_names(obj:Callable) -> list[str]:
    """
    Get the names of the methods in Callable object (Class/Instance)

    Args:
        obj (Callable): object of interest

    Returns:
        list[str]: list of method names
    """
    return [attr for attr in dir(obj) if callable(getattr(obj, attr)) and not attr.startswith('__')]

def get_plans(configs:dict, registry:dict|None = None) -> dict:
    """
    Get available configurations
    
    Args:
        configs (dict): dictionary of configurations
        registry (dict|None, optional): dictionary of addresses. Defaults to None.
    
    Returns:
        dict: dictionary of available configurations
    """
    addresses = connection.get_addresses(registry)
    configs = parse_configs(configs, addresses)
    return configs

def get_setup(
    config_file:Path|str, 
    registry_file:Path|str|None = None, 
    platform_type:Type|None = None
) -> tuple|Any:
    """
    Load setup from files and return as NamedTuple or Platform
    
    Args:
        config_file (Path|str): config filename
        registry_file (Path|str|None, optional): registry filename. Defaults to None.
        platform_type (Type|None, optional): target platform type. Defaults to None.
        
    Returns:
        tuple|Any: named tuple or Platform object
    """
    platform: NamedTuple = load_setup_from_files(config_file=config_file, registry_file=registry_file, create_tuple=True)
    if platform_type is None or len(platform_type.__annotations__) == 0:
        return platform
    return platform_type(**platform._asdict())

def load_parts(configs:dict, **kwargs) -> dict:
    """
    Load all parts of compound tools from configuration

    Args:
        config (dict): dictionary of configuration parameters

    Returns:
        dict: dictionary of part tools
    """
    parts = {}
    configs.update(kwargs)
    for name, details in configs.items():
        title = f'\n{name.upper()}'
        settings = details.get('settings', {})
        simulated = settings.get('simulation', False)
        title = title + ' [simulated]' if simulated else title
        logger.info(title)
        
        logger.debug(f'{pprint.pformat(details, indent=1, depth=4, sort_dicts=False)}\n')
        module_name = details.get('module')
        class_name = details.get('class')
        _class = get_class(module_name, class_name)
        
        parent = _class.__mro__[1].__name__
        if parent in ('Compound','Combined'):
            parts[name] = _class.fromConfig(settings)
        elif parent in ('Tool','Device'):
            parts[name] = _class.create(**settings)
        else:
            parts[name] = _class(**settings)
    return parts

def load_setup_from_files(
    config_file:Path|str, 
    registry_file:Path|str|None = None, 
    create_tuple:bool = True
) -> dict|tuple:
    """
    Load and initialise setup

    Args:
        config_file (Path|str): config filename
        registry_file (Path|str|None, optional): registry filename. Defaults to None.
        create_tuple (bool, optional): whether to return a named tuple, if not returns dictionary. Defaults to True.

    Returns:
        dict|tuple: dictionary or named tuple of setup objects
    """
    config_file = Path(config_file)
    registry_file = Path(registry_file) if registry_file is not None else None
    configs = file_handler.read_config_file(config_file)
    registry = file_handler.read_config_file(registry_file) if registry_file is not None else None
    plans = get_plans(configs, registry)
    shortcuts = plans.pop('SHORTCUTS',{})
    setup = load_parts(configs=plans)
    
    for name,value in shortcuts.items():
        parent, child = value.split('.')
        tool = setup.get(parent, None)
        if tool is None:
            logger.warning(f"Tool does not exist ({parent})")
            continue
        if not hasattr(tool, '_parts'):
            logger.warning(f"Tool ({parent}) does not have parts")
            continue
        setup[name] = getattr(tool.parts, child)
    if create_tuple:
        return dict_to_named_tuple(setup, tuple_name=config_file.stem)
    return setup

def parse_configs(configs:dict, addresses:dict|None = None) -> dict:
    """
    Decode dictionary of configuration details to get tuples and `numpy.ndarray`

    Args:
        configs (dict): dictionary of configuration details
        addresses (dict|None, optional): dictionary of registered addresses. Defaults to None.

    Returns:
        dict: dictionary of configuration details
    """
    addresses = {} if addresses is None else addresses
    for name, details in configs.items():
        settings = details.get('settings', {})
        
        for key,value in settings.items():
            if key == 'details':
                value = parse_configs(value, addresses=addresses)
            if type(value) == str:
                if key in ('cam_index', 'port') and value.startswith('__'):
                    settings[key] = addresses.get(key, {}).get(settings[key], value)
            if type(value) == dict:
                if "tuple" in value:
                    settings[key] = tuple(value['tuple'])
                elif "array" in value:
                    settings[key] = np.array(value['array'])

        configs[name] = details
    return configs

def zip_kwargs_to_dict(primary_key:str, kwargs:dict) -> dict:
    """ 
    Checks and zips multiple keyword arguments of lists into dictionary
    
    Args:
        primary_keyword (str): primary keyword to be used as key
        kwargs (dict): {keyword, list of values} pairs
        
    Returns:
        dict: dictionary of (primary keyword, kwargs)
        
    Raises:
        AssertionError: Ensure the lengths of inputs are the same
    """
    length = len(kwargs[primary_key])
    for key, value in kwargs.items():
        if isinstance(value, Sequence):
            continue
        if isinstance(value, set):
            kwargs[key] = list(value)
            continue
        kwargs[key] = [value]*length
    keys = list(kwargs.keys())
    assert all(len(kwargs[key]) == length for key in keys), f"Ensure the lengths of these inputs are the same: {', '.join(keys)}"
    primary_values = kwargs.pop(primary_key)
    other_values = [v for v in zip(*kwargs.values())]
    sub_dicts = [dict(zip(keys[1:], values)) for values in other_values]
    new_dict = dict(zip(primary_values, sub_dicts))
    return new_dict
