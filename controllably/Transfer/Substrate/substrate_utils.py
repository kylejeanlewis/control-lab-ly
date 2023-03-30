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
    def __init__(self):
        """Instantiate the class"""
        ...
    
    @abstractmethod
    def drop(self) -> bool:
        pass
    
    @abstractmethod
    def grab(self) -> bool:
        pass
