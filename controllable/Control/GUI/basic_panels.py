# %% -*- coding: utf-8 -*-
"""
Created: Tue 2022/11/30 10:30:00
@author: Chang Jie

Notes / actionables:
- 
"""
# Standard library imports
import numpy as np
import time

# Third party imports
import PySimpleGUI as sg # pip install PySimpleGUI

# Local application imports
from...Measure.Electrical import Electrical
from .gui_utils import Panel
print(f"Import: OK <{__name__}>")

WIDTH, HEIGHT = sg.Window.get_screen_size()
THEME = 'LightGreen'
TYPEFACE = "Helvetica"
FONT_SIZES = [14,12,10,8,6]

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
    def __init__(self, measurer:Electrical, name='MEASURE', theme=THEME, typeface=TYPEFACE, font_sizes=FONT_SIZES, group='measurer'):
        super().__init__(name=name, theme=theme, typeface=typeface, font_sizes=font_sizes, group=group)
        self.current_program = ''
        self.measurer = measurer
        return
    
    def close(self):
        """
        Close window
        """
        return super().close()
    
    def getLayout(self, title='Panel', title_font_level=0, **kwargs):
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
        dropdown = sg.Listbox(values=self.measurer.available_programs, size=(20, 5), key=self._mangle('-PROGRAMS-'), enable_events=True)
        
        # add template for procedurally adding input fields
        labels = []
        inputs = []
        for input_field in self.measurer.possible_inputs:
            _label = sg.Column([[sg.Text(input_field.title(), key=self._mangle(f'-{input_field}-LABEL-'), visible=False)]])
            _input = sg.Column([[sg.Input(0, size=(5,2), key=self._mangle(f'-{input_field}-VALUE-'), visible=False, tooltip='')]])
            labels.append([_label])
            inputs.append([_input])
        labels_column = sg.Column(labels, justification='right', pad=10, visible=True)
        inputs_column = sg.Column(inputs, justification='left', pad=10, visible=True)
        labels_inputs = [labels_column, inputs_column]
        
        # add run, clear, reset buttons
        layout = [
            [layout],
            [self._pad()],
            [sg.Column([[dropdown]], justification='center')],
            [self._pad()],
            labels_inputs,
            [self._pad()],
            [sg.Column([self.getButtons(['Run','Clear','Reset'], (5,2), self.name, font)], justification='center')],
            [self._pad()]
        ]
        layout = sg.Column(layout, vertical_alignment='top')
        return layout
    
    def listenEvents(self, event, values):
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
            selected_program = values[self._mangle('-PROGRAMS-')][0]
            if selected_program != self.current_program:
                self.measurer.loadProgram(selected_program)
                update = self.showInputs(self.measurer.program_details['inputs_and_defaults'])
                updates.update(update)
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
            update = self.showInputs(self.measurer.program_details['inputs_and_defaults'])
            updates.update(update)
        return updates
    
    def showInputs(self, active_inputs:list):
        updates = {}
        for input_field in self.measurer.possible_inputs:
            key_label = self._mangle(f'-{input_field}-LABEL-')
            key_input = self._mangle(f'-{input_field}-VALUE-')
            updates[key_label] = dict(visible=False)
            updates[key_input] = dict(visible=False)
            if input_field in active_inputs.keys():
                updates[key_label] = dict(visible=True, tooltip=self.measurer.program_details['tooltip'])
                updates[key_input] = dict(visible=True, value=active_inputs[input_field], 
                                          tooltip=self.measurer.program_details['tooltip'])
        return updates


