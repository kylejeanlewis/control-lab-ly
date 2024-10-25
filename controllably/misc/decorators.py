# -*- coding: utf-8 -*-
"""
This module holds the decorator functions in Control.lab.ly.

Functions:
    safety_measures (decorator)
"""
# Standard library imports
from enum import Enum
from functools import wraps
from logging import getLogger
import time
from typing import Callable

logger = getLogger(__name__)
logger.info(f"Import: OK <{__name__}>")

class Safety(Enum):
    """
    Enum for safety modes
    """
    WAIT = 'wait'
    PAUSE = 'pause'

def safety_measures(mode:Safety|str|None = None, countdown:int = 3) -> Callable:
    """
    Wrapper for creating safe move functions

    Args:
        mode (str|None, optional): mode for implementing safety measure. Defaults to None.
        countdown (int, optional): time delay before executing action. Defaults to 3.
        
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
            str_args = ','.join([repr(a) for a in args[1:]])
            str_kwargs = ','.join([f'{k}={v}' for k,v in kwargs.items()])
            str_inputs = ','.join(filter(None, [str_args, str_kwargs]))
            str_call = f"{str_method}({str_inputs})"
            match mode:
                case Safety.WAIT.value:
                    logger.warning(f"Executing in {countdown} seconds: {str_call}")
                    time.sleep(countdown)
                case Safety.PAUSE.value:
                    logger.warning(f"Executing: {str_call}")
                    time.sleep(0.1)
                    input(f"Press 'Enter' to execute")
                case _:
                    logger.warning(f"Executing: {str_call}")
            return func(*args, **kwargs)
        return wrapper
    return inner
