# %% -*- coding: utf-8 -*-
"""
Created: Tue 2022/12/27 21:05:00
@author: Chang Jie

Notes / actionables:
- 
"""
# Standard library imports
import functools
import inspect

# Local application imports
print(f"Import: OK <{__name__}>")

def inherit_docstring(cls):
    for base in inspect.getmro(cls):
        if base.__doc__ is not None:
            cls.__doc__ = base.__doc__
            break
    return cls

def multichannel(all_channels):
    def decorator_multi(func):
        @functools.wraps(func)
        def wrapper_multi(*args, **kwargs):
            return_values = {}
            channels = kwargs.pop('channels', None)
            if channels is None:
                return func(*args, **kwargs)
            if len(channels) == 0:
                channels = list(all_channels)
            
            for channel in channels:
                _kwargs = kwargs.copy()
                _kwargs['channel'] = channel
                value = func(*args, **_kwargs)
                return_values[channel] = value
            return return_values
        return wrapper_multi
    return decorator_multi
