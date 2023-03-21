# %% -*- coding: utf-8 -*-
"""
Created: Tue 2022/11/30 10:30:00
@author: Chang Jie

Notes / actionables:
- 
"""
# Standard library imports
import time
from typing import Protocol

# Third party imports
import PySimpleGUI as sg # pip install PySimpleGUI

# Local application imports
from .gui_utils import Panel
print(f"Import: OK <{__name__}>")

class Viewer(Protocol):
    def close(self, *args, **kwargs):
        ...
    def getImage(self, *args, **kwargs):
        ...

class ViewerPanel(Panel):
    """
    Viewer Panel class

    Args:
        viewer (obj): Viewer object
        name (str, optional): name of panel. Defaults to 'VIEW'.
        theme (str, optional): name of theme. Defaults to THEME.
        typeface (str, optional): name of typeface. Defaults to TYPEFACE.
        font_sizes (list, optional): list of font sizes. Defaults to FONT_SIZES.
        group (str, optional): name of group. Defaults to 'viewer'.
    """
    def __init__(self, viewer:Viewer, name='VIEW', group='viewer', **kwargs):
        super().__init__(name=name, group=group, **kwargs)
        self.viewer = viewer
        self.display_box = self._mangle('-IMAGE-')
        
        self.flags['update_display'] = True
        self._last_read_time = time.time()
        return
    
    def close(self):
        """
        Close window
        """
        self.viewer.close()
        return
        
    def getLayout(self, title_font_level=1, **kwargs):
        """
        Get layout object

        Args:
            title_font_level (int, optional): index of font size from levels in font_sizes. Defaults to 1.

        Returns:
            PySimpleGUI.Column: Column object
        """
        font = (self.typeface, self.font_sizes[title_font_level])
        layout = super().getLayout(f'{self.name} Control', justification='center', font=font)
        layout = [
            [layout],
            [sg.Image(filename='', key=self.display_box, enable_events=True)]
        ]
        layout = sg.Column(layout, vertical_alignment='top')
        return layout
    
    def listenEvents(self, event, values):
        """
        Listen to events and act on values

        Args:
            event (str): event triggered
            values (dict): dictionary of values from window

        Returns:
            dict: dictionary of updates
        """
        updates = {}
        if self.flags['update_display']:
            frame_interval = time.time() - self._last_read_time
            fps = round(1/frame_interval, 2)
            ret, image = self.viewer.getImage()
            self._last_read_time = time.time()
            if ret:
                image = image.addText(f'FPS: {fps}', position=(0,image.frame.shape[0]-5), inplace=False)
            updates[self.display_box] = dict(data=image.encode())
        return updates
