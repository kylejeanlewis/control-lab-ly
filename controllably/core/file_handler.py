# -*- coding: utf-8 -*-
# Standard library imports
from __future__ import annotations
import json
import logging

# Third party imports
import yaml

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.debug(f"Import: OK <{__name__}>")

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
