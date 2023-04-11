# %% -*- coding: utf-8 -*-
"""

"""
# Standard library imports
from __future__ import annotations
import time
from typing import Protocol

# Third party imports
import PySimpleGUI as sg # pip install PySimpleGUI

# Local application imports
from .gui_utils import Panel
print(f"Import: OK <{__name__}>")

class Viewer(Protocol):
    def getImage(self, *args, **kwargs):
        ...
    def shutdown(self, *args, **kwargs):
        ...

class ViewerPanel(Panel):
    """
    ViewerPanel provides methods to create a control panel for a viewer
    
    ### Constructor
    Args:
        `viewer` (Viewer): Viewer object
        `name` (str, optional): name of panel. Defaults to 'VIEW'.
        `group` (str, optional): name of group. Defaults to 'viewer'.

    ### Attributes
    - `display_box` (str): element id
    
    ### Properties
    - `viewer` (Viewer): alias for `tool`
    
    ### Methods
    - `close`: exit the application
    - `getLayout`: build `sg.Column` object
    - `listenEvents`: listen to events and act on values
    """
    def __init__(self, 
        viewer: Viewer, 
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
        self.tool = viewer
        
        self.display_box = self._mangle('-IMAGE-')
        self._last_read_time = time.time()
        
        self.setFlag(update_display=True)
        return
    
    # Properties
    @property
    def viewer(self) -> Viewer:
        return self.tool
    
    def close(self):
        """Exit the application"""
        self.viewer.shutdown()
        return super().close()
        
    def getLayout(self, title_font_level:int = 1, **kwargs) -> sg.Column:
        """
        Build `sg.Column` object

        Args:
            title_font_level (int, optional): index of font size from levels in `font_sizes`. Defaults to 1.

        Returns:
            sg.Column: Column object
        """
        font = (self.typeface, self.font_sizes[title_font_level])
        layout = super().getLayout(f'{self.name} Control', justification='center', font=font)
        layout = [
            [layout],
            [sg.Image(filename='', key=self.display_box, enable_events=True)]
        ]
        layout = sg.Column(layout, vertical_alignment='top')
        return layout
    
    def listenEvents(self, event:str, values:dict[str, str]) -> dict[str, dict]:
        """
        Listen to events and act on values

        Args:
            event (str): event triggered
            values (dict[str, str]): dictionary of values from window

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
