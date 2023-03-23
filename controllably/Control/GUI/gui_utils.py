# %% -*- coding: utf-8 -*-
"""
Created: Tue 2022/11/30 10:30:00
@author: Chang Jie

Notes / actionables:
- 
"""
# Standard library imports
from __future__ import annotations
from abc import ABC, abstractmethod
from collections import OrderedDict
from typing import Optional, Union

# Third party imports
import PySimpleGUI as sg # pip install PySimpleGUI
from PySimpleGUI import WIN_CLOSED, WINDOW_CLOSE_ATTEMPTED_EVENT

# Local application imports
print(f"Import: OK <{__name__}>")

WIDTH, HEIGHT = sg.Window.get_screen_size()
THEME = 'LightGreen'
TYPEFACE = "Helvetica"
FONT_SIZES = (14,12,10,8,6)

class Panel(ABC):
    font_sizes: list[int]
    theme: str
    typeface: str
    _default_flags: dict[str, bool] = {}
    def __init__(self, 
        name: str = '', 
        group: Optional[str] = None,
        font_sizes: list[int] = list(FONT_SIZES),
        theme: str = THEME, 
        typeface: str = TYPEFACE
    ):
        """
        Panel class

        Args:
            name (str, optional): name of panel. Defaults to ''.
            theme (str, optional): name of theme. Defaults to THEME.
            typeface (str, optional): name of typeface. Defaults to TYPEFACE.
            font_sizes (list, optional): list of font sizes. Defaults to FONT_SIZES.
            group (str, optional): name of group. Defaults to None.
        """
        self.name = name
        self.group = group
        self.flags = {}
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
        Get layout object

        Args:
            title (str, optional): title of layout. Defaults to 'Panel'.
            title_font_level (int, optional): index of font size from levels in font_sizes. Defaults to 0.

        Returns:
            PySimpleGUI.Column: Column object
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
            values (dict): dictionary of values from window

        Returns:
            dict: dictionary of updates
        """
        updates = {}
        # Listen to events here
        return updates

    @staticmethod
    def getButtons(
        labels: list[str], 
        size: Union[int, tuple], 
        key_prefix: str, 
        font: tuple[str, int], 
        texts: list[str] = [], 
        **kwargs
    ) -> list[sg.Button]:
        """
        Get list of panel buttons

        Args:
            labels (list): list of button labels
            size (int, or tuple): button width (,height)
            key_prefix (any): prefix of button key
            font (tuple): (typeface, font size)
            texts (list, optional): alternative text labels for buttons. Defaults to [].

        Returns:
            list: list of PySimpleGUI.Button objects
        """
        buttons = []
        specials = kwargs.pop('specials', {})
        for i,label in enumerate(labels):
            key_string = label.replace('\n','')
            key = f"-{key_prefix}-{key_string}-" if key_prefix else f"-{key_string}-"
            kw = kwargs.copy()
            if label in specials.keys():
                for k,v in specials[label].items():
                    kw[k] = v
            if len(texts):
                try:
                    label = texts[i]
                except IndexError:
                    pass
            buttons.append(sg.Button(label, size=size, key=key, font=font, **kw))
        return buttons
    
    @staticmethod
    def pad():
        """
        Spacer / padding

        Returns:
            PySimpleGUI.Push: padding
        """
        ele = sg.Text('', size=(1,1))
        try:
            ele = sg.Push()
        except Exception as e:
            print(e)
        return ele
    
    @staticmethod
    def parseInput(string:str) -> list[Union[float, str]]:
        """
        Parse inputs from GUI

        Args:
            string (str): input string read from GUI window

        Returns:
            any: appropriate values
        """
        if ',' in string:
            strings = string.split(',')
        elif ';' in string:
            strings = string.split(';')
        else:
            try:
                string = float(string)
                return string
            finally:
                # return string
                pass
        output = []
        for string in strings:
            try:
                output.append(float(string))
            except ValueError:
                # output.append(string)
                pass
        return output
    
    @classmethod
    def arrangeElements(cls, elements:list, shape:tuple[int, int] = (0,0), form:str = '') -> list[list]:
        """
        Arrange elements in a horizontal / vertical / cross-shape pattern

        Args:
            elements (list): list of GUI elements
            shape (tuple, optional): shape of grid. Defaults to (0,0).
            form (str, optional): shape of pattern. Defaults to ''.

        Raises:
            Exception: Grid size must be large enough to accommodate all elements

        Returns:
            list: list of arranged GUI elements
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
                raise Exception('Make sure grid size is able to fit the number of elements.')
            else:
                row = rows
            while n < num:
                l,u = n, min(n+row, num)
                arranged_elements.append([cls.pad()]+ [elements[l:u]] +[cls.pad()])
                n += row
        return arranged_elements
    
    @classmethod
    def configure(cls, **kwargs):
        """
        Configure defaults
        """
        cls.font_sizes = kwargs.pop('font_sizes', cls.font_sizes)
        cls.theme = kwargs.pop('theme', cls.theme)
        cls.typeface = kwargs.pop('typeface', cls.typeface)
        
        element_padding = kwargs.pop('element_padding', (0,0))
        font = kwargs.pop('font', (cls.typeface, cls.font_sizes[int(len(cls.font_sizes)/2)]))
        
        sg.theme(cls.theme)
        sg.set_options(font=font, element_padding=element_padding, **kwargs)
        return
    
    def close(self):
        """
        Close window
        """
        try:
            self.window.close()
        except AttributeError:
            pass
        return

    def getWindow(self, title:str = 'Application', **kwargs) -> sg.Window:
        """
        Get window object

        Args:
            title (str, optional): title of window. Defaults to 'Application'.

        Returns:
            PySimpleGUI.Window: Window object
        """
        layout = [[self.getLayout()]]
        window = sg.Window(title, layout, enable_close_attempted_event=True, resizable=False, finalize=True, icon='icon.ico', **kwargs)
        self.window = window
        return window
    
    def runGUI(self, title='Application', maximize=False):
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
        Set a flag's truth value

        Args:
            `name` (str): label
            `value` (bool): flag value
        """
        if not all([type(v)==bool for v in kwargs.values()]):
            raise ValueError("Ensure all assigned flag values are boolean.")
        for key, value in kwargs.items():
            self.flags[key] = value
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
    
    def _mangle(self, string:str):
        """
        Mangle string with name of panel

        Args:
            string (str): string to be mangled

        Returns:
            str: mangled string
        """
        return f'-{self.name}{string}'
    

class CompoundPanel(Panel):
    """
    Compound Panel class

    Args:
        ensemble (dict, optional): dictionary of individual sub-panels. Defaults to {}.
        theme (str, optional): name of theme. Defaults to THEME.
        typeface (str, optional): name of typeface. Defaults to TYPEFACE.
        font_sizes (list, optional): list of font sizes. Defaults to FONT_SIZES.
        group (str, optional): name of group. Defaults to None.
    """
    def __init__(self, 
        ensemble: dict[str, Panel],
        group: Optional[str] = None,
        **kwargs
    ):
        super().__init__(group=group, **kwargs)
        self.panels = {key: value for key,value in ensemble.items()}
        return
    
    def close(self):
        """
        Close window
        """
        for panel in self.panels.values():
            panel.close()
        return super().close()
    
    def getLayout(self, title:str = 'Control Panel', title_font_level:int = 0, **kwargs) -> sg.Column:
        """
        Get layout object

        Args:
            title (str, optional): title of layout. Defaults to 'Panel'.
            title_font_level (int, optional): index of font size from levels in font_sizes. Defaults to 0.

        Returns:
            PySimpleGUI.Column: Column object
        """
        font = (self.typeface, self.font_sizes[title_font_level], 'bold')
        layout = super().getLayout(title, justification='center', font=font)
        
        tab_groups = {'main': []}
        for key, panel in self.panels.items():
            group = panel.group
            _layout = panel.getLayout(title_font_level=title_font_level+1)
            if not group:
                group = 'main'
            if group not in tab_groups.keys():
                tab_groups[group] = []
            tab_groups[group].append((key, _layout))
            
        tab_group_order = ['main', 'viewer', 'mover', 'measurer'] 
        tab_group_order = tab_group_order + [grp for grp in list(tab_groups.keys()) if grp not in tab_group_order]
        ordered_tab_groups = OrderedDict()
        for key in tab_group_order:
            if key not in tab_groups:
                continue
            ordered_tab_groups[key] = tab_groups.get(key)
        tab_groups = ordered_tab_groups
        
        panels = []
        excluded = ['main']
        for group, _layouts in tab_groups.items():
            if group == 'main':
                panels = panels + [_layout for _,_layout in _layouts]
                continue
            if len(_layouts) == 1:
                panels.append(_layouts[0][1])
                excluded.append(group)
            else:
                tabs = [sg.Tab(key, [[_layout]], expand_x=True) for key,_layout in tab_groups[group]]
                tab_group = sg.TabGroup([tabs], tab_location='bottomright', key=f'-{group}-TABS-', 
                                        expand_x=True, expand_y=True)
                tab_groups[group] = tab_group
                panels.append(tab_group)
        # panels = panels + [element for group,element in tab_groups.items() if group not in excluded]
        panel_list = [panels[0]]
        for p in range(1, len(panels)):
            panel_list.append(sg.VerticalSeparator(color="#ffffff", pad=5))
            panel_list.append(panels[p])
        
        suite = sg.Column([panel_list], vertical_alignment='top')
        layout = [
            [layout],
            [suite]
        ]
        layout = sg.Column(layout, vertical_alignment='top')
        return layout
    
    def listenEvents(self, event:str, values:dict[str, str]) -> dict[str, dict]:
        """
        Listen to events and act on values

        Args:
            event (str): event triggered
            values (dict): dictionary of values from window

        Returns:
            dict: dictionary of updates
        """
        updates = {}
        for panel in self.panels.values():
            update = panel.listenEvents(event, values)
            updates.update(update)
        return updates


def configure(**kwargs):
    return Panel.configure(**kwargs)
