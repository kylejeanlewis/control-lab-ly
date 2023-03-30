# %% -*- coding: utf-8 -*-
"""
Created: Tue 2022/11/02 17:13:35
@author: Chang Jie

Notes / actionables:
-
"""
# Standard library imports
from collections import namedtuple
from functools import wraps
import time
from typing import Callable, Optional

# Third party imports

# Local application imports
print(f"Import: OK <{__name__}>")

def named_tuple_from_dict(func:Callable) -> Callable:
    """
    Wrapper for creating named tuple from dictionary

    Args:
        func (Callable): function to be wrapped
    """
    @wraps(func)
    def wrapper(*args, **kwargs) -> tuple:
        setup_dict = func(*args, **kwargs)
        field_list = []
        object_list = []
        for k,v in setup_dict.items():
            field_list.append(k)
            object_list.append(v)
        
        Setup = namedtuple('Setup', field_list)
        print(f"Objects created: {', '.join(field_list)}")
        return Setup(*object_list)
    return wrapper

def safety_measures(mode:Optional[str] = None, countdown:int = 3) -> Callable:
    """
    Wrapper for creating safe move functions

    Args:
        func (Callable): function to be wrapped
        mode (str, optional): mode for implementing safety measure. Defaults to None.
    """
    def inner(func:Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Callable:
            str_method = repr(func).split(' ')[1]
            str_args = ','.join([repr(a) for a in args[1:]])
            str_kwargs = ','.join([f'{k}={v}' for k,v in kwargs.items()])
            str_inputs = ','.join(filter(None, [str_args, str_kwargs]))
            str_call = f"{str_method}({str_inputs})"
            if mode == 'wait':
                print(f"Executing in {countdown} seconds:")
                print(str_call)
                time.sleep(countdown)
            elif mode == 'pause':
                print(f"Executing: {str_call}")
                time.sleep(0.1)
                input(f"Press 'Enter' to execute")
            return func(*args, **kwargs)
        return wrapper
    return inner
