# %% -*- coding: utf-8 -*-
"""
Created: Tue 2022/11/30 10:30:00
@author: Chang Jie

Notes / actionables:
- 
"""
# Standard library imports
import numpy as np
import time
from typing import Protocol, Callable

# Third party imports
import PySimpleGUI as sg # pip install PySimpleGUI

# Local application imports
from ...misc import Helper
from .gui_utils import Panel, WIDTH, HEIGHT, THEME, TYPEFACE, FONT_SIZES
print(f"Import: OK <{__name__}>")

class LoaderPanel(Panel):
    """
    Loader Panel class

    Args:
        name (str, optional): name of panel. Defaults to ''.
        theme (str, optional): name of theme. Defaults to THEME.
        typeface (str, optional): name of typeface. Defaults to TYPEFACE.
        font_sizes (list, optional): list of font sizes. Defaults to FONT_SIZES.
        group (str, optional): name of group. Defaults to None.
    """
    def __init__(self, name='', theme=THEME, typeface=TYPEFACE, font_sizes=FONT_SIZES, group=None):
        super().__init__(name, theme, typeface, font_sizes, group)
        return
    