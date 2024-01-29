# %% -*- coding: utf-8 -*-
"""
This module holds the class for viewer control panels.

Classes:
    ViewerPanel (Panel)
"""
# Standard library imports
from __future__ import annotations
import time
from typing import Protocol

# Third party imports
import cv2              # pip install opencv-python
import PySimpleGUI as sg # pip install PySimpleGUI

# Local application imports
from ..gui_utils import Panel
print(f"Import: OK <{__name__}>")

class Viewer(Protocol):
    def getImage(self, *args, **kwargs):
        ...
    def isConnected(self):
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
        self._last_read_time = time.perf_counter()
        
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
        if not self.viewer.isConnected():
            self.viewer.connect()
        if not self.viewer.isConnected():
            raise Exception('Unable to connect viewing device.')
        font = (self.typeface, self.font_sizes[title_font_level])
        layout = super().getLayout(f'{self.name.title()} Control', justification='center', font=font)
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
            now = time.perf_counter()
            ret, frame = self.viewer.getImage(resize=True)
            if ret:
                frame_interval =  now - self._last_read_time
                self._last_read_time = now
                fps = round(1/frame_interval, 2)
                frame = cv2.putText(frame, f'FPS: {fps}', (0,frame.shape[0]-5), cv2.FONT_HERSHEY_PLAIN, 1, (255,255,255), 1)
            updates[self.display_box] = dict(data=cv2.imencode(".png", frame)[1].tobytes())
        return updates
