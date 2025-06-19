# -*- coding: utf-8 -*-
""" 
This module contains functions to handle files and folders.

Attributes:
    TEMP_ZIP (Path): temporary zip file path

## Functions:
    `create_folder`: Check and create folder if it does not exist
    `get_git_info`: Get current git branch name, short commit hash, and commit datetime in UTC
    `get_package_info`: Get package information (local, editable, source path)
    `init`: Add repository to `sys.path`, and get machine id and connected ports
    `log_version_info`: Log version information of the package
    `read_config_file`: Read configuration file and return as dictionary
    `readable_duration`: Display time duration (s) as HH:MM:SS text
    `resolve_repo_filepath`: Resolve relative path to absolute path
    `start_logging`: Start logging to file
    `start_project_here`: Create new project in destination directory
    `zip_files`: Zip files and return zip file path

<i>Documentation last updated: 2025-06-11</i>
"""
# Standard library imports
from __future__ import annotations
import atexit
from datetime import datetime, timedelta, timezone
from importlib import resources, metadata
import json
import logging
import logging.config
import logging.handlers
import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Iterable
from zipfile import ZipFile

# Third party imports
import yaml

# Local application imports
from . import connection

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

def get_git_info(directory: str = '.') -> tuple[str|None, str|None, datetime|None]:
    """
    Get current git branch name, short commit hash, and commit datetime in UTC.
    
    Args:
        directory (str, optional): path to git repository. Defaults to '.'.
        
    Returns:
        tuple[str|None, str|None]: branch name, short commit hash, commit datetime in UTC
    """
    branch_name = None
    short_commit_hash = None
    commit_datetime_utc = None
    try:
        # Get the branch name
        # --abbrev-ref HEAD gives the branch name or "HEAD" for detached state
        branch_name_output = subprocess.check_output(
            ['git', 'rev-parse', '--abbrev-ref', 'HEAD'], 
            stderr=subprocess.STDOUT,
            cwd=directory
        )
        branch_name = branch_name_output.strip().decode('utf-8')

        # Get the short commit hash
        short_commit_hash_output = subprocess.check_output(
            ['git', 'rev-parse', '--short', 'HEAD'],
            stderr=subprocess.STDOUT,
            cwd=directory
        )
        short_commit_hash = short_commit_hash_output.strip().decode('utf-8')
        
        # Get the Unix timestamp of the committer date for HEAD
        # Git typically stores timestamps in UTC.
        commit_timestamp_str = subprocess.check_output(
            ['git', 'show', '-s', '--format=%ct', 'HEAD'],
            stderr=subprocess.STDOUT,
            cwd=directory
        )
        commit_timestamp = int(commit_timestamp_str.strip().decode('utf-8'))
        commit_datetime_utc = datetime.fromtimestamp(commit_timestamp, tz=timezone.utc)
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Error getting git info: {e}")
    except FileNotFoundError:
        logger.error("Git command not found. Make sure Git is installed and in your PATH.")
    except ValueError:
        logger.error(f"Error: Could not parse commit timestamp '{commit_timestamp_str}'.")
    return branch_name, short_commit_hash, commit_datetime_utc

def get_package_info(package_name: str) -> tuple[bool, bool, Path|None]:
    """
    Get package information (local, editable, source path)
    
    Args:
        package_name (str): name of the package
        
    Returns:
        tuple[bool, bool, Path|None]: is_local, is_editable, source_path
    """
    is_local = False
    is_editable = False
    source_path = None
    try:
        dist = metadata.distribution(package_name)
        direct_url_file = None
        for f in dist.files:
            path = f.locate()
            if 'direct_url.json' in str(path):
                direct_url_file = path
                break
        if direct_url_file is not None and direct_url_file.exists():
            is_local = True
            with open(direct_url_file, 'r') as f:
                direct_url_data = json.load(f)
            is_editable = direct_url_data.get('dir_info',{}).get('editable', False)
            source_path = direct_url_data.get('url','')
            if source_path.startswith('file://'):
                source_path = source_path.replace('file://', '', 1)
                if os.name == 'nt' and source_path.startswith('/'):
                    source_path = source_path[1:]
                source_path = Path(source_path).resolve()

    except metadata.PackageNotFoundError:
        logger.error(f"Package '{package_name}' not found.")
    except Exception as e:
        logger.error(f"An error occurred: {e}")
    return is_local, is_editable, source_path

