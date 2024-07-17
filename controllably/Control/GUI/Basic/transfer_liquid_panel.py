# %% -*- coding: utf-8 -*-
"""
This module holds the class for liquid control panels.

Classes:
    LiquidPanel (Panel)
"""
# Standard library imports
from __future__ import annotations
import logging
from threading import Thread
from typing import Callable, Protocol

# Third party imports
import PySimpleGUI as sg    # pip install PySimpleGUI

# Local application imports
from ..multichannel_panel import MultiChannelPanel

logger = logging.getLogger(__name__)
logger.debug(f"Import: OK <{__name__}>")

class Liquid(Protocol):
    capacity: float
    channel: int
    reagent: str
    volume: float
    def aspirate(self, *args, **kwargs):
        ...
    def blowout(self, *args, **kwargs):
        ...
    def dispense(self, *args, **kwargs):
        ...
    def empty(self, *args, **kwargs):
        ...
    def fill(self, *args, **kwargs):
        ...

class LiquidPanel(MultiChannelPanel):
    """
    Liquid Panel class

    ### Constructor
    Args:
        `liquid` (Liquid): liquid transfer object
        `name` (str, optional): name of panel. Defaults to 'LIQUID'.
        `group` (str, optional): name of group. Defaults to 'transfer'.
    
    ### Properties
    - `liquid` (Liquid): alias for `tool`
    
    ### Methods
    - `getChannelPanel`: get the panel layout for a single channel
    - `getLayout`: build `sg.Column` object
    - `listenEvents`: listen to events and act on values
    """
    
    def __init__(self, 
        liquid: Liquid, 
        name: str = 'LIQUID', 
        group: str = 'transfer', 
        **kwargs
    ):
        """
        Instantiate the class

        Args:
            liquid (Liquid): liquid transfer object
            name (str, optional): name of panel. Defaults to 'LIQUID'.
            group (str, optional): name of group. Defaults to 'transfer'.
        """
        super().__init__(name=name, group=group, **kwargs)
        self.tool = liquid
        self._button_keys = tuple()
        self._channels = {}
        if 'channels' in dir(self.tool):
            self._channels = self.tool.channels
        else:
            self._channels = {self.tool.channel: self.tool}
        return
    
    # Properties
    @property
    def liquid(self) -> Liquid:
        return self.tool
    
    def getChannelPanel(self, channel_id:int, tool:Liquid) -> sg.Column:
        """
        Get the panel layout for a single channel

        Args:
            channel_id (int): channel index
            tool (Liquid): tool object

        Returns:
            sg.Column: Column object
        """
        reagent_name = f"{tool.reagent}" if len(tool.reagent) else ''
        font = (self.typeface, self.font_sizes[2])
        slider = sg.Slider(
            (0,tool.capacity), default_value=tool.volume, orientation='v', size=(12,20), key=self._mangle(f'-{channel_id}-SLIDER-'),
            resolution=1, enable_events=False, font=font, disabled=True
        )
        slider_column = sg.Column([
            [sg.Text(tool.capacity, font=font, justification='right', expand_x=True)],
            [slider],
            [sg.Text("0 µL", font=font, justification='right', expand_x=True)],
        ], justification='center', element_justification='center')
        
        font = (self.typeface, self.font_sizes[1])
        button_map = [
            ('fill', "⏫"),
            ('aspirate', "🔼"),
            ('dispense', "🔽"),
            ('empty', "⏬"),
            ('blowout', "⏺️")
        ]
        labels, texts = list(zip(*button_map))
        buttons = self.getButtons(
            labels=[l.upper() for l in labels], size=(5,2), key_prefix=f'{self.name}-{channel_id}', 
            font=font, texts=texts, tooltips=[l.title() for l in labels]
        )
        self._button_keys = tuple([f'-{self.name}-{channel_id}-{l.upper()}-' for l in labels])
        buttons_column = sg.Column([[button] for button in buttons])
        
        fields = ('Volume', 'Speed', 'Cycles', 'Wait', 'Reagent')
        inputs = [self.getInputs(fields=fields, key_prefix=f'{self.name}-{channel_id}')]
        inputs_column = sg.Column(inputs)
        
        checks = ('Pause', 'Blowout')
        checks_column = sg.Column([[sg.Checkbox(
                check, default=False, key=self._mangle(f'-{channel_id}-{check.upper()}-CHECK-')
            ) for check in checks
        ]], justification='right', vertical_alignment='top')
        
        font = (self.typeface, self.font_sizes[2], "bold")
        layout = sg.Column([
            [sg.Text(
                reagent_name, key=self._mangle(f'-{channel_id}-REAGENT-NAME-'),
                font=font, justification='center', expand_x=True
            )],
            [sg.Push()],
            [slider_column, sg.Push(), buttons_column, sg.Push(),], 
            [inputs_column],
            [checks_column]
        ], justification='center')
        return layout
    
    def getLayout(self, title:str = 'Liquid Control', title_font_level:int = 1, **kwargs) -> sg.Column:
        """
        Build `sg.Column` object

        Args:
            title (str, optional): title of layout. Defaults to 'Liquid Control'.
            title_font_level (int, optional): index of font size from levels in `font_sizes`. Defaults to 1.

        Returns:
            sg.Column: Column object
        """
        return super().getLayout(title=title, title_font_level=title_font_level, **kwargs)
    
    def listenEvents(self, event: str, values: dict[str, str]) -> dict[str, str]:
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
        channel_tool = self._channels[channel_id]
        parameters = dict(channel=channel_id)
        if event == '__TIMEOUT__':
            updates[self._mangle(f'-{channel_id}-SLIDER-')] = dict(value=channel_tool.volume)
            updates[self._mangle(f'-{channel_id}-REAGENT-NAME-')] = dict(value=channel_tool.reagent)
            updates[self._mangle(f'-{channel_id}-REAGENT-LABEL-')] = dict(visible=(channel_tool.volume == 0))
            updates[self._mangle(f'-{channel_id}-REAGENT-VALUE-')] = dict(visible=(channel_tool.volume == 0))
            return updates
        
        fields = ('Volume', 'Speed', 'Cycles', 'Wait', 'Reagent')
        for field in fields:
            value = values[self._mangle(f'-{channel_id}-{field.upper()}-VALUE-')]
            if field == 'Reagent':
                parameters[field.lower()] = value if len(value) else ''
                continue
            if len(value) and value.isnumeric():
                parameters[field.lower()] = float(value)
                continue
            if field == 'Volume':
                parameters[field.lower()] = 0
            updates[self._mangle(f'-{channel_id}-{field.upper()}-VALUE-')] = dict(value='')

        checks = ('Pause', 'Blowout')
        for check in checks:
            value = values[self._mangle(f'-{channel_id}-{check.upper()}-CHECK-')]
            parameters[check.lower()] = value
        
        action = None
        if event == self._mangle(f'-{channel_id}-FILL-'):
            action = self.tool.fill
        if event == self._mangle(f'-{channel_id}-ASPIRATE-'):
            action = self.tool.aspirate
        if event == self._mangle(f'-{channel_id}-DISPENSE-'):
            action = self.tool.dispense
        if event == self._mangle(f'-{channel_id}-EMPTY-'):
            action = self.tool.empty
        if event == self._mangle(f'-{channel_id}-BLOWOUT-'):
            if channel_tool.volume == 0:
                action = self.tool.blowout
        
        if action is not None:
            thread = Thread(target=self._freeze_gui, kwargs=(dict(action=action, parameters=parameters)))
            thread.start()
        return updates
    
    # Protected method(s)
    def _freeze_gui(self, action:Callable, parameters:dict, **kwargs):
        """
        Temporarily disable GUI elements when long action is taking place

        Args:
            action (Callable): tool method to be called
            parameters (dict): dictionary of parameters to be passed to the tool method
        """
        for button_key in self._button_keys:
                self.window[button_key].update(disabled=True)
        action(**parameters)
        for button_key in self._button_keys:
            self.window[button_key].update(disabled=False)
        return
    