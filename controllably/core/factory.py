# -*- coding: utf-8 -*-
""" 
This module contains functions to create and manage objects.

## Functions:
    `create`: Create object of class with arguments and keyword arguments
    `create_from_config`: Create object of class with dictionary
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

<i>Documentation last updated: 2025-06-11</i>
"""
# Standard library imports
from dataclasses import fields
import importlib
import inspect
import json
import logging
from pathlib import Path
import pprint
import sys
import time
from types import SimpleNamespace
from typing import Callable, Sequence, NamedTuple, Type, Any, Protocol

# Third party imports
import numpy as np

# Local application imports
from . import connection
from . import device
from . import file_handler

# Configure logging
from controllably import CustomLevelFilter
logger = logging.getLogger(__name__)
CustomLevelFilter().setModuleLevel(__name__, logging.INFO)

class Part(Protocol):
    device: Any
    connection_details: dict
    is_busy: bool
    is_connected: bool
    verbose: bool
    def connect(self):...
    def disconnect(self):...
    def resetFlags(self):...
    def shutdown(self):...


def create(obj:Callable, *args, **kwargs) -> object:
    """
    Create object of class with arguments and keyword arguments

    Args:
        obj (Callable): target class
        args (Iterable[Any], optional): arguments for class. Defaults to tuple().
        kwargs (Mapping[str,Any], optional): keyword arguments for class. Defaults to dict().

    Returns:
        object: object of target class
    """
    assert inspect.isclass(obj), f"Ensure object is a class: {obj} | {type(obj)}"
    parents = [parent.__name__ for parent in obj.__mro__]
    try:
        if 'Compound' in parents or 'Combined' in parents:
            docs = inspect.getdoc(obj.fromConfig)
            new_obj = obj.fromConfig(kwargs)
        else:
            docs = inspect.getdoc(obj.__init__)
            new_obj = obj(*args, **kwargs)
    except TypeError as e:
        logger.error(f"Error creating object: {obj.__name__}")
        logger.error(docs)
        logger.error(f"Received args: {args}")
        logger.error(f"Received kwargs: {kwargs}")
        raise e
    return new_obj

def create_from_config(config:dict) -> object:
    """
    Create object of class with dictionary

    Args:
        config (dict): dictionary of arguments

    Returns:
        object: object of target class
    """
    if 'device' in config:
        return config['device']
    device_type = config.pop('device_type', None)
    if device_type is not None:
        assert inspect.isclass(device_type), "Ensure device_type is a callable class"
        return create(device_type, **config)
    if 'baudrate' in config:
        device_type = device.SerialDevice
    elif 'host' in config:
        device_type = device.SocketDevice
    return create(device_type, **config)

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
    
    named_tuple = NamedTuple(tuple_name, field_list)
    logger.info(f"\nObjects created: {', '.join([k for k,v in d.items() if not isinstance(v,Exception)])}")
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
    try:
        module_ = importlib.import_module(module_name)
        class_ = getattr(module_, class_name)
    except ModuleNotFoundError as e:
        logger.error(f"Module not found: {module_name}")
        raise e
    except AttributeError as e:
        logger.error(f"Class not found: {class_name}")
        raise e
    return class_

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
    config_file: Path|str, 
    registry_file: Path|str|None = None, 
    platform_type: Type|None = None,
    silent_fail: bool = False
) -> tuple|Any:
    """
    Load setup from files and return as NamedTuple or Platform
    
    Args:
        config_file (Path|str): config filename
        registry_file (Path|str|None, optional): registry filename. Defaults to None.
        platform_type (Type|None, optional): target platform type. Defaults to None.
        silent_fail (bool, optional): whether to let setup errors through without raising an exception. Defualts to False.
        
    Returns:
        tuple|Any: named tuple or Platform object
    """
    setup: NamedTuple = load_setup_from_files(config_file=config_file, registry_file=registry_file, create_tuple=True)
    errors = {name: tool for name,tool in setup._asdict().items() if isinstance(tool, Exception)}
    n_errors = len(errors)
    if n_errors and not silent_fail:
        logger.error(f'Errors occurred for: {", ".join(errors.keys())}')
        for _,part in setup._asdict().items():
            try:
                part.disconnect()
            except:
                pass
        raise RuntimeError(f"{n_errors} error(s) during initialization", setup)
    
    if platform_type is None or len(platform_type.__annotations__) != len(setup):
        logger.warning('Unable to create typed Platform dataclass')
        logger.warning(f'{type(setup).__name__} has fields: {setup._fields}')
        if platform_type is not None:
            logger.warning(f'Platform type has fields: {fields(platform_type)}')
        logger.warning('Returning NamedTuple instead...')
        return setup
    
    try:
        new_platform = platform_type(**setup._asdict())
        if n_errors:
            logger.error(f'Errors occurred for: {", ".join(errors.keys())}')
    except TypeError as e:
        logger.error(f"Error creating Platform for {type(setup).__name__}")
        logger.error(e)
        logger.warning('Returning NamedTuple instead...')
        return setup
    return new_platform

