# %% -*- coding: utf-8 -*-
"""
This module holds the class for measurer control panels.

Classes:
    MeasurerPanel (Panel)
    ProgramDetails (dataclass)
"""
# Standard library imports
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Protocol, Callable, Any

# Third party imports
import PySimpleGUI as sg # pip install PySimpleGUI

# Local application imports
from ... import modules
from .gui_utils import Panel
print(f"Import: OK <{__name__}>")

@dataclass
class ProgramDetails:
    """
    ProgramDetails dataclass represents the set of inputs, default values, truncated docstring and tooltip of a program class.
    <from `controllably.Measure.program_utils`>
    
    ### Constructor
    Args:
        `inputs` (list[str]): list of input field names
        `defaults` (dict[str, Any]): dictionary of kwargs and default values
        `short_doc` (str): truncated docstring of the program
        `tooltip` (str): descriptions of input fields
    """
    
    inputs: list[str] = field(default_factory=lambda: [])
    defaults: dict[str, Any] = field(default_factory=lambda: {})
    short_doc: str = ''
    tooltip: str = ''

class Measurer(Protocol):
    _place: str
    program_details: ProgramDetails
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

    ### Constructor
    Args:
        `measurer` (Measurer): Measurer object
        `name` (str, optional): name of panel. Defaults to 'MEASURE'.
        `group` (str, optional): name of group. Defaults to 'measurer'.
        
    ### Attributes
    - `current_program` (str): currently active program
    - `input_map` (dict[int, Optional[str]]): enumerated map of program inputs
    
    ### Properties
    - `measurer` (Measurer): alias for `tool`
    
    ### Methods
    - `getLayout`: build `sg.Column` object
    - `listenEvents`: listen to events and act on values
    """
    
    _default_input_map: dict = {f"INPUT-{i:02}": None for i in range(20)}
    def __init__(self, 
        measurer: Measurer, 
        name: str = 'MEASURE', 
        group: str = 'measurer', 
        **kwargs
    ):
        """
        Instantiate the class

        Args:
            measurer (Measurer): Measurer object
            name (str, optional): name of panel. Defaults to 'MEASURE'.
            group (str, optional): name of group. Defaults to 'measurer'.
        """
        super().__init__(name=name, group=group, **kwargs)
        self.tool = measurer
        self.current_program = ''
        self.input_map = self._default_input_map
        return
    
    # Properties
    @property
    def measurer(self) -> Measurer:
        return self.tool
    
    def getLayout(self, title_font_level:int = 0, **kwargs) -> sg.Column:
        """
        Build `sg.Column` object

        Args:
            title_font_level (int, optional): index of font size from levels in font_sizes. Defaults to 0.

        Returns:
            sg.Column: Column object
        """
        font = (self.typeface, self.font_sizes[title_font_level])
        layout = super().getLayout(f'{self.name.title()} Control', justification='center', font=font)
        
        font = (self.typeface, self.font_sizes[title_font_level+1])
        # add dropdown for program list
        programs = eval(f"modules.at.{self.measurer._place}.programs")
        program_names = [p for p in programs]
        dropdown = sg.Combo(
            values=program_names, size=(20, 1), 
            key=self._mangle('-PROGRAMS-'), enable_events=True, readonly=True
        )
        
        # add template for procedurally adding input fields
        labels_inputs = self.getInputs(fields=[i for i in self.input_map], key_prefix=self.name, initial_visibility=False)
        
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
            values (dict[str, str]): dictionary of values from window

        Returns:
            dict: dictionary of updates
        """
        updates = {}
        # 1. Select program
        if event == self._mangle('-PROGRAMS-'):
            selected_program = values[self._mangle('-PROGRAMS-')]       # COMBO
            if selected_program != self.current_program:
                self.measurer.loadProgram(eval(f"modules.at.{self.measurer._place}.programs.{selected_program}"))
                update_part = self._show_inputs(self.measurer.program_details)
                updates.update(update_part)
            self.current_program = selected_program
        
        # 2. Start measure
        if event == self._mangle('-Run-'):
            if self.measurer.program_type is not None:
                print('Start measure')
                parameters = {}
                for key, input_field in self.input_map.items():
                    if input_field is None:
                        break
                    key_input = self._mangle(f'-{key}-VALUE-')
                    value = self.parseInput(values[key_input])
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
            update_part = self._show_inputs(self.measurer.program_details)
            updates.update(update_part)
        return updates
    
    # Protected method(s)    
    def _show_inputs(self, program_details: ProgramDetails) -> dict[str, dict]:
        """
        Show the relevant input fields

        Args:
            program_details (ProgramDetails): details of loaded program

        Returns:
            dict: dictionary of updates
        """
        updates = {}
        self.input_map = self._default_input_map
        for key_id, input_field in enumerate(program_details.inputs):
            self.input_map[f"INPUT-{key_id:02}"] = input_field
        
        for key, input_field in self.input_map.items():
            key_label = self._mangle(f'-{key}-LABEL-')
            key_input = self._mangle(f'-{key}-VALUE-')
            updates[f'{key_label}BOX-'] = dict(visible=False)
            updates[f'{key_input}BOX-'] = dict(visible=False)
            if input_field is None:
                continue
            if input_field in program_details.inputs:
                updates[key_label] = dict(tooltip=program_details.tooltip,
                                          value=input_field.title())
                updates[key_input] = dict(tooltip=program_details.tooltip, 
                                          value=program_details.defaults.get(input_field,''))
                updates[f'{key_label}BOX-'] = dict(visible=True)
                updates[f'{key_input}BOX-'] = dict(visible=True)
        return updates
