# -*- coding: utf-8 -*-
# Standard library imports
from __future__ import annotations
from datetime import datetime, timedelta
import json
import logging
import os
from pathlib import Path

# Third party imports
import yaml

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.debug(f"Import: OK <{__name__}>")

def create_folder(base:Path|str = '', sub:Path|str = '') -> str:
    """
    Check and create folder if it does not exist

    Args:
        parent_folder (Optional[str], optional): parent folder directory. Defaults to None.
        child_folder (Optional[str], optional): child folder directory. Defaults to None.
    
    Returns:
        str: name of main folder
    """
    main_folder = Path(datetime.now().strftime("%Y%m%d_%H%M"))
    new_folder = Path(base) / main_folder / Path(sub)
    os.makedirs(new_folder)
    return main_folder

def create_project_structure():
    ...
    return

def read_config_file(filepath:str|Path) -> dict:
    """
    Read configuration file and return as dictionary

    Args:
        file_path (str): path to configuration file

    Returns:
        dict: configuration file as dictionary
    """
    filepath = str(filepath)
    file_type = filepath.split('.')[-1]
    with open(filepath, 'r') as file:
        if file_type in ('jsn', 'json', 'jsonl'):
            return json.load(file)
        elif file_type == ('yml', 'yaml'):
            return yaml.safe_load(file)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
    return

def readable_duration(total_time:float) -> str:
    """
    Display time duration (s) as HH:MM:SS text

    Args:
        total_time (float): duration in seconds

    Returns:
        str: formatted time string
    """
    delta = timedelta(seconds=total_time)
    strings = str(delta).split(' ')
    strings[-1] = "{}h {}min {}sec".format(*strings[-1].split(':'))
    return ' '.join(strings)

def resolve_repo_filepath(filepath:str|Path) -> Path:
    """
    Resolve relative path to absolute path

    Args:
        filepath (str): relative path to file

    Returns:
        str: absolute path to file
    """
    filepath = str(filepath)
    if len(filepath) == 0 or filepath == '.':
        return Path('')
    if os.path.isabs(filepath):
        return Path(filepath)
    parent = [os.path.sep] + os.getcwd().split(os.path.sep)[1:]
    path = os.path.normpath(filepath).split(os.path.sep)
    full_path = os.path.abspath(os.path.join(*parent[:parent.index(path[0])], *path))
    return Path(full_path)
