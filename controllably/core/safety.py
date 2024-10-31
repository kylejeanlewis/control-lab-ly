# -*- coding: utf-8 -*-
"""
This module holds the decorator functions in Control.lab.ly.

Functions:
    safety_measures (decorator)
"""
# Standard library imports
from functools import wraps
import logging
import time
from typing import Callable

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.debug(f"Import: OK <{__name__}>")

SUPERVISED = -10
DEBUG = 0
DELAY = 3

def guard(mode:int = DEBUG) -> Callable:
    """
    Wrapper for creating guardrails for functions, especially involving movement

    Args:
        mode (int, optional): mode for implementing safety measure. Defaults to None.
            SUPERVISED (-10): requires user input before executing
            DEBUG (0): logs the function call
            DELAY (3): waits for a few seconds before executing
        
    Returns:
        Callable: wrapped function
    """
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
            str_args = ','.join([repr(a) for a in args[1:]])
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
                time.sleep(mode)
            return func(*args, **kwargs)
        return wrapper
    return inner
