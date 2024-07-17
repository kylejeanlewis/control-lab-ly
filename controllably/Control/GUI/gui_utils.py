# %% -*- coding: utf-8 -*-
"""
This module holds the base class for control panels.

Classes:
    Panel (ABC)

Other constants and variables:
    HEIGHT (int): height of screen size in number of pixels
    WIDTH (int): width of screen size in number of pixels
"""
# Standard library imports
from __future__ import annotations
from abc import ABC, abstractmethod
import logging
from typing import Optional, Union

# Third party imports
import PySimpleGUI as sg                                            # pip install PySimpleGUI
from PySimpleGUI import WIN_CLOSED, WINDOW_CLOSE_ATTEMPTED_EVENT

# Local application imports
logger = logging.getLogger(__name__)
logger.debug(f"Import: OK <{__name__}>")

WIDTH, HEIGHT = sg.Window.get_screen_size()

class Panel(ABC):
    """
    Abstract Base Class (ABC) for Panel objects (i.e. GUI panels).
    ABC cannot be instantiated, and must be subclassed with abstract methods implemented before use.

    ### Constructor
    Args:
        `name` (str, optional): name of panel. Defaults to ''.
        `group` (Optional[str], optional): name of group. Defaults to None.
        `font_sizes` (tuple[int], optional): list of font sizes. Defaults to (14,12,10,8,6).
        `theme` (str, optional): name of theme. Defaults to 'LightGreen'.
        `typeface` (str, optional): name of typeface. Defaults to "Helvetica".
    
    ### Attributes
    #### Class
    - `font_sizes` (tuple[int]): list of font sizes
    - `theme` (str): name of theme
    - `typeface` (str): name of typeface
    #### Instance
    - `flags` (dict[str, bool]): keywords paired with boolean flags
    - `group` (str): name of group
    - `name` (str): name of panel
    - `tool` (Callable): tool to be controlled
    - `window` (sg.Window): Window object
    
    ### Methods
    #### Abstract
    - `getLayout`: build `sg.Column` object
    - `listenEvents`: listen to events and act on values
    #### Public
    - `arrangeElements`: arrange elements in a horizontal, vertical, or cross-shape pattern
    - `close`: exit the application
    - `configure`: configure GUI defaults
    - `getButtons`: get a list of panel buttons
    - `getInputs`: get the layout for the input section
    - `getWindow`: build `sg.Window` object
    - `pad`: add spacer in GUI
    - `parseInput`: parse inputs from GUI
    - `runGUI`: run the GUI loop
    - `setFlag`: set flags by using keyword arguments
    """
    
    font_sizes: tuple[int]
    theme: str
    typeface: str
    _default_flags: dict[str, bool] = {}
    def __init__(self, 
        name: str = '', 
        group: Optional[str] = None,
        font_sizes: tuple[int] = (14,12,10,8,6),
        theme: str = 'LightGreen', 
        typeface: str = "Helvetica"
    ):
        """
        Instantiate the class

        Args:
            name (str, optional): name of panel. Defaults to ''.
            group (Optional[str], optional): name of group. Defaults to None.
            font_sizes (tuple[int], optional): list of font sizes. Defaults to (14,12,10,8,6).
            theme (str, optional): name of theme. Defaults to 'LightGreen'.
            typeface (str, optional): name of typeface. Defaults to "Helvetica".
        """
        self.name = name
        self.group = group
        self.flags = self._default_flags.copy()
        self.tool = None
        self.window = None
        
        Panel.font_sizes = font_sizes
        Panel.theme = theme
        Panel.typeface = typeface
        
        self.configure()
        return
    
    def __del__(self):
        self.close()
    
    @abstractmethod
    def getLayout(self, title:str = 'Panel', title_font_level:int = 0, **kwargs) -> sg.Column:
        """
        Build `sg.Column` object

        Args:
            title (str, optional): title of layout. Defaults to 'Panel'.
            title_font_level (int, optional): index of font size from levels in `font_sizes`. Defaults to 0.

        Returns:
            sg.Column: Column object
        """
        font = (self.typeface, self.font_sizes[title_font_level]) if 'font' not in kwargs.keys() else kwargs.pop('font')
        layout = [[
            sg.Text(title, 
                    font=font,
                    **kwargs)
        ]]
        # Build Layout here
        layout = sg.Column(layout, vertical_alignment='top')
        return layout

    @abstractmethod
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
        # Listen to events here
        return updates

    @classmethod
    def arrangeElements(cls, elements:list, shape:tuple[int, int] = (0,0), form:str = '') -> list[list]:
        """
        Arrange elements in a horizontal, vertical, or cross-shape pattern

        Args:
            elements (list): list of GUI elements
            shape (tuple[int, int], optional): shape of grid. Defaults to (0,0).
            form (str, optional): shape of pattern. Defaults to ''.

        Raises:
            RuntimeError: Make sure grid size is able to fit the number of elements

        Returns:
            list[list]: list of lists of arranged GUI elements
        """
        arranged_elements = []
        if form in ['X', 'x', 'cross', '+']:
            h = elements[0]
            v = elements[1]
            if len(h) == 0:
                return cls.arrangeElements(v, form='V')
            if len(v) == 0:
                return cls.arrangeElements(h, form='H')
            h_keys = [b.Key for b in h]
            for ele in reversed(v):
                if ele.Key in h_keys:
                    arranged_elements.append([cls.pad()]+ h +[cls.pad()])
                else:
                    arranged_elements.append([cls.pad(), ele, cls.pad()])
        elif form in ['V', 'v', 'vertical', '|']:
            arranged_elements = [[cls.pad(), ele, cls.pad()] for ele in reversed(elements)]
        elif form in ['H', 'h', 'horizontal', '-', '_']:
            arranged_elements = [[cls.pad()]+ elements +[cls.pad()]]
        else: # arrange in grid
            rows, cols = shape
            num = len(elements)
            n = 0
            if not all(shape):
                if rows:
                    row = rows
                elif cols:
                    row = int(num/cols)
                else: # find the most compact arrangement 
                    root = 1
                    while True:
                        if root**2 > num:
                            break
                        root += 1
                    row = root
            elif rows*cols < num:
                raise RuntimeError('Make sure grid size is able to fit the number of elements.')
            else:
                row = rows
            while n < num:
                l,u = n, min(n+row, num)
                arranged_elements.append([cls.pad()]+ [elements[l:u]] +[cls.pad()])
                n += row
        return arranged_elements

    def close(self):
        """Exit the application"""
        try:
            self.window.close()
        except AttributeError:
            pass
        return

    @classmethod
    def configure(cls, **kwargs):
        """Configure GUI defaults"""
        cls.font_sizes = kwargs.pop('font_sizes', cls.font_sizes)
        cls.theme = kwargs.pop('theme', cls.theme)
        cls.typeface = kwargs.pop('typeface', cls.typeface)
        
        element_padding = kwargs.pop('element_padding', (0,0))
        font = kwargs.pop('font', (cls.typeface, cls.font_sizes[int(len(cls.font_sizes)/2)]))
        
        sg.theme(cls.theme)
        sg.set_options(font=font, element_padding=element_padding, **kwargs)
        return
    
    @staticmethod
    def getButtons(
        labels: list[str], 
        size: Union[int, tuple], 
        key_prefix: str, 
        font: tuple[str, int], 
        texts: Optional[list[str]] = None, 
        tooltips: Optional[list[str]] = None, 
        **kwargs
    ) -> list[sg.Button]:
        """
        Get list of panel buttons

        Args:
            labels (list[str]): list of button labels
            size (Union[int, tuple]): button width (,height)
            key_prefix (str): prefix of button key
            font (tuple[str, int]): (typeface, font size)
            texts (Optional[list[str]], optional): alternative text labels for buttons. Defaults to None.
            tooltips (Optional[list[str]], optional): tooltip labels for buttons. Defaults to None.
            
        Returns:
            list[sg.Button]: list of buttons
        """
        texts = [] if texts is None else texts
        tooltips = [] if tooltips is None else tooltips
        buttons = []
        specials = kwargs.pop('specials', {})
        for i,label in enumerate(labels):
            key_string = label.replace('\n','')
            key = f"-{key_prefix}-{key_string}-" if key_prefix else f"-{key_string}-"
            kw = kwargs.copy()
            if label in specials.keys():
                for k,v in specials[label].items():
                    kw[k] = v
            label = texts[i] if i<len(texts) else label
            tooltip = tooltips[i] if i<len(tooltips) else None
            buttons.append(sg.Button(label, size=size, key=key, font=font, tooltip=tooltip, **kw))
        return buttons
    
    @staticmethod
    def getInputs(
            fields: list[str], 
            key_prefix: str, 
            initial_visibility: bool = True, 
            label_map: Optional[dict] = None,
            defaults: Optional[dict] = None,
            tooltips: Optional[dict] = None,
            **kwargs
        ) -> list[sg.Column]:
        """
        Get the layout for the input section
        
        Args:
            fields (list[str]): list of field names
            key_prefix (str): prefix of button key
            initial_visibility (bool, optional): whether the field is initially visible. Defaults to True.
            label_map (Optional[dict], optional): text label for each field. Defaults to None.
            defaults (Optional[dict], optional): default value for each field. Defaults to None.
            tooltips (Optional[dict], optional): tooltip for each field. Defaults to None.

        Returns:
            list[sg.Column]: list of columns
        """
        # template for procedurally adding input fields
        labels = []
        inputs = []
        for input_field in fields:
            key_label = f'-{key_prefix}-{input_field.upper()}-LABEL-'
            key_input = f'-{key_prefix}-{input_field.upper()}-VALUE-'
            label = label_map.get(input_field, input_field.title()) if type(label_map) is dict else input_field.title()
            default = defaults.get(input_field, '') if type(defaults) is dict else ''
            tooltip = tooltips.get(input_field, None) if type(tooltips) is dict else None
            
            _label = sg.pin(
                sg.Column(
                    [[sg.Text(label, key=key_label, visible=True, tooltip=tooltip)]],
                    key=f'{key_label}BOX-', visible=initial_visibility
                )
            )
            _input = sg.pin(
                sg.Column(
                    [[sg.Input(default, size=(5,2), key=key_input, visible=True, tooltip=tooltip)]],
                    key=f'{key_input}BOX-', visible=initial_visibility
                )
            )
            labels.append([_label])
            inputs.append([_input])
        labels_column = sg.Column(labels, justification='right', pad=10, visible=True)
        inputs_column = sg.Column(inputs, justification='left', pad=10, visible=True)
        labels_inputs = [labels_column, inputs_column]
        return labels_inputs

    def getWindow(self, title:str = 'Application', **kwargs) -> sg.Window:
        """
        Build `sg.Window` object

        Args:
            title (str, optional): title of window. Defaults to 'Application'.

        Returns:
            sg.Window: Window object
        """
        layout = [[self.getLayout()]]
        window = sg.Window(title, layout, enable_close_attempted_event=True, resizable=False, finalize=True, icon='icon.ico', **kwargs)
        self.window = window
        return window

    @staticmethod
    def pad() -> Union[sg.Push, sg.Text]:
        """
        Add spacer in GUI

        Returns:
            Union[sg.Push, sg.Text]: GUI spacer
        """
        ele = sg.Text('', size=(1,1))
        try:
            ele = sg.Push()
        except Exception as e:
            print(e)
        return ele
    
    @classmethod
    def parseInput(cls, text:str) -> Union[list, bool, float, str, None]:
        """
        Parse inputs from GUI

        Args:
            text (str): input text read from GUI window

        Returns:
            Union[list, bool, float, str, None]: variable output including floats, strings, and tuples
        """
        text = text.strip()
        if len(text) == 0:
            return None
        
        array = []
        if ',' in text:
            array = text.split(',')
        elif ';' in text:
            array = text.split(';')
        if len(array):
            new_array = []
            for value in array:
                new_array.append(cls.parseInput(value))
            return new_array
        
        if text.replace('.','',1).replace('-','',1).isdigit():
            if '.' in text:
                return float(text)
            else:
                return int(text)
        
        if text.title() == "True":
            return True
        if text.title() == "False":
            return False
        
        if text[0] in ("'", '"') and text[-1] in ("'", '"'):
            return text[1:-1]
        return text
    
    def runGUI(self, title:str = 'Application', maximize:bool = False):
        """
        Run the GUI loop

        Args:
            title (str, optional): title of window. Defaults to 'Application'.
            maximize (bool, optional): whether to maximise window. Defaults to False.
        """
        self.configure()
        self.getWindow(title)
        self.window.Finalize()
        if maximize:
            self.window.Maximize()
        self.window.bring_to_front()
        try:
            self._loop_gui()
        finally:
            self.close()
        return
    
    def setFlag(self, **kwargs):
        """
        Set flags by using keyword arguments

        Kwargs:
            key, value: (flag name, boolean) pairs
        """
        if not all([type(v)==bool for v in kwargs.values()]):
            raise ValueError("Ensure all assigned flag values are boolean.")
        self.flags.update(kwargs)
        # for key, value in kwargs.items():
        #     self.flags[key] = value
        return

    # Protected method(s)
    def _loop_gui(self):
        """Loop GUI process"""
        if type(self.window) == type(None):
            return
        while True:
            event, values = self.window.read(timeout=30)
            if event in ('Ok', WIN_CLOSED, WINDOW_CLOSE_ATTEMPTED_EVENT, None):
                self.window.close()
                break
            updates = self.listenEvents(event, values)
            for ele_key, kwargs in updates.items():
                tooltip = kwargs.pop('tooltip', None)
                if tooltip is not None:
                    self.window[ele_key].set_tooltip(str(tooltip))
                self.window[ele_key].update(**kwargs)
        return
    
    def _mangle(self, text:str) -> str:
        """
        Mangle text with name of panel

        Args:
            text (str): text to be mangled

        Returns:
            str: mangled text
        """
        return f'-{self.name}{text}'
