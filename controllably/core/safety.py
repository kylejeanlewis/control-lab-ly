# -*- coding: utf-8 -*-
"""
This module contains the functions and decorator for implementing safety measures in the robot.
The decorator function is used to create guardrails for functions and functions, especially involving movement.
The module also contains functions to set and reset the safety level for the safety measures.

Attributes:
    DEBUG (int): Safety mode that logs the function call
    DELAY (int): Safety mode that waits for a few seconds before executing. Defaults to 3.
    SUPERVISED (int): Safety mode that requires user input before executing
    safety_mode (int): Safety mode for the safety measures

## Functions:
    `guard` (decorator): Decorator for creating guardrails for functions and functions, especially involving movement
    `set_level`: Set the safety level for the safety measures
    `reset_level`: Reset the safety level to None
    
<i>Documentation last updated: 2024-11-12</i>
"""
# Standard library imports
from functools import wraps
import logging
import time
from typing import Callable

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.debug(f"Import: OK <{__name__}>")

DEBUG = 0
"""Safety mode that logs the function call"""
DELAY = 3
"""Safety mode that waits for a few seconds before executing. Defaults to 3."""
SUPERVISED = -10
"""Safety mode that requires user input before executing"""

safety_mode = None
"""Safety mode for the safety measures"""

def set_level(mode: int):
    """
    Set the safety level for the safety measures

    Args:
        mode (int): safety mode
            - DEBUG (0): logs the function call
            - DELAY (>=1): waits for a few seconds before executing. Defaults to 3.
            - SUPERVISED (-10): requires user input before executing
    """
    global safety_mode
    safety_mode = mode
    return

def reset_level():
    """Reset the safety level to None"""
    global safety_mode
    safety_mode = None
    return

def guard(mode:int = DEBUG) -> Callable:
    """
    Decorator for creating guardrails for functions and functions, especially involving movement

    Args:
        mode (int, optional): mode for implementing safety measure. Defaults to DEBUG.
            - DEBUG (0): logs the function call
            - DELAY (>=1): waits for a few seconds before executing. Defaults to 3.
            - SUPERVISED (-10): requires user input before executing
        
    Returns:
        Callable: wrapped function
    """
    global safety_mode
    mode = safety_mode if safety_mode is not None else mode
    assert isinstance(mode, int), f"mode must be an integer, not {type(mode)}"
    def inner(func:Callable) -> Callable:
        """
        Inner wrapper for creating safe move functions

        Args:
            func (Callable): function to be wrapped

        Returns:
            Callable: wrapped function
        """
        @wraps(func)
        def wrapper(*args, **kwargs) -> Callable:
            str_method = repr(func).split(' ')[1]
            str_args = ','.join([repr(a) for a in args if a not in ('cls', 'self')])
            str_kwargs = ','.join([f'{k}={v}' for k,v in kwargs.items()])
            str_inputs = ','.join(filter(None, [str_args, str_kwargs]))
            str_call = f"{str_method}({str_inputs})"
            
            if mode == DEBUG:
                logger.debug(f"[DEBUG] {str_call}")
            elif mode < DEBUG:  # SUPERVISED
                logger.warning(f"[SUPERVISED] {str_call}")
                time.sleep(0.1)
                input(f"Press 'Enter' to continue")
            else:               # DELAY
                logger.warning(f"[DELAY] {str_call}")
                logger.warning(f"Waiting for {mode} seconds")
                time.sleep(mode)
            return func(*args, **kwargs)
        return wrapper
    return inner
