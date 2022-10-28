# %% -*- coding: utf-8 -*-
"""
Created on Fri 2022/10/28 13:30:00

@author: Chang Jie

Template for Tool structure

Notes: 
- (actionables)
"""
# Import from other modules / libraries
import os, sys
import time
import numpy as np
import pandas as pd
print(f"Import: OK <{__name__}>")


# %%
class Helper(object):
    def __init__(self):
        return


class Tool(object):
    def __init__(self, address=None, name='', inst=None, flags={}, buffer_df=None, program=None):
        self.name = ''
        self.flags = {}
        self.address = None
        self.inst = None
        self.buffer_df = None
        self.program = None
        return