def init(repository:str|Path) -> str:
    """
    Add repository to `sys.path`, and getting machine id and connected ports

    Args:
        repository (str|Path): name of current repository, or path to repository folder
        
    Returns:
        str: target directory path
    """
    repository = repository if isinstance(repository, Path) else Path(repository)
    if repository.is_absolute():
        target_dir = str(repository)
    else:
        cwd = str(Path().absolute())
        assert str(repository) in cwd, f"Repository name '{repository}' not found in current working directory: {cwd}"
        root = cwd.split(str(repository))[0]
        target_dir = f'{root}{repository}'
    if target_dir not in sys.path:
        sys.path.append(target_dir)
    connection.get_node()
    connection.get_ports()
    return target_dir

def log_version_info():
    """Log version information of the package"""
    _logger = logging.getLogger('controllably')
    _logger.setLevel(logging.DEBUG)
    is_local, _, source_path = get_package_info('control-lab-ly')
    _logger.debug(f'Local install: {is_local}')
    if is_local:
        branch, commit, date = get_git_info(source_path)
        date_string = date.strftime("%Y/%m/%d %H:%M:%S [%z]") if date else 'unknown'
        if any([branch, commit]):
            _logger.debug(f'Git reference: {branch} | {commit} | {date_string}')
        else:
            _logger.debug(f'Source: {source_path}')
    else:
        version = metadata.version('control-lab-ly')
        _logger.debug(f'Version: {version}')
    return

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

def start_logging(
    log_dir:Path|str|None = None, 
    log_file:Path|str|None = None, 
    log_config_file:Path|str|None = None,
    logging_config:dict|None = None
) -> Path|None:
    """
    Start logging to file. Default logging behavior is to log to file in current working directory.
    
    Args:
        log_dir (Path|str|None, optional): log directory path. Defaults to None.
        log_file (Path|str|None, optional): log file path. Defaults to None.
        log_config_file (Path|str|None, optional): path to logging configuration file. Defaults to None.
        logging_config (dict|None, optional): logging configuration. Defaults to None.
        
    Returns:
        Path|None: path to log file; None if logging_config is provided
    """
    log_path = None
    if logging_config is not None and isinstance(logging_config, dict):
        logging.config.dictConfig(logging_config)
    elif log_config_file is not None and isinstance(log_config_file, (Path,str)):
        logging_config = read_config_file(log_config_file)
        logging.config.dictConfig(logging_config)
    else:
        now = datetime.now().strftime("%Y%m%d_%H%M")
        log_dir = Path.cwd() if log_dir is None else Path(log_dir)
        log_file = f'logs/session_{now}.log' if not isinstance(log_file, (Path,str)) else log_file
        log_path = log_dir/log_file
        os.makedirs(log_path.parent, exist_ok=True)
        
        try:
            log_config_file = resources.files('controllably') / 'core/_templates/library/configs/logging.yaml'
            logging_config = read_config_file(log_config_file)
            logging_config['handlers']['file_handler']['filename'] = str(log_path)
            logging.config.dictConfig(logging_config)
        except FileNotFoundError:
            print(f"Logging configuration file not found: {log_config_file}. Logging to {log_path}")
            file_handler = logging.FileHandler(log_path)
            file_handler.setLevel(logging.DEBUG)
            logging.root.addHandler(file_handler)
    
    for handler in logging.root.handlers:
        if isinstance(handler, logging.handlers.QueueHandler):
            handler.listener.start()
            atexit.register(handler.listener.stop)
    logger.info(f"Current working directory: {Path.cwd()}")
    log_version_info()
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
    logger.info(f"Creating new project in: {dst}")
    for directory in src.iterdir():
        # if directory.is_dir() and directory.name == 'messaging':
        #     continue
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
