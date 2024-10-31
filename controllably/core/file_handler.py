# -*- coding: utf-8 -*-
# Standard library imports
from __future__ import annotations
import json
from logging import getLogger

# Third party imports
import yaml

logger = getLogger(__name__)
logger.info(f"Import: OK <{__name__}>")


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
