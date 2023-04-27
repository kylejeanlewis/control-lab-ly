# %% -*- coding: utf-8 -*-
"""
This module holds the class for liquid control panels.

Classes:
    ViewerPanel (Panel)
"""
# Standard library imports
from __future__ import annotations
import time
from typing import Protocol

# Third party imports
import cv2                  # pip install opencv-python
import PySimpleGUI as sg    # pip install PySimpleGUI

# Local application imports
from .gui_utils import Panel
print(f"Import: OK <{__name__}>")

class Liquid(Protocol):
    def getImage(self, *args, **kwargs):
        ...
    def shutdown(self, *args, **kwargs):
        ...

class LiquidPanel(Panel):
    def __init__(self, 
        liquid: Liquid, 
        name: str = 'VIEW', 
        group: str = 'viewer', 
        **kwargs
    ):
        """
        Instantiate the class

        Args:
            viewer (Viewer): viewer object
            name (str, optional): name of panel. Defaults to 'VIEW'.
            group (str, optional): name of group. Defaults to 'viewer'.
        """
        super().__init__(name=name, group=group, **kwargs)
        self.tool = liquid
        
        self.display_box = self._mangle('-IMAGE-')
        self._last_read_time = time.perf_counter()
        
        self.setFlag(update_display=True)
        return
    
    # Properties
    @property
    def liquid(self) -> Liquid:
        return self.tool
    
    def getLayout(self, title_font_level: int = 1, **kwargs) -> sg.Column:
        font = (self.typeface, self.font_sizes[title_font_level])
        layout = super().getLayout(f'{self.name} Control', justification='center', font=font)
        
        ...
        return
    
    def listenEvents(self, event: str, values: dict[str, str]) -> dict[str, str]:
        return super().listenEvents(event, values)