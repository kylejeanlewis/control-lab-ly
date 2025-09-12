# -*- coding: utf-8 -*-
"""
This module contains the functions and decorator for implementing safety measures in the robot.
The decorator function is used to create guardrails for functions and functions, especially involving movement.
The module also contains functions to set and reset the safety level for the safety measures.

Attributes:
    safety_mode (int): Safety mode for the safety measures
    SafetyLevel (Enum): Enum for safety levels
        - DEBUG (int): Safety mode that logs the function call [0]
        - DELAY (int): Safety mode that waits for a few seconds before executing.[3]
        - SUPERVISED (int): Safety mode that requires user input before executing. [-10]

## Functions:
    `guard` (decorator): Decorator for creating guardrails for functions and functions, especially involving movement
    `set_level`: Set the safety level for the safety measures
    `reset_level`: Reset the safety level to None
    
<i>Documentation last updated: 2025-06-11</i>
"""
# Standard library imports
from enum import IntEnum
from functools import wraps
import logging
import time
from typing import Callable

# Configure logging
logger = logging.getLogger(__name__)

class SafetyLevel(IntEnum):
    """Enum for safety levels"""
    DEBUG = 0
    """Safety mode that logs the function call"""
    DELAY = 3
    """Safety mode that waits for a few seconds before executing. Defaults to 3."""
    SUPERVISED = -10
    """Safety mode that requires user input before executing"""

safety_mode = None
"""Safety mode for the safety measures"""

def get_safety_level() -> int|None:
    """
    Get the current safety level
    
    Returns:
        int|None: current safety level
    """
    global safety_mode
    return safety_mode

def get_safety_mode(mode:int|None) -> int:
    """
    Get the effective safety mode

    Args:
        mode (int|None): safety mode

    Returns:
        int: effective safety mode
    """
    if mode != -10:
        mode = get_safety_level() if get_safety_level() else mode
    assert isinstance(mode, int), f"Mode must be an integer, not {type(mode)}"
    return mode

def set_safety_level(mode: int):
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

def reset_safety_level():
    """Reset the safety level to None"""
    global safety_mode
    safety_mode = None
    return

def guard(mode:int = SafetyLevel.DEBUG) -> Callable:
    """
    Decorator for creating guardrails for functions and functions, especially involving movement

    Args:
        mode (int, optional): mode for implementing safety measure. Defaults to SafetyLevel.DEBUG.
            - DEBUG (0): logs the function call
            - DELAY (>=1): waits for a few seconds before executing. Defaults to 3.
            - SUPERVISED (-10): requires user input before executing
        
    Returns:
        Callable: wrapped function
    """
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
            
            effective_mode = get_safety_mode(mode)
            if effective_mode == SafetyLevel.DEBUG:
                logger.debug(f"[DEBUG] {str_call}")
            elif effective_mode < SafetyLevel.DEBUG:    # SUPERVISED
                logger.warning(f"[SUPERVISED] {str_call}")
                time.sleep(0.1)
                input("Press 'Enter' to continue")
            else:                           # DELAY
                logger.warning(f"[DELAY] {str_call}")
                logger.warning(f"Waiting for {effective_mode} seconds")
                time.sleep(effective_mode)
            return func(*args, **kwargs)
        return wrapper
    return inner