def load_parts(configs:dict[str,dict], **kwargs) -> dict:
    """
    Load all parts of compound tools from configuration

    Args:
        configs (dict[str,dict]): dictionary of configuration parameters

    Returns:
        dict: dictionary of part tools
    """
    parts = {}
    configs.update(kwargs)
    errors = []
    for name, details in configs.items():
        time.sleep(2)
        title = f'\n{name.upper()}'
        settings = details.get('settings', {})
        simulated = settings.get('simulation', False)
        title = title + ' [simulated]' if simulated else title
        logger.info(title)
        
        logger.debug(f'{pprint.pformat(details, indent=1, depth=4, sort_dicts=False)}\n')
        module_name = details.get('module')
        class_name = details.get('class')
        
        if not module_name or not class_name:
            config_name = details.get('config_name', name)
            config_file = Path(details.get('config_file', ''))
            config_file = file_handler.resolve_repo_filepath(config_file) if not config_file.is_absolute() else config_file
            if config_file.is_file():
                sub_configs = file_handler.read_config_file(config_file)
                details.update(sub_configs[config_name])
            else:
                error_message = f"Config file does not exist: {config_file}"
                logger.error(error_message)
                error = FileNotFoundError(error_message)
                errors.append(error)
                parts[name] = error
                continue
            module_name = details.get('module')
            class_name = details.get('class')
            settings = details.get('settings', {})
        
        try:
            class_ = get_class(module_name, class_name)
            part: Part = create(class_, **settings)
            parts[name] = part
            if not part.is_connected:
                part.connect()
        except Exception as e:
            logger.error(f"Error loading {name}: {e}")
            errors.append(e)
            parts[name] = e
            continue
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
    
    shortcut_errors = 0
    for name,value in shortcuts.items():
        prefix = "" if shortcut_errors else "\n"
        parent, child = value.split('.')
        tool = setup.get(parent, None)
        if tool is None:
            logger.warning(f"{prefix}Tool does not exist ({parent})")
            shortcut_errors += 1
            continue
        if not hasattr(tool, '_parts'):
            logger.warning(f"{prefix}Tool ({parent}) does not have parts")
            shortcut_errors += 1
            continue
        setup[name] = getattr(tool.parts, child)
    if create_tuple:
        tuple_name = config_file.stem.replace('config', '') or config_file.parent.stem
        return dict_to_named_tuple(setup, tuple_name=tuple_name)
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
        if 'module' not in details or 'class' not in details:
            config_name = details.get('config_name', name)
            config_file = Path(details.get('config_file', ''))
            config_file = file_handler.resolve_repo_filepath(config_file) if not config_file.is_absolute() else config_file
            if config_file.is_file():
                sub_configs = file_handler.read_config_file(config_file)
                details.update(sub_configs[config_name])
        
        settings = details.get('settings', {})
        
        for key,value in settings.items():
            if key == 'details':
                value = parse_configs(value, addresses=addresses)
            if type(value) is str:
                if key in ('cam_index', 'port') and value.startswith('__'):
                    settings[key] = addresses.get(key, {}).get(settings[key], value)
            if type(value) is dict:
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
        primary_key (str): primary keyword to be used as key
        kwargs (dict): {keyword, list of values} pairs
        
    Returns:
        dict: dictionary of (primary keyword, kwargs)
        
    Raises:
        AssertionError: Ensure the lengths of inputs are the same
    """
    length = len(kwargs[primary_key])
    for key, value in kwargs.items():
        if isinstance(value, (Sequence, np.ndarray)):
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
