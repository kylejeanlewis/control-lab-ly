# %% -*- coding: utf-8 -*-
"""
This module holds pop-up functions.

Functions:
    get_combo_box
    get_image_labeller
    get_listbox
    get_notification
"""
# Standard library imports
from __future__ import annotations
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

def get_image_labeller(img:str = 'draw.png', data:bytes = None, img_size:tuple[int] = (400,400)):
    """
    WIP: Get new pop-up to annotate rectangles on image
    
    Adapted from https://github.com/PySimpleGUI/PySimpleGUI/blob/master/DemoPrograms/Demo_Graph_Drawing_And_Dragging_Figures.py

    Args:
        img (str, optional): filename of image. Defaults to 'draw.png'.
        data (bytes, optional): encoded image data. Defaults to None.
        img_size (tuple, optional): size of image. Defaults to (400,400).

    Returns:
        list: list of rectangle positions
    """
    col = [
        [sg.Text('Choose what clicking a figure does')],
        [sg.Radio('Draw Rectangles', group_id=1, key='-RECT-', size=(20,1), enable_events=True, default=True)],
        [sg.Radio('Erase all', group_id=1, key='-CLEAR-', size=(20,1), enable_events=True)],
        [sg.Button('Save & Close', size=(10,1), key='-SAVE-')],
    ]

    layout = [[
                sg.Graph(
                    canvas_size=img_size,
                    graph_bottom_left=(0,0),
                    graph_top_right=img_size,
                    key="-GRAPH-",
                    enable_events=True,
                    drag_submits=True,
                    right_click_menu=[[],['Erase item',]]
                ), 
                sg.Col(col, key='-COL-') 
            ],
            [sg.Text('', size=(60, 1), key='-INFO-')]
        ]

    window = sg.Window("Manually Annotate Targets", layout, finalize=True, modal=True)
    graph: sg.Graph = window["-GRAPH-"]
    info: sg.Text = window["-INFO-"]
    try:
        graph.draw_image(data=data, location=(0,img_size[1]))
    except:
        graph.draw_image(img, location=(0,img_size[1]))

    dragging = False
    start_point = end_point = prior_rect = None
    
    positions = []
    while True:
        event, values = window.read()
        if event in ('-SAVE-', sg.WIN_CLOSED, sg.WINDOW_CLOSE_ATTEMPTED_EVENT, None):
            break

        elif not event.startswith('-GRAPH-'):
            graph.set_cursor(cursor='left_ptr')

        if event == "-GRAPH-":
            x, y = values["-GRAPH-"]
            if not dragging:
                start_point = (x, y)
                dragging = True
                drag_figures = graph.get_figures_at_location((x,y))[1:]
                lastxy = x,y
            else:
                end_point = (x, y)
            if prior_rect:
                graph.delete_figure(prior_rect)
            delta_x, delta_y = x - lastxy[0], y - lastxy[1]
            lastxy = x,y
            if None not in (start_point, end_point):
                if values['-RECT-']:
                    prior_rect = graph.draw_rectangle(start_point, end_point, fill_color=None, line_color='green')
                    
                elif values['-CLEAR-']:
                    positions = []
                    graph.erase()
                    try:
                        graph.draw_image(data=data, location=(0,img_size[1]))
                    except:
                        graph.draw_image(img, location=(0,img_size[1]))
                
            info.update(value=f"mouse {values['-GRAPH-']}")
        elif event.endswith('+UP'):  # The drawing has ended because mouse up
            info.update(value=f"grabbed rectangle from {start_point} to {end_point}")
            if values['-RECT-'] and start_point and end_point:
                start_point = (start_point[0], img_size[1]-start_point[1])
                end_point = (end_point[0], img_size[1]-end_point[1])
                rect = {
                    0: min(start_point[0], end_point[0]), 
                    1: min(start_point[1], end_point[1]), 
                    2: abs(start_point[0] - end_point[0]), 
                    3: abs(start_point[1] - end_point[1])}
                positions.append(rect)
                point_x = (end_point[0] + start_point[0])/2
                point_y = img_size[1] - (end_point[1] + start_point[1])/2
                graph.draw_point((point_x, point_y), size=5, color='red')
            start_point, end_point = None, None  # enable grabbing a new rect
            dragging = False
            prior_rect = None
        elif event.endswith('+RIGHT+'):  # Right click
            info.update(value=f"Right clicked location {values['-GRAPH-']}")
        elif event.endswith('+MOTION+'):  # Right click
            info.update(value=f"mouse freely moving {values['-GRAPH-']}")
    window.close()
    return positions

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
