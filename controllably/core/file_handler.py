# -*- coding: utf-8 -*-
""" 
This module contains functions to handle files and folders.

Attributes:
    TEMP_ZIP (Path): temporary zip file path

## Functions:
    `create_folder`: Check and create folder if it does not exist
    `init`: Add repository to `sys.path`, and get machine id and connected ports
    `read_config_file`: Read configuration file and return as dictionary
    `readable_duration`: Display time duration (s) as HH:MM:SS text
    `resolve_repo_filepath`: Resolve relative path to absolute path
    `start_logging`: Start logging to file
    `start_project_here`: Create new project in destination directory
    `zip_files`: Zip files and return zip file path

<i>Documentation last updated: 2025-02-22</i>
"""
# Standard library imports
from __future__ import annotations
from datetime import datetime, timedelta
from importlib import resources
import json
import logging
import os
from pathlib import Path
import shutil
import sys
from typing import Iterable
from zipfile import ZipFile

# Third party imports
import yaml

# Local application imports
from . import connection

_logger = logging.getLogger("controllably.core")
_logger.debug(f"Import: OK <{__name__}>")

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
logger.addHandler(handler)

TEMP_ZIP = Path('_temp.zip')

def create_folder(base:Path|str = '', sub:Path|str = '') -> Path:
    """
    Check and create folder if it does not exist
    
    Args:
        base (Path|str, optional): parent folder directory. Defaults to ''.
        sub (Path|str, optional): child folder directory. Defaults to ''.
        
    Returns:
        Path: name of main folder
    """
    main_folder = Path(datetime.now().strftime("%Y%m%d_%H%M"))
    new_folder = Path(base) / main_folder / Path(sub)
    os.makedirs(new_folder)
    return new_folder

def init(repository_name:str) -> str:
    """
    Add repository to `sys.path`, and getting machine id and connected ports

    Args:
        repository_name (str): name of current repository
        
    Returns:
        str: target directory path
    """
    cwd = str(Path().absolute())
    assert repository_name in cwd, f"Repository name '{repository_name}' not found in current working directory: {cwd}"
    root = cwd.split(repository_name)[0]
    target_dir = f'{root}{repository_name}'
    if target_dir not in sys.path:
        sys.path.append(target_dir)
    connection.get_node()
    connection.get_ports()
    return target_dir

def read_config_file(filepath:Path|str) -> dict:
    """
    Read configuration file and return as dictionary
    
    Args:
        filepath (Path|str): path to configuration file
        
    Returns:
        dict: configuration file as dictionary
    
    Raises:
        ValueError: Unsupported file type
    """
    filepath = str(filepath)
    file_type = filepath.split('.')[-1]
    with open(filepath, 'r') as file:
        if file_type in ('jsn', 'json', 'jsonl'):
            return json.load(file)
        elif file_type in ('yml', 'yaml'):
            return yaml.safe_load(file)
    raise ValueError(f"Unsupported file type: {file_type}")

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

def resolve_repo_filepath(filepath:Path|str) -> Path:
    """
    Resolve relative path to absolute path
    
    Args:
        filepath (Path|str): relative path to file
        
    Returns:
        Path: absolute path to file
    """
    filepath = str(filepath)
    if len(filepath) == 0 or filepath == '.':
        return Path().absolute()
    if os.path.isabs(filepath):
        return Path(filepath)
    parent = [os.path.sep] + os.getcwd().split(os.path.sep)[1:]
    path = os.path.normpath(filepath).split(os.path.sep)
    index = parent.index(path[0])
    index = [i for i,value in enumerate(parent) if value == path[0]][-1]
    full_path = os.path.abspath(os.path.join(*parent[:index], *path))
    return Path(full_path)

def start_logging(log_dir:Path|str|None = None, log_file:Path|str|None = None, logging_config:dict|None = None) -> Path|None:
    """
    Start logging to file. Default logging behavior is to log to file in current working directory.
    
    Args:
        log_dir (Path|str|None, optional): log directory path. Defaults to None.
        log_file (Path|str|None, optional): log file path. Defaults to None.
        logging_config (dict|None, optional): logging configuration. Defaults to None.
        
    Returns:
        Path|None: path to log file; None if logging_config is provided
    """
    if logging_config is not None and isinstance(logging_config, dict):
        logging.basicConfig(**logging_config)
        return
    
    now = datetime.now().strftime("%Y%m%d_%H%M")
    log_dir = Path.cwd() if log_dir is None else Path(log_dir)
    log_file = f'logs/session_{now}.log' if ((log_file is None) or (not isinstance(log_file, (Path,str)))) else Path(log_file)
    log_path = log_dir/log_file
    os.makedirs(log_path.parent, exist_ok=True)
    
    handler = logging.FileHandler(log_path)
    handler.setLevel(logging.DEBUG)
    logging.basicConfig(handlers=[handler])
    logger.debug(f"Current working directory: {Path.cwd()}")
    return log_path

def start_project_here(dst:Path|str|None = None):
    """
    Create new project in destination directory. 
    If destination is not provided, create in current directory
    
    Args:
        dst (Path|str|None, optional): destination folder. Defaults to None.
    """
    src = resources.files('controllably') / 'core/_templates'
    dst = Path.cwd() if dst is None else Path(dst)
    logger.debug(f"Creating new project in: {dst}")
    for directory in src.iterdir():
        new_dst = dst / directory.name
        if new_dst.exists():
            logger.warning(f"Folder/file already exists: {new_dst}")
            continue
        if directory.is_file():
            shutil.copy2(src=directory, dst=dst / directory.name)
        if directory.is_dir():
            shutil.copytree(src=directory, dst=dst / directory.name)
    logger.info(f"New project created in: {dst}")
    logger.info(f"Please update the configuration files in: {dst/'tools/registry.yaml'}")
    logger.info(f"Current machine id: {connection.get_node()}")
    return

def zip_files(filepaths: Iterable[Path], zip_filepath: str|Path|None = None) -> Path:
    """ 
    Zip files and return zip file path
    
    Args:
        filepaths (Iterable[Path]): list of file paths
        zip_filepath (str|Path|None, optional): zip file path. Defaults to None.
        
    Returns:
        Path: zip file path
    """
    filepaths = list(set(list(filepaths)))
    zip_filepath = zip_filepath or TEMP_ZIP
    zip_filepath = Path(zip_filepath)
    with ZipFile(zip_filepath, 'w') as z:
        for filepath in filepaths:
            z.write(filepath, filepath.name)
    return zip_filepath
