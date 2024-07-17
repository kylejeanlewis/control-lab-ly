# %% -*- coding: utf-8 -*-
"""
This module holds the core functions in Control.lab.ly.
    
Functions:
    create_configs
    create_named_tuple_from_dict
    create_setup
    load_deck
    load_setup
    set_safety

Other constants and variables:
    here (str)
"""
__all__ = [
    "create_configs", 
    "create_named_tuple_from_dict",
    "create_setup", 
    "load_deck", 
    "load_setup", 
    "set_safety"
]
# Standard library imports
from collections import namedtuple
import logging
import os
from pathlib import Path
from shutil import copytree
from typing import Callable, Optional, Union

# Local application imports
from . import factory
from . import helper

logger = logging.getLogger(__name__)
logger.debug(f"Import: OK <{__name__}>")

here = str(Path(__file__).parent.absolute()).replace('\\', '/')
"""Path to this current file"""

# Core functions
def create_configs():
    """Create new tools configs folder"""
    cwd = os.getcwd().replace('\\', '/')
    src = f"{here}/templates/tools"
    dst = f"{cwd}/tools"
    if not os.path.exists(dst):
        print("Creating tools folder...\n")
        copytree(src=src, dst=dst)
        helper.get_node()
    return

def create_named_tuple_from_dict(d:dict, type_name:str = 'Setup') -> tuple:
    """
    creating named tuple from dictionary

    Args:
        d (dict): dictionary to be transformed
        type_name (str, optional): name of new namedtuple type. Defaults to 'Setup'.

    Returns:
        tuple: named tuple from dictionary
    """
    field_list = []
    object_list = []
    for k,v in d.items():
        field_list.append(k)
        object_list.append(v)
    
    named_tuple = namedtuple(type_name, field_list)
    print(f"Objects created: {', '.join(field_list)}")
    return named_tuple(*object_list)

def create_setup(setup_name:Optional[str] = None):
    """
    Create new setup folder

    Args:
        setup_name (Optional[str], optional): name of new setup. Defaults to None.
    """
    cwd = os.getcwd().replace('\\', '/')
    if setup_name is None:
        setup_num = 1
        while True:
            setup_name = f'Setup{str(setup_num).zfill(2)}'
            if not os.path.exists(f"{cwd}/tools/{setup_name}"):
                break
            setup_num += 1
    src = f"{here}/templates/setup"
    cfg = f"{cwd}/tools"
    dst = f"{cfg}/{setup_name}"
    if not os.path.exists(cfg):
        create_configs()
    if not os.path.exists(dst):
        print(f"Creating setup folder ({setup_name})...\n")
        copytree(src=src, dst=dst)
        helper.get_node()
    return

def load_deck(device:Callable, layout_file:str, get_absolute_filepath:bool = True) -> Callable:
    """
    Load deck information from layout file

    Args:
        device (Callable): device object that has the deck attribute
        layout_file (str): layout file name
        get_absolute_filepath (bool, optional): whether to extend the filepaths defined in layout file to their absolute filepaths. Defaults to True.

    Returns:
        Callable: device with deck loaded
    """
    layout_dict = helper.read_json(layout_file)
    if get_absolute_filepath:
        get_repo_name = True
        root = ''
        for slot in layout_dict['slots'].values():
            if get_repo_name:
                repo_name = slot.get('filepath','').replace('\\', '/').split('/')[0]
                root = layout_file.split(repo_name)[0]
                get_repo_name = False
            slot['filepath'] = f"{root}{slot['filepath']}"
    device.loadDeck(layout_dict=layout_dict)
    return device

def load_setup(config_file:str, registry_file:Optional[str] = None, create_tuple:bool = True) -> Union[dict,tuple]:
    """
    Load and initialise setup

    Args:
        config_file (str): config filename
        registry_file (Optional[str], optional): registry filename. Defaults to None.
        create_tuple (bool, optional): whether to return a named tuple, if not returns dictionary. Defaults to True.

    Returns:
        Union[dict,tuple]: dictionary or named tuple of setup objects
    """
    config = helper.get_plans(config_file=config_file, registry_file=registry_file)
    setup = factory.load_components(config=config)
    shortcuts = config.get('SHORTCUTS',{})
    
    for key,value in shortcuts.items():
        parent, child = value.split('.')
        tool = setup.get(parent)
        if tool is None:
            print(f"Tool does not exist ({parent})")
            continue
        if 'components' not in tool.__dict__:
            print(f"Tool ({parent}) does not have components")
            continue
        setup[key] = tool.components.get(child)
    if create_tuple:
        return create_named_tuple_from_dict(setup)
    return setup

def set_safety(safety_level:Optional[str] = None, safety_countdown:int = 3):
    """
    Set safety level of session

    Args:
        safety_level (Optional[str], optional): 'high' - pauses for input before every move action; 'low' - waits for safety timeout before every move action. Defaults to None.
        safety_countdown (int, optional): safety timeout in seconds. Defaults to 3.
    """
    safety_mode = None
    if safety_level == 'high':
        safety_mode = 'pause'
    elif safety_level == 'low':
        safety_mode = 'wait'
    helper.safety_mode = safety_mode
    helper.safety_countdown = safety_countdown
    return
