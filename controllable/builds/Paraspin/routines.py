# %% -*- coding: utf-8 -*-
"""
Adapted from @jaycecheng spinutils

Created: Tue 2022/11/01 17:13:35
@author: Chang Jie

Notes / actionables:
-
"""
# Standard library imports
import pandas as pd
import threading
import time

# Third party imports

# Local application imports
from ... import Make
from ... import Move
print(f"Import: OK <{__name__}>")

mover_class = Move.Cartesian.Primitiv
liquid_class = Move.Liquid.SyringeAssembly
maker_class = Make.ThinFilm.SpinnerAssembly

class Setup(object):
    def __init__(self, config):
        self.mover = None
        self.liquid = None
        self.maker = None
        
        self._config = config
        
        self.connect()
        pass
    
    def connect(self):
        mover_kwargs = {}
        liquid_kwargs = {}
        maker_kwargs = {}
        
        # self.mover = mover_class(**mover_kwargs)
        # self.liquid = liquid_class(**liquid_kwargs)
        # self.maker = maker_class(**maker_kwargs)
        
        self.mover = mover_class("COM8", [(-470,0,0), (0,0,0)], Z_safe=0, Z_updown=(0,0))
        self.liquid = liquid_class("COM4", [3000]*5, [3,4,5,6,7], offsets=[-100,-75,-50,-25,0])
        self.maker = maker_class(["COM16","COM15","COM14","COM13"], [0,1,2,3], [-325,-250,-175,-100])
        
        # self.mover = Move.Cartesian.Primitiv("COM8", [(-470,0,0), (0,0,0)], Z_safe=0, Z_updown=(0,0))
        # self.liquid = Move.Liquid.SyringeAssembly("COM4", [3000]*5, [3,4,5,6,7], offsets=[-100,-75,-50,-25,0])
        # self.maker
        return
