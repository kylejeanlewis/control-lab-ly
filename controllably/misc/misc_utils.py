# %% -*- coding: utf-8 -*-
"""
Created: Tue 2022/11/02 17:13:35
@author: Chang Jie

Notes / actionables:
-
"""
# Standard library imports
import os
from pathlib import Path
from shutil import copytree

# Third party imports

# Local application imports
from .helper import Helper, HELPER
from . import decorators
print(f"Import: OK <{__name__}>")

here = str(Path(__file__).parent.absolute()).replace('\\', '/')

# Core functions
def create_configs():
    """
    Create new configs folder
    """
    cwd = os.getcwd().replace('\\', '/')
    src = f"{here}/templates/configs"
    dst = f"{cwd}/configs"
    if not os.path.exists(dst):
        print("Creating configs folder...\n")
        copytree(src=src, dst=dst)
        node_id = Helper.get_node()
        print(f"Current machine id: {node_id}")
    return

def create_setup(setup_name:str = None):
    """
    Create new setup folder

    Args:
        setup_name (str, optional): name of new setup. Defaults to None.
    """
    cwd = os.getcwd().replace('\\', '/')
    if setup_name is None:
        setup_num = 1
        while True:
            setup_name = f'Setup{str(setup_num).zfill(2)}'
            if not os.path.exists(f"{cwd}/configs/{setup_name}"):
                break
            setup_num += 1
    src = f"{here}/templates/setup"
    cfg = f"{cwd}/configs"
    dst = f"{cfg}/{setup_name}"
    if not os.path.exists(cfg):
        create_configs()
    if not os.path.exists(dst):
        print(f"Creating setup folder ({setup_name})...\n")
        copytree(src=src, dst=dst)
    return

@decorators.named_tuple_from_dict
def load_setup(config_file:str, registry_file:str = None):
    """
    Load and initialise setup

    Args:
        config_file (str): config filename
        registry_file (str, optional): registry filename. Defaults to None.

    Returns:
        dict: dictionary of loaded devices
    """
    config = Helper.get_plans(config_file=config_file, registry_file=registry_file)
    setup = Helper.load_components(config=config)
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
    return setup

def load_deck(device, layout_file:str, get_absolute_filepath:bool = True):
    """
    Load the deck information from layout file

    Args:
        device (object): device object that has the deck attribute
        layout_file (str): layout file name
        get_absolute_filepath (bool, optional): whether to extend the filepaths defined in layout file to their absolute filepaths. Defaults to True.

    Returns:
        object: device with deck loaded
    """
    layout_dict = Helper.read_json(layout_file)
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

def set_safety(safety_level:str = None, safety_countdown:int = 3):
    """
    Set safety level of session

    Args:
        safety_level (str): 'high' - pauses for input before every move action; 'low' - waits for safety timeout before every move action
        safety_countdown (int, optional): safety timeout in seconds. Defaults to 3.
    """
    safety_mode = None
    if safety_level == 'high':
        safety_mode = 'pause'
    elif safety_level == 'low':
        safety_mode = 'wait'
    HELPER.safety_mode = safety_mode
    HELPER.safety_countdown = safety_countdown
    return
