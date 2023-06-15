# %% -*- coding: utf-8 -*-
"""
This module holds the base class for multichannel panels.

Classes:
    MultiChannelPanel (Panel)
"""
# Standard library imports
from __future__ import annotations
from abc import abstractmethod
from typing import Optional

# Third party imports
import PySimpleGUI as sg        # pip install PySimpleGUI

# Local application imports
from .gui_utils import Panel
print(f"Import: OK <{__name__}>")

class MultiChannelPanel(Panel):
    """
    Abstract Base Class (ABC) for Multi-Channel Panel objects (i.e. GUI panels for tools with multiple channels).
    ABC cannot be instantiated, and must be subclassed with abstract methods implemented before use.

    ### Constructor
    Args:
        `name` (str, optional): name of panel. Defaults to ''.
        `group` (Optional[str], optional): name of group. Defaults to None.
    
    ### Methods
    #### Abstract
    - `getChannelPanel`: get the panel layout for a single channel
    - `listenEvents`: listen to events and act on values
    #### Public
    - `getLayout`: build `sg.Column` object
    """
    
    def __init__(self, name:str = '', group:Optional[str] = None):
        """
        Instantiate the class

        Args:
            name (str, optional): name of panel. Defaults to ''.
            group (Optional[str], optional): name of group. Defaults to None.
        """
        super().__init__(name=name, group=group)
        return
    
    @abstractmethod
    def getChannelPanel(self, channel_id:int, tool:object, **kwargs) -> sg.Column:
        """
        Get the panel layout for a single channel

        Args:
            channel_id (int): channel index
            tool (object): tool object

        Returns:
            sg.Column: Column object
        """
        
    def getLayout(self, title:str = 'Tool Control', title_font_level:int = 1, **kwargs) -> sg.Column:
        """
        Build `sg.Column` object

        Args:
            title (str, optional): title of layout. Defaults to 'Tool Control'.
            title_font_level (int, optional): index of font size from levels in `font_sizes`. Defaults to 1.

        Returns:
            sg.Column: Column object
        """
        font = (self.typeface, self.font_sizes[title_font_level])
        layout = super().getLayout(title, justification='center', font=font)
        channels = {}
        if 'channels' in dir(self.tool):
            channels = self.tool.channels
        else:
            channels = {self.tool.channel: self.tool}
        if len(channels) == 0:
            return layout
        
        channel_panels = []
        for channel_id, tool in channels.items():
            _layout = self.getChannelPanel(channel_id, tool)
            channel_panels.append((channel_id, _layout))
        if len(channel_panels) == 1:
            panel = channel_panels[0][1]
        else:
            tabs = [sg.Tab(key, [[_layout]], expand_x=True) for key,_layout in channel_panels]
            panel = sg.TabGroup(
                [tabs], tab_location='topleft', key=f'-{self.name}-TABS-', 
                expand_x=True, expand_y=True
            )
        
        suite = sg.Column([[panel]], vertical_alignment='top')
        layout = [
            [layout],
            [sg.Push()],
            [suite]
        ]
        layout = sg.Column(layout, vertical_alignment='top')
        return layout
