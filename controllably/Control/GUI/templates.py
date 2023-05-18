# %% -*- coding: utf-8 -*-
"""
This module holds functions to generate panel templates.

Functions:
    get_computer_vision_controls
    get_directory_selector
"""
# Standard library imports
from typing import Optional

# Third party imports
import PySimpleGUI as sg                # pip install PySimpleGUI

# Local application imports
print(f"Import: OK <{__name__}>")

FONT = "Helvetica"
TEXT_SIZE = 10
TITLE_SIZE = 12

def get_computer_vision_controls(**kwargs) -> sg.Column:
    """
    Get controls for Open CV detection

    Returns:
        sg.Column: computer vision controls
    """
    font_text = kwargs.get('font_text', (FONT, TEXT_SIZE))
    font_title = kwargs.get('font_title', (FONT, TITLE_SIZE))
    size_label = (20,1)
    size_overall = (64,1)
    size_radio = (int(size_overall[0]/8), 1)
    size_slider = (40,10)
    column = [
        [sg.Text("OpenCV Haar Cascade", size=size_overall, justification='center', font=(*font_title,'bold'))],
        [
            sg.Text("Brightness  ", size=size_label, justification='right', font=font_text), 
            sg.Slider((0,100), default_value=0, orientation='h', size=size_slider, key="-BRIGHTNESS SLIDER-")
        ],
        [
            sg.Text("Contrast  ", size=size_label, justification='right', font=font_text), 
            sg.Slider((0,5), default_value=1, orientation='h', size=size_slider, key="-CONTRAST SLIDER-")
        ],
        
        [sg.Text("Gaussian Blurring Kernel", size=size_overall, font=(*font_text,'bold'))],
        [
            sg.Push(), 
            sg.Radio('Disable', group_id='blurring_kernel', size=size_radio, key="-KERNEL DISABLE-", default=True), 
            sg.Radio('3x3', group_id='blurring_kernel', size=size_radio, key="-3x3 KERNEL SIZE-"),
            sg.Radio('5x5', group_id='blurring_kernel', size=size_radio, key="-5x5 KERNEL SIZE-"), 
            sg.Radio('9x9', group_id='blurring_kernel', size=size_radio, key="-9x9 KERNEL SIZE-"), 
            sg.Push()
        ],
        
        [
            sg.Text("Device Detection (Haar Cascade & Contour Detection)", size=(50, 1), font=(*font_text,'bold')),
            sg.Checkbox("Pause detection", default=True, size=(14,1), key="-PAUSE DETECT-")
        ],
        [
            sg.Text("Scale Factor  ", size=size_label, justification='right', font=font_text), 
            sg.Slider((50,1000), default_value=525, orientation='h', size=size_slider, key="-SCALE SLIDER-")
        ], 
        [
            sg.Text("Min Neighbour  ", size=size_label, justification='right', font=font_text), 
            sg.Slider((0,20), default_value=10, orientation='h', size=size_slider, key="-NEIGHBOR SLIDER-")
        ],
        [
            sg.Text("BG Noise Removal  ", size=size_label, justification='right', font=font_text), 
            sg.Slider((0,5), default_value=0, orientation='h', size=size_slider, key="-OPENING SLIDER-")
        ], 
        [
            sg.Text("FG Noise Removal  ", size=size_label, justification='right', font=font_text), 
            sg.Slider((0,5), default_value=0, orientation='h', size=size_slider, key="-CLOSING SLIDER-")
        ]
    ]
    return sg.Column(column)

def get_directory_selector(field:str, file:bool = True, default:Optional[str] = None, **kwargs) -> sg.Column:
    """
    Get file / folder selector control

    Args:
        field (str): name of field
        file (bool, optional): whether to select a file. Defaults to True.
        default (str, optional): default file / folder. Defaults to ''.

    Returns:
        sg.Column: directory selector
    """
    selector = None
    key = f"-{field.upper()} BROWSE-"
    font = kwargs.get('font', (FONT, TEXT_SIZE))
    size = kwargs.get('size', (8,1))
    
    if file:
        default_folder = '/'.join(default.split('/')[:-1]) if default else None
        selector = sg.FileBrowse(size=size, font=font, key=key, initial_folder=default_folder)
    else:
        selector = sg.FolderBrowse(size=size, font=font, key=key, initial_folder=default)
    
    column = [
        [sg.Push()],
        [
            sg.Text(f"Choose {field} location: ", size=(20,1), justification='right'), 
            sg.Input(default, size=(36,1), key=f"-{field.upper()} DIR-", enable_events=True), 
            selector
        ]
    ]
    return sg.Column(column)
