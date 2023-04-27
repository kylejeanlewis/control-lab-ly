# %% -*- coding: utf-8 -*-
"""
This module holds the class for mover control panels.

Classes:
    MoverPanel (Panel)
"""
# Standard library imports
from __future__ import annotations
import numpy as np
from typing import Callable, Optional, Protocol, Union

# Third party imports
import PySimpleGUI as sg # pip install PySimpleGUI

# Local application imports
from ...misc import Factory, Helper
from .gui_utils import Panel
print(f"Import: OK <{__name__}>")

class Mover(Protocol):
    # attachment: Callable
    heights: dict
    home_coordinates: tuple
    max_actions: int
    possible_attachments: list
    tool_position: tuple(np.ndarray, np.ndarray)
    def home(self, *args, **kwargs):
        ...
    def move(self, *args, **kwargs):
        ...
    def moveTo(self, *args, **kwargs):
        ...
    def reset(self, *args, **kwargs):
        ...
    def rotateTo(self, *args, **kwargs):
        ...
    # def toggleAttachment(self, *args, **kwargs):
    #     ...
    def _transform_out(self, *args, **kwargs):
        ...
        
class MoverPanel(Panel):
    """
    MoverPanel provides methods to create a control panel for a mover

    ### Constructor
    Args:
        `mover` (Mover): Mover object
        `name` (str, optional): name of panel. Defaults to 'MOVE'.
        `group` (str, optional): name of group. Defaults to 'mover'.
        `axes` (Union[list, str], optional): available axes of motion. Defaults to 'XYZabc'.
        
    ### Attributes
    - `attachment_methods` (list[str]): list of methods available to attachment
    - `axes` (list[str]): list of available axes of motion
    - `buttons` (dict[str, tuple[str, float]]) : dictionary of {button id, (axes, value)}
    - `current_attachment` (str): name of current attachment
    - `methods_fn_key_map` (dict[str, str]): dictionary of {button id, button label} 
    
    ### Properties
    - `mover` (Mover): alias for `tool`
    
    ### Methods
    - `getLayout`: build `sg.Column` object
    - `listenEvents`: listen to events and act on values
    """
    
    def __init__(self, 
        mover: Mover, 
        name: str = 'MOVE', 
        group: str = 'mover', 
        axes: Union[list, str] = 'XYZabc', 
        **kwargs
    ):
        """
        Instantiate the class

        Args:
            mover (Mover): mover object
            name (str, optional): name of panel. Defaults to 'MOVE'.
            group (str, optional): name of group. Defaults to 'mover'.
            axes (Union[list, str], optional): available axes of motion. Defaults to 'XYZabc'.
        """
        super().__init__(name=name, group=group, **kwargs)
        self.tool = mover
        
        self.axes = [*axes]
        self.buttons = {}
        self.current_attachment = ''
        self.attachment_methods = []
        self.methods_fn_key_map = {}
        
        self.flags['update_position'] = True
        return
    
    # Properties
    @property
    def mover(self) -> Mover:
        return self.tool
       
    def getLayout(self, title_font_level:int = 1, **kwargs) -> sg.Column:
        """
        Build `sg.Column` object

        Args:
            title_font_level (int, optional): index of font size from levels in font_sizes. Defaults to 1.

        Returns:
            sg.Column: Column object
        """
        font = (self.typeface, self.font_sizes[title_font_level])
        layout = super().getLayout(f'{self.name} Control', justification='center', font=font)
        
        # yaw (alpha/a, about z-axis), pitch (beta/b, about x-axis), roll (gamma/c, about y-axis)
        axes = ['X','Y','Z','a','b','c']
        increments = ['-10','-1','-0.1',0,'+0.1','+1','+10']
        center_buttons = ['home']*2 + ['safe'] + ['zero']*3
        font = (self.typeface, self.font_sizes[title_font_level+1])
        color_codes = {
            'X':None, 'Y':None, 'Z':None,
            'a':'#ffffbb', 'b':'#ffbbff', 'c':'#bbffff'
        }
        tooltips = {
            'X':None, 'Y':None, 'Z':None,
            'a':'Rotation (in degrees) about Z-axis or yaw', 
            'b':'Rotation (in degrees) about Y-axis or roll', 
            'c':'Rotation (in degrees) about X-axis or pitch'
        }
        labels = {axis: [] for axis in axes}
        elements = {}
        input_fields = []
        
        for axis,center in zip(axes, center_buttons):
            specials = {}
            bg_color = color_codes[axis]
            column = sg.Column([[sg.Text(axis, font=font)], 
                                [sg.Input(0, size=(5,2), key=self._mangle(f'-{axis}-VALUE-'), 
                                          tooltip=tooltips[axis],
                                          font=font, background_color=bg_color)]],
                               justification='center', pad=10, visible=(axis in self.axes))
            input_fields.append(column)
            
            if axis in ['a','b','c']:
                orientation = 'v' if axis=='c' else 'h'
                size = (15,20) if axis=='c' else (36,20)
                slider = sg.Slider((-180,180), 0, orientation=orientation, size=size, key=self._mangle(f'-{axis}-SLIDER-'), 
                                   resolution=1, enable_events=True, disable_number_display=True, 
                                   font=font, trough_color=bg_color, visible=(axis in self.axes),
                                   tooltip=tooltips[axis]
                                   )
                elements[axis] = [[self.pad(), slider, self.pad()]]
                continue
            
            if axis not in self.axes:
                elements[axis] = []
                continue
            
            for inc in increments:
                label = f'{axis}\n{inc}' if inc else center
                labels[axis].append(label)
                key = self._mangle(f"-{label}-") if self.name else f"-{label}-"
                self.buttons[key.replace('\n','')] = (axis, float(inc))
            specials[center] = dict(button_color=('#000000', '#ffffff'))
            elements[axis] = self.getButtons(labels[axis], (5,2), self.name, font, specials=specials)
        
        # Generate function buttons
        function_buttons = self._get_function_buttons(font=font)
        
        layout = [
            [layout],
            [self.pad()],
            [
                sg.Column([[sg.Column(elements['b'], justification='right')],
                           [self.pad()],
                           [sg.Column(self.arrangeElements(elements['Z'], form='V')),
                            sg.Column(self.arrangeElements([elements['X'], elements['Y']], form='X'))],
                           [self.pad()],
                           [sg.Column(elements['a'], justification='right')]]), 
                sg.Column(elements['c'])
            ],
            [self.pad()],
            input_fields,
            [self.pad()],
            [sg.Column([self.getButtons(['Go','Clear','Reset'], (5,2), self.name, font)], justification='center')],
            [self.pad()],
            [function_buttons],
            [self.pad()]
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
        tool_position = list(np.concatenate(self.mover.tool_position))
        cache_position = tool_position.copy()
        if event in [self._mangle(f'-{e}-') for e in ('safe', 'home', 'Go', 'Clear', 'Reset')]:
            self.flags['update_position'] = True
            
        # 1. Home
        if event == self._mangle(f'-home-'):
            self.mover.home()
        
        # 2. Safe
        if event == self._mangle(f'-safe-'):
            try:
                coord = tool_position[:2] + [self.mover.heights['safe']]
            except (AttributeError,KeyError):
                coord = self.mover._transform_out(coordinates=self.mover.home_coordinates, tool_offset=True)
                coord = (*tool_position[:2], coord[2])
            if tool_position[2] >= coord[2]:
                print('Already cleared safe height. Staying put...')
            else:
                orientation = tool_position[-3:]
                self.mover.moveTo(coord, orientation)
            
        # 3. XYZ buttons
        if event in self.buttons.keys():
            axis, displacement = self.buttons[event]
            self.mover.move(axis, displacement)
            self.flags['update_position'] = True
            tool_position = list(np.concatenate(self.mover.tool_position))
            
        # 4. abg sliders
        if event in [self._mangle(f'-{axis}-SLIDER-') for axis in ['a','b','c']]:
            orientation = [float(values[self._mangle(f'-{axis}-SLIDER-')]) for axis in ['a','b','c']]
            self.mover.rotateTo(orientation)
            self.flags['update_position'] = True
            tool_position = list(np.concatenate(self.mover.tool_position))
            
        # 5. Go to position
        if event == self._mangle(f'-Go-'):
            coord = [float(values[self._mangle(f'-{axis}-VALUE-')]) for axis in ['X','Y','Z']]
            orientation = [float(values[self._mangle(f'-{axis}-VALUE-')]) for axis in ['a','b','c']]
            self.mover.moveTo(coord, orientation)
            tool_position = list(np.concatenate(self.mover.tool_position))
        
        # 6. Reset mover
        if event == self._mangle(f'-Reset-'):
            self.mover.reset()
            tool_position = cache_position
            
        # 7. Function buttons for attachment
        if event in self.methods_fn_key_map:
            fn_name = self.methods_fn_key_map[event].lower()
            print(fn_name)
            action = getattr(self.mover.attachment, fn_name, None)
            if callable(action):
                action()
                
        # 8. Select attachment
        if event == self._mangle('-ATTACH-'):
            selected_attachment = values[self._mangle('-ATTACH-')]         # COMBO
            if selected_attachment != self.current_attachment:
                if selected_attachment == 'None':
                    selected_attachment = ''
                    self.mover.toggleAttachment(False)
                    self.attachment_methods = []
                    update_part = self._toggle_buttons(False)
                else:
                    selected_attachment_class = Factory.get_class(f"Transfer.Substrate.Dobot.{selected_attachment}")     ### FIXME: hard-coded
                    self.mover.toggleAttachment(True, selected_attachment_class)
                    self.attachment_methods = [method for method in Helper.get_method_names(self.mover.attachment) if not method.startswith('_')]
                    fn_buttons = [l.title() for l in self.attachment_methods]
                    update_part = self._toggle_buttons(True, fn_buttons)
                updates.update(update_part)
            self.current_attachment = selected_attachment
        
        # 9. Update position
        if self.flags['update_position']:
            for i,axis in enumerate(['X','Y','Z','a','b','c']):
                updates[self._mangle(f'-{axis}-VALUE-')] = dict(value=round(tool_position[i],1))
                if axis in ['a','b','c']:
                    updates[self._mangle(f'-{axis}-SLIDER-')] = dict(value=round(tool_position[i],1))
        self.flags['update_position'] = False
        return updates
    
    # Protected method(s)
    def _get_function_buttons(self, font:tuple[str, int]) -> sg.Column:
        """
        Get function buttons for attachment

        Args:
            font (tuple[str, int]): tuple of typeface and font size

        Returns:
            sg.Column: column of labelled buttons if there is an attachment, else placeholder buttons
        """
        show_section = False
        show_buttons = False
        alt_texts = []
        fn_layout = []
        button_labels = [f'FN{i+1}' for i in range(max(self.mover.max_actions,5))]  # Placeholder buttons
        if 'attachment' in dir(self.mover):
            show_section = True
            default_value = self.mover.attachment.__class__.__name__ if self.mover.attachment is not None else 'None'
            dropdown = sg.Combo(
                values=self.mover.possible_attachments+['None'], default_value=default_value,
                size=(20, 1), key=self._mangle('-ATTACH-'), enable_events=True, readonly=True
            )
            dropdown_column = sg.Column([[dropdown]], justification='center')
            fn_layout.append([dropdown_column])
            fn_layout.append([self.pad()])
            if self.mover.attachment is not None:
                show_buttons = True
                self.current_attachment = self.mover.attachment.__class__.__name__
                self.attachment_methods = [method for method in Helper.get_method_names(self.mover.attachment) if not method.startswith('_')]
                alt_texts = [l.title() for l in self.attachment_methods]
                self.methods_fn_key_map = {f'-{self.name}-{k}-':v for k,v in zip(button_labels, alt_texts)}
        buttons = self.getButtons(button_labels, (5,2), self.name, font, texts=alt_texts)
        buttons = [sg.pin(button) for button in buttons]
        buttons_column = sg.Column([buttons], justification='center', visible=show_buttons, key=self._mangle('-FN-BUTTONS-'))
        fn_layout.append([buttons_column])
        
        column = sg.Column(fn_layout, justification='center', visible=show_section)
        return column
     
    def _toggle_buttons(self, on:bool, active_buttons:Optional[list[str]] = None) -> dict[str, dict]:
        """
        Toggle between shown the function buttons for attachment

        Args:
            on (bool): whether to show buttons
            active_buttons (Optional[list[str]], optional): list of method names. Defaults to None.

        Returns:
            dict: dictionary of updates
        """
        updates = {}
        self.methods_fn_key_map = {}
        # Hide all buttons
        if not on:
            updates[self._mangle('-FN-BUTTONS-')] = dict(visible=False)
            return updates
        if active_buttons is None:
            return updates
        
        # Show buttons and change labels
        updates[self._mangle('-FN-BUTTONS-')] = dict(visible=True)
        for i,method in enumerate(active_buttons):
            key_button = self._mangle(f'-FN{i+1}-')
            updates[key_button] = dict(visible=True, text=method)
            self.methods_fn_key_map[key_button] = method
        
        # Hide remaining buttons
        for j in range(i+1, max(self.mover.max_actions,5)):
            key_button = self._mangle(f'-FN{j+1}-')
            updates[key_button] = dict(visible=False, text=f'FN{j+1}')
        return updates
