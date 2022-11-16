# %% -*- coding: utf-8 -*-
"""
Created: Tue 2022/11/1 13:20:00
@author: Chang Jie

Notes / actionables:
- validation on copper 
- rewrite the operation modes as programs, instead of subclasses
"""
# Standard library imports
import numpy as np
import os
import pandas as pd
import pkgutil
import time

# Third party imports
import cv2 # pip install opencv-python

# Local application imports
print(f"Import: OK <{__name__}>")

class CascadeClassifier(object):
    def __init__(self) -> None:
        pass
    
    def detect(self):
        return