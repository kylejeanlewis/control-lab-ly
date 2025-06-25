# -*- coding: utf-8 -*-
""" 
This module contains functions to handle logging in the application.

## Functions:
    `get_git_info`: Get current git branch name, short commit hash, and commit datetime in UTC
    `get_package_info`: Get package information (local, editable, source path)
    `log_version_info`: Log version information of the package
    `start_logging`: Start logging to file

<i>Documentation last updated: 2025-06-11</i>
"""
# Standard library imports
from __future__ import annotations
import atexit
from datetime import datetime, timezone
from importlib import resources, metadata
import json
import logging
import logging.config
import logging.handlers
import os
from pathlib import Path
import subprocess

# Local application imports
from .file_handler import read_config_file

# Configure logging
from controllably import CustomLevelFilter
logger = logging.getLogger(__name__)
CustomLevelFilter().setModuleLevel(__name__, logging.INFO)

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

def log_version_info():
    """Log version information of the package"""
    app_logger = logging.getLogger('controllably')
    is_local, _, source_path = get_package_info('control-lab-ly')
    app_logger.debug(f'Local install: {is_local}')
    if is_local:
        branch, commit, date = get_git_info(source_path)
        date_string = date.strftime("%Y/%m/%d %H:%M:%S [%z]") if date else 'unknown'
        if any([branch, commit]):
            app_logger.debug(f'Git reference: {branch} | {commit} | {date_string}')
        else:
            app_logger.debug(f'Source: {source_path}')
    else:
        version = metadata.version('control-lab-ly')
        app_logger.debug(f'Version: {version}')
    return

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
    app_logger = logging.getLogger('controllably')
    
    if logging_config is not None and isinstance(logging_config, dict):
        logging.config.dictConfig(logging_config)
        _ = [app_logger.removeHandler(h) for h in app_logger.handlers]
        app_logger.propagate = True
    elif log_config_file is not None and isinstance(log_config_file, (Path,str)):
        logging_config = read_config_file(log_config_file)
        logging.config.dictConfig(logging_config)
        _ = [app_logger.removeHandler(h) for h in app_logger.handlers]
        app_logger.propagate = True
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
            _ = [app_logger.removeHandler(h) for h in app_logger.handlers]
            app_logger.propagate = True
        except FileNotFoundError:
            print(f"Logging configuration file not found: {log_config_file}. Logging to {log_path}")
            file_handler = logging.handlers.RotatingFileHandler(log_path, maxBytes=5242880)
            file_handler.setLevel(logging.DEBUG)
            fmt = logging.Formatter(
                "%(asctime)s %(levelname)s %(name)s: %(message)s",
                datefmt="%Y-%m-%dT%H:%M:%S%z"
            )
            file_handler.setFormatter(fmt)
            app_logger.addHandler(file_handler)
        except ValueError as e :
            print(e)
    
    for handler in logging.root.handlers:
        if isinstance(handler, logging.handlers.QueueHandler):
            handler.listener.start()
            atexit.register(handler.listener.stop)
    app_logger.info(f"Current working directory: {Path.cwd()}")
    log_version_info()
    return log_path
