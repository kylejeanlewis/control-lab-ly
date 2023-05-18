# %% -*- coding: utf-8 -*-
"""
This module holds functions to generate panel templates.

Functions:
    get_combo_box
    get_notification
"""
# Standard library imports
from typing import Optional

# Third party imports
import PySimpleGUI as sg                # pip install PySimpleGUI

# Local application imports
print(f"Import: OK <{__name__}>")

FONT = "Helvetica"
TEXT_SIZE = 10

def get_combo_box(message:str, options:Optional[list] = None, allow_input:bool = False, **kwargs) -> str:
    """
    Get a combo box (drop-down list) pop-up, with optional input field

    Args:
        message (str): message string
        options (Optional[list], optional): list of options. Defaults to None.
        allow_input (bool, optional): whether to allow user input. Defaults to False.

    Returns:
        str: selected option
    """
    lines = message.split("\n")
    w = max([len(line) for line in lines])
    h = len(lines)
    
    font = kwargs.get('font_text', (FONT, TEXT_SIZE))
    options = options if options is not None else []
    options = [''] + options
    layout = [
        [sg.Text(message, size=(w+2, h))],
        [sg.Combo(options, options[0], key='-COMBO-', size=(20,1), font=font, enable_events=True)],
        [sg.Input('', size=(20,1), key='-INPUT', visible=allow_input)],
        [sg.Button('OK', size=(10, 1))]
    ]
    
    window = sg.Window('Select', layout, finalize=True, modal=True, resizable=True)
    selected = options[0]
    while True:
        event, values = window.read(timeout=20)
        if event in ('OK', sg.WIN_CLOSED, sg.WINDOW_CLOSE_ATTEMPTED_EVENT, None):
            input_text = values['-INPUT-']
            selected = input_text if input_text else 'unknown'
            print(f'Selected: {selected}')
            break
        
        if event == '-COMBO-':
            selected_option = values['-COMBO-']
            window['-INPUT-'].update(value=selected_option)
            pass
    window.close()
    return selected

def get_listbox(message:str, **kwargs) -> list:
    """
    Get a listbox (multiple selection field) pop-up

    Args:
        message (str): message string

    Returns:
        list: selected option(s)
    """
    lines = message.split("\n")
    w = max([len(line) for line in lines])
    h = len(lines)
    
    font = kwargs.get('font_text', (FONT, TEXT_SIZE))
    options = options if options is not None else []
    options = [''] + options
    layout = [
        [sg.Text(message, size=(w+2, h))],
        [sg.Listbox(
            options, options, select_mode=sg.LISTBOX_SELECT_MODE_MULTIPLE, 
            key='-LISTBOX-', size=(20, min(10, len(options))), font=font
        )],
        [sg.Button('OK', size=(10, 1))]
    ]
    
    window = sg.Window('Select', layout, finalize=True, modal=True, resizable=True)
    selected = options
    while True:
        event, values = window.read(timeout=20)
        if event in ('OK', sg.WIN_CLOSED, sg.WINDOW_CLOSE_ATTEMPTED_EVENT, None):
            selected = values['-LISTBOX-']
            print(f'Selected: {selected}')
            break
    window.close()
    return selected

def get_notification(message:str = 'Note!'):
    """
    Get notification pop-up

    Args:
        message (str, optional): notification message. Defaults to 'Note!'.
    """
    lines = message.split("\n")
    w = max([len(line) for line in lines])
    h = len(lines)
    layout = [
        [sg.Text(message, size=(w+2, h), justification='center')], 
        [sg.Button('OK', size=(w+2, h))]
    ]
    
    window = sg.Window('Note', layout, finalize=True, modal=True)
    while True:
        event, values = window.read(timeout=20)
        if event in ('OK', sg.WIN_CLOSED, sg.WINDOW_CLOSE_ATTEMPTED_EVENT, None):
            break
    window.close()
    return
