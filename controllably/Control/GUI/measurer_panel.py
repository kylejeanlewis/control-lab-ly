# %% -*- coding: utf-8 -*-
"""
Created: Tue 2022/11/30 10:30:00
@author: Chang Jie

Notes / actionables:
- 
"""
# Standard library imports
from __future__ import annotations
from typing import Protocol, Callable

# Third party imports
import PySimpleGUI as sg # pip install PySimpleGUI

# Local application imports
from .gui_utils import Panel
print(f"Import: OK <{__name__}>")

class Measurer(Protocol):
    available_programs: list[str]
    possible_inputs: list[str]
    program_details: dict
    program_type: Callable
    def loadProgram(self, *args, **kwargs):
        ...
    def measure(self, *args, **kwargs):
        ...
    def reset(self, *args, **kwargs):
        ...

class MeasurerPanel(Panel):
    """
    Measurer Panel class

    Args:
        measurer (obj): Measurer object
        name (str, optional): name of panel. Defaults to 'MEASURE'.
        theme (str, optional): name of theme. Defaults to THEME.
        typeface (str, optional): name of typeface. Defaults to TYPEFACE.
        font_sizes (list, optional): list of font sizes. Defaults to FONT_SIZES.
        group (str, optional): name of group. Defaults to 'measurer'.
    """
    def __init__(self, 
        measurer: Measurer, 
        name: str = 'MEASURE', 
        group: str = 'measurer', 
        **kwargs
    ):
        super().__init__(name=name, group=group, **kwargs)
        self.measurer = measurer
        self.current_program = ''
        return
    
    def getLayout(self, title_font_level=0, **kwargs) -> sg.Column:
        """
        Get layout object

        Args:
            title (str, optional): title of layout. Defaults to 'Panel'.
            title_font_level (int, optional): index of font size from levels in font_sizes. Defaults to 0.

        Returns:
            PySimpleGUI.Column: Column object
        """
        font = (self.typeface, self.font_sizes[title_font_level])
        layout = super().getLayout(f'{self.name} Control', justification='center', font=font)
        
        font = (self.typeface, self.font_sizes[title_font_level+1])
        # add dropdown for program list
        dropdown = sg.Combo(
            values=self.measurer.available_programs, size=(20, 1), 
            key=self._mangle('-PROGRAMS-'), enable_events=True, readonly=True
        )
        
        # add template for procedurally adding input fields
        labels_inputs = self._get_input_section()
        
        # add run, clear, reset buttons
        layout = [
            [layout],
            [self.pad()],
            [sg.Column([[dropdown]], justification='center')],
            [self.pad()],
            labels_inputs,
            [self.pad()],
            [sg.Column([self.getButtons(['Run','Clear','Reset'], (5,2), self.name, font)], justification='center')],
            [self.pad()]
        ]
        layout = sg.Column(layout, vertical_alignment='top')
        return layout
    
    def listenEvents(self, event:str, values:dict[str, str]) -> dict[str, str]:
        """
        Listen to events and act on values

        Args:
            event (str): event triggered
            values (dict): dictionary of values from window

        Returns:
            dict: dictionary of updates
        """
        updates = {}
        # 1. Select program
        if event == self._mangle('-PROGRAMS-'):
            selected_program = values[self._mangle('-PROGRAMS-')]       # COMBO
            if selected_program != self.current_program:
                self.measurer.loadProgram(selected_program)
                update_part = self._show_inputs(self.measurer.program_details['inputs_and_defaults'])
                updates.update(update_part)
            self.current_program = selected_program
        
        # 2. Start measure
        if event == self._mangle('-Run-'):
            if self.measurer.program_type is not None:
                print('Start measure')
                parameters = {}
                for input_field in self.measurer.program_details['inputs_and_defaults']:
                    key = self._mangle(f'-{input_field}-VALUE-')
                    if key in values.keys():
                        value = self.parseInput(values[key])
                        parameters[input_field] = value
                print(parameters)
                self.measurer.measure(parameters=parameters)
            else:
                print('Please select a program first.')
        
        # 3. Reset measurer
        if event == self._mangle('-Reset-'):
            print('Reset')
            self.measurer.reset()
        
        # 4. Clear input fields
        if event == self._mangle('-Clear-'):
            update_part = self._show_inputs(self.measurer.program_details['inputs_and_defaults'])
            updates.update(update_part)
        return updates
    
    # Protected method(s)
    def _show_inputs(self, active_inputs:dict) -> dict[str, dict]:
        """
        Show the relevant input fields

        Args:
            active_inputs (list): list of relevant input fields

        Returns:
            dict: dictionary of updates
        """
        updates = {}
        for input_field in self.measurer.possible_inputs:
            key_label = self._mangle(f'-{input_field}-LABEL-')
            key_input = self._mangle(f'-{input_field}-VALUE-')
            updates[f'{key_label}BOX-'] = dict(visible=False)
            updates[f'{key_input}BOX-'] = dict(visible=False)
            if input_field in active_inputs.keys():
                updates[key_label] = dict(tooltip=self.measurer.program_details['tooltip'])
                updates[key_input] = dict(tooltip=self.measurer.program_details['tooltip'], 
                                          value=active_inputs[input_field])
                updates[f'{key_label}BOX-'] = dict(visible=True)
                updates[f'{key_input}BOX-'] = dict(visible=True)
        return updates

    def _get_input_section(self):
        """
        Get the layout for the input section

        Returns:
            list: list of columns
        """
        # template for procedurally adding input fields
        labels = []
        inputs = []
        for input_field in self.measurer.possible_inputs:
            key_label = self._mangle(f'-{input_field}-LABEL-')
            key_input = self._mangle(f'-{input_field}-VALUE-')
            _label = sg.pin(
                sg.Column(
                    [[sg.Text(input_field.title(), key=key_label, visible=True)]],
                    key=f'{key_label}BOX-', visible=False
                )
            )
            _input = sg.pin(
                sg.Column(
                    [[sg.Input(0, size=(5,2), key=key_input, visible=True, tooltip='')]],
                    key=f'{key_input}BOX-', visible=False
                )
            )
            labels.append([_label])
            inputs.append([_input])
        labels_column = sg.Column(labels, justification='right', pad=10, visible=True)
        inputs_column = sg.Column(inputs, justification='left', pad=10, visible=True)
        labels_inputs = [labels_column, inputs_column]
        return labels_inputs
    