class MoverPanel(Panel):
    """
    Mover Panel class

    Args:
        mover (obj): Mover object
        name (str, optional): name of panel. Defaults to 'MOVE'.
        theme (str, optional): name of theme. Defaults to THEME.
        typeface (str, optional): name of typeface. Defaults to TYPEFACE.
        font_sizes (list, optional): list of font sizes. Defaults to FONT_SIZES.
        group (str, optional): name of group. Defaults to 'mover'.
        axes (list, optional): list of degrees of freedom/axes. Defaults to ['X','Y','Z','a','b','c'].
    """
    def __init__(self, mover, name='MOVE', theme=THEME, typeface=TYPEFACE, font_sizes=FONT_SIZES, group='mover', axes=['X','Y','Z','a','b','c']):
        super().__init__(name=name, theme=theme, typeface=typeface, font_sizes=font_sizes, group=group)
        self.axes = axes
        self.buttons = {}
        self.mover = mover
        self.flags['update_position'] = True
        return
        
    def getLayout(self, title_font_level=1, **kwargs):
        """
        Get layout object

        Args:
            title_font_level (int, optional): index of font size from levels in font_sizes. Defaults to 1.

        Returns:
            PySimpleGUI.Column: Column object
        """
        font = (self.typeface, self.font_sizes[title_font_level])
        layout = super().getLayout(f'{self.name} Control', justification='center', font=font)
        
        # yaw (alpha, about z-axis), pitch (beta, about x-axis), roll (gamma, about y-axis)
        axes = ['X','Y','Z','a','b','c']
        increments = ['-10','-1','-0.1',0,'+0.1','+1','+10']
        center_buttons = ['home']*2 + ['safe'] + ['zero']*3
        font = (self.typeface, self.font_sizes[title_font_level+1])
        color_codes = {
            'X':None, 'Y':None, 'Z':None,
            # 'X':'#bbbbff', 'Y':'#bbffbb', 'Z':'#ffbbbb',
            'a':'#ffffbb', 'b':'#ffbbff', 'c':'#bbffff'
        }
        tooltips = {
            'X':None, 'Y':None, 'Z':None,
            'a':'Rotation (in degrees) about Z-axis', 
            'b':'Rotation (in degrees) about Y-axis', 
            'c':'Rotation (in degrees) about X-axis'
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
                elements[axis] = [[self._pad(), slider, self._pad()]]
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
        
        layout = [
            [layout],
            [self._pad()],
            [
                sg.Column([[sg.Column(elements['b'], justification='right')],
                           [self._pad()],
                           [sg.Column(self.arrangeElements(elements['Z'], form='V')),
                            sg.Column(self.arrangeElements([elements['X'], elements['Y']], form='X'))],
                           [self._pad()],
                           [sg.Column(elements['a'], justification='right')]]), 
                sg.Column(elements['c'])
            ],
            [self._pad()],
            input_fields,
            [self._pad()],
            [sg.Column([self.getButtons(['Go','Clear','Reset'], (5,2), self.name, font)], justification='center')],
            [self._pad()]
        ]
        layout = sg.Column(layout, vertical_alignment='top')
        return layout
    
    def listenEvents(self, event, values):
        """
        Listen to events and act on values

        Args:
            event (str): event triggered
            values (dict): dictionary of values from window

        Returns:
            dict: dictionary of updates
        """
        updates = {}
        tool_position = list(np.concatenate(self.mover.getToolPosition()))
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
            tool_position = list(np.concatenate(self.mover.getToolPosition()))
            
        # 4. abg sliders
        if event in [self._mangle(f'-{axis}-SLIDER-') for axis in ['a','b','c']]:
            orientation = [float(values[self._mangle(f'-{axis}-SLIDER-')]) for axis in ['a','b','c']]
            self.mover.rotateTo(orientation)
            self.flags['update_position'] = True
            tool_position = list(np.concatenate(self.mover.getToolPosition()))
            
        # 5. Go to position
        if event == self._mangle(f'-Go-'):
            coord = [float(values[self._mangle(f'-{axis}-VALUE-')]) for axis in ['X','Y','Z']]
            orientation = [float(values[self._mangle(f'-{axis}-VALUE-')]) for axis in ['a','b','c']]
            self.mover.moveTo(coord, orientation)
            tool_position = list(np.concatenate(self.mover.getToolPosition()))
        
        # 6. Reset mover
        if event == self._mangle(f'-Reset-'):
            self.mover.reset()
            tool_position = cache_position
        
        # 7. Update position
        if self.flags['update_position']:
            for i,axis in enumerate(['X','Y','Z','a','b','c']):
                updates[self._mangle(f'-{axis}-VALUE-')] = dict(value=tool_position[i])
                if axis in ['a','b','c']:
                    updates[self._mangle(f'-{axis}-SLIDER-')] = dict(value=tool_position[i])
        self.flags['update_position'] = False
        return updates


class ViewerPanel(Panel):
    """
    Viewer Panel class

    Args:
        viewer (obj): Viewer object
        name (str, optional): name of panel. Defaults to 'VIEW'.
        theme (str, optional): name of theme. Defaults to THEME.
        typeface (str, optional): name of typeface. Defaults to TYPEFACE.
        font_sizes (list, optional): list of font sizes. Defaults to FONT_SIZES.
        group (str, optional): name of group. Defaults to 'viewer'.
    """
    def __init__(self, viewer, name='VIEW', theme=THEME, typeface=TYPEFACE, font_sizes=FONT_SIZES, group='viewer'):
        super().__init__(name=name, theme=theme, typeface=typeface, font_sizes=font_sizes, group=group)
        self.viewer = viewer
        self.display_box = self._mangle('-IMAGE-')
        
        self.flags['update_display'] = True
        self._last_read_time = time.time()
        return
    
    def close(self):
        """
        Close window
        """
        self.viewer.close()
        return
        
    def getLayout(self, title_font_level=1, **kwargs):
        """
        Get layout object

        Args:
            title_font_level (int, optional): index of font size from levels in font_sizes. Defaults to 1.

        Returns:
            PySimpleGUI.Column: Column object
        """
        font = (self.typeface, self.font_sizes[title_font_level])
        layout = super().getLayout(f'{self.name} Control', justification='center', font=font)
        layout = [
            [layout],
            [sg.Image(filename='', key=self.display_box, enable_events=True)]
        ]
        layout = sg.Column(layout, vertical_alignment='top')
        return layout
    
    def listenEvents(self, event, values):
        """
        Listen to events and act on values

        Args:
            event (str): event triggered
            values (dict): dictionary of values from window

        Returns:
            dict: dictionary of updates
        """
        updates = {}
        if self.flags['update_display']:
            frame_interval = time.time() - self._last_read_time
            fps = round(1/frame_interval, 2)
            ret, image = self.viewer.getImage()
            self._last_read_time = time.time()
            if ret:
                image = image.addText(f'FPS: {fps}', position=(0,image.frame.shape[0]-5), inplace=False)
            updates[self.display_box] = dict(data=image.encode())
        return updates


class LoaderPanel(Panel):
    """
    Loader Panel class

    Args:
        name (str, optional): name of panel. Defaults to ''.
        theme (str, optional): name of theme. Defaults to THEME.
        typeface (str, optional): name of typeface. Defaults to TYPEFACE.
        font_sizes (list, optional): list of font sizes. Defaults to FONT_SIZES.
        group (str, optional): name of group. Defaults to None.
    """
    def __init__(self, name='', theme=THEME, typeface=TYPEFACE, font_sizes=FONT_SIZES, group=None):
        super().__init__(name, theme, typeface, font_sizes, group)
        return
