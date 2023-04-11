# %% -*- coding: utf-8 -*-
"""
Created: Tue 2022/12/12 13:13:00
@author: Chang Jie

Notes / actionables:
-
"""
# Standard library imports
from abc import ABC, abstractmethod
print(f"Import: OK <{__name__}>")

class Gripper(ABC):
    """
    Abstract Base Class (ABC) for Gripper objects (i.e. tools that picks up and places objects).
    ABC cannot be instantiated, and must be subclassed with abstract methods implemented before use.

    ### Methods
    #### Abstract
    - `drop`: releases an object
    - `grab`: picks up an object
    """
    
    def __init__(self):
        """Instantiate the class"""
        ...
    
    @abstractmethod
    def drop(self) -> bool:
        """
        Releases an object
        
        Returns:
            bool: whether action is successful
        """
    
    @abstractmethod
    def grab(self) -> bool:
        """
        Picks up an object
        
        Returns:
            bool: whether action is successful
        """
