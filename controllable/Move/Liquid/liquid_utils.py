# %% -*- coding: utf-8 -*-
"""
Created: Tue 2022/11/01 17:13:35
@author: Chang Jie

Notes / actionables:
-
"""
# Local application imports
from .. import Mover
print(f"Import: OK <{__name__}>")

class LiquidHandler(Mover):
    def __init__(self) -> None:
        super().__init__()
        return