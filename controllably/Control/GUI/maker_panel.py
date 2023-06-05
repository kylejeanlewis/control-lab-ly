# %% -*- coding: utf-8 -*-
"""
This module holds the class for maker control panels.

Classes:
    MakerPanel (MultiChannelPanel)
"""
# Standard library imports
from __future__ import annotations
import inspect
from typing import Protocol

# Third party imports
import PySimpleGUI as sg # pip install PySimpleGUI

# Local application imports
from .gui_utils import MultiChannelPanel
print(f"Import: OK <{__name__}>")

class Maker(Protocol):
    channel: int
    def execute(self, *args, **kwargs):
        ...

class MakerPanel(MultiChannelPanel):
    """
    Maker Panel class

    ### Constructor
    Args:
        `maker` (Maker): Maker object
        `name` (str, optional): name of panel. Defaults to 'MAKER'.
        `group` (str, optional): name of group. Defaults to 'maker'.
        
    ### Attributes
    - `input_map` (dict[int, Optional[str]]): enumerated map of program inputs
    
    ### Properties
    - `maker` (Maker): alias for `tool`
    
    ### Methods
    - `getChannelPanel`: get the panel layout for a single channel
    - `getLayout`: build `sg.Column` object
    - `listenEvents`: listen to events and act on values
    """
    
    _default_input_map: dict = {f"INPUT-{i:02}": None for i in range(8)}
    def __init__(self, 
        maker: Maker, 
        name: str = 'MAKER', 
        group: str = 'maker', 
        **kwargs
    ):
        """
        Instantiate the class

        Args:
            maker (Maker): Maker object
            name (str, optional): name of panel. Defaults to 'MAKER'.
            group (str, optional): name of group. Defaults to 'maker'.
        """
        super().__init__(name=name, group=group, **kwargs)
        self.tool = maker
        self.input_map = self._default_input_map
        
        self._channels = {}
        if 'channels' in dir(self.tool):
            self._channels = self.tool.channels
        else:
            self._channels = {self.tool.channel: self.tool}
        
        self._tooltip = ""
        self._signature = None
        self._parameters = {}
        self._defaults = {}
        self.__info__()
        return
    
    def __info__(self):
        """Get info from `Maker.execute()` method"""
        self._signature = inspect.signature(self.maker.execute)
        self._parameters = {k:v for k,v in dict(self._signature.parameters).items() if k not in ('self', 'args', 'kwargs')}
        self._defaults = {k:v.default for k,v in self._parameters.items() if v.default != inspect.Parameter.empty}
        doc = self.maker.execute.__doc__
        tooltip = [line.strip() for line in doc.split('Args:')[1].split('\n')]
        self._tooltip = '\n'.join([line for line in tooltip if line])
        return
    
    # Properties
    @property
    def maker(self) -> Maker:
        return self.tool
    
    def getChannelPanel(self, channel_id:int, tool:Maker) -> sg.Column:
        """
        Get the panel layout for a single channel

        Args:
            channel_id (int): channel index
            tool (Maker): tool object

        Returns:
            sg.Column: Column object
        """
        # add template for procedurally adding input fields
        defaults = self._defaults.copy()
        if 'channel' in self._parameters:
            defaults.update(channel=channel_id)
        labels_inputs = self.getInputs(
            fields = [i for i in self.input_map], 
            key_prefix = f"{self.name}-{channel_id}", 
            initial_visibility = True,
            label_map = self.input_map,
            defaults = {k:defaults[v] for k,v in self.input_map.items() if v in defaults},
            tooltips = {k: self._tooltip for k in self.input_map}
        )
        layout = sg.Column([labels_inputs], vertical_alignment='top')
        return layout
    
    def getLayout(self, title_font_level:int = 0, **kwargs) -> sg.Column:
        """
        Build `sg.Column` object

        Args:
            title (str, optional): title of layout. Defaults to 'Panel'.
            title_font_level (int, optional): index of font size from levels in font_sizes. Defaults to 0.

        Returns:
            sg.Column: Column object
        """
        self.input_map = {f"INPUT-{i:02}": p for i,p in enumerate(self._parameters)}
        
        font = (self.typeface, self.font_sizes[title_font_level])
        layout = super().getLayout(f'{self.name.title()} Control', justification='center', font=font)
        font = (self.typeface, self.font_sizes[title_font_level+1])
        button_names = ['Run','Clear']
        layout = [
            [layout],
            [sg.Push()],
            [sg.Column([self.getButtons(button_names, (5,2), self.name, font)], justification='center')],
            [self.pad()]
        ]
        layout = sg.Column(layout, vertical_alignment='top')
        return layout
    
    def listenEvents(self, event:str, values:dict[str, str]) -> dict[str, str]:
        """
        Listen to events and act on values

        Args:
            event (str): event triggered
            values (dict[str, str]): dictionary of values from window

        Returns:
            dict: dictionary of updates
        """
        updates = {}
        channel_id = values.get(self._mangle('-TABS-'), self.tool.channel)
        
        # 1. Start process
        if event == self._mangle('-Run-'):
            print('Start process')
            parameters = {}
            for key, input_field in self.input_map.items():
                if input_field is None:
                    break
                key_input = self._mangle(f'-{channel_id}-{key}-VALUE-')
                value = self.parseInput(values[key_input])
                parameters[input_field] = value
            print(parameters)
            self.maker.execute(**parameters)
            
        # 2. Clear input fields
        if event == self._mangle('-Clear-'):
            update_part = self._show_defaults(channel_id)
            updates.update(update_part)
        
        # # 3. Reset maker
        # if event == self._mangle('-Reset-'):
        #     print('Reset (not implemented yet)')
        #     # self.maker.reset()
        return updates
    
    # Protected method(s)
    def _show_defaults(self, channel_id:int) -> dict[str, dict]:
        """
        Show the relevant input fields

        Args:
            channel_id (int): channel index

        Returns:
            dict: dictionary of updates
        """
        updates = {}
        defaults = self._defaults.copy()
        if 'channel' in self._parameters:
            defaults.update(channel=channel_id)
        default_map = {k:defaults.get(v,'') for k,v in self.input_map.items()}
        
        for key,default in default_map.items():
            if default is None:
                default = ''
            key_input = self._mangle(f'-{channel_id}-{key}-VALUE-')
            updates[key_input] = dict(value=default)
        return updates
