# -*- coding: utf-8 -*-
# Standard library imports
from __future__ import annotations
from datetime import datetime
import json
import logging
import os
from pathlib import Path

# Third party imports
import yaml

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.debug(f"Import: OK <{__name__}>")

here = str(Path(__file__).parent.absolute()).replace('\\', '/')
"""Path to this current file"""

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

def read_config_file(filepath:str) -> dict:
    """
    Read configuration file and return as dictionary

    Args:
        file_path (str): path to configuration file

    Returns:
        dict: configuration file as dictionary
    """
    file_type = filepath.split('.')[-1]
    with open(filepath, 'r') as file:
        if file_type in ('jsn', 'json', 'jsonl'):
            return json.load(file)
        elif file_type == ('yml', 'yaml'):
            return yaml.safe_load(file)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
    return


