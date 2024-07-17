# %% -*- coding: utf-8 -*-
"""
This module holds the base class for compound panels.

Classes:
    CompoundPanel (Panel)
"""
# Standard library imports
from __future__ import annotations
from collections import OrderedDict
import logging
from typing import Optional

# Third party imports
import PySimpleGUI as sg # pip install PySimpleGUI

# Local application imports
from .gui_utils import Panel

logger = logging.getLogger(__name__)
logger.debug(f"Import: OK <{__name__}>")

class CompoundPanel(Panel):
    """
    CompoundPanel provides methods to form a multi-tool control panel

    ### Constructor
    Args:
        `ensemble` (dict[str, Panel]): dictionary of individual sub-panels
        `name` (str, optional): name of panel. Defaults to ''.
        `group` (Optional[str], optional): name of group. Defaults to None.
    
    ### Attributes
    - `panels` (dict[str, Panel]): dictionary of individual sub-panels
    
    ### Methods
    - `close`: exit the application
    - `getLayout`: build `sg.Column` object
    - `listenEvents`: listen to events and act on values
    """
    
    def __init__(self, 
        ensemble: dict[str, Panel],
        name: str = '', 
        group: Optional[str] = None,
        **kwargs
    ):
        """
        Instantiate the class

        Args:
            ensemble (dict[str, Panel]): dictionary of individual sub-panels
            name (str, optional): name of panel. Defaults to ''.
            group (Optional[str], optional): name of group. Defaults to None.
        """
        super().__init__(name=name, group=group, **kwargs)
        self.panels = {key: value for key,value in ensemble.items()}
        return
    
    def close(self):
        """Exit the application"""
        for panel in self.panels.values():
            panel.close()
        return super().close()
    
    def getLayout(self, title:str = 'Control Panel', title_font_level:int = 0, **kwargs) -> sg.Column:
        """
        Build `sg.Column` object

        Args:
            title (str, optional): title of layout. Defaults to 'Control Panel'.
            title_font_level (int, optional): index of font size from levels in `font_sizes`. Defaults to 0.

        Returns:
            sg.Column: Column object
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
    
    def getWindow(self, title:str = 'Application', **kwargs) -> sg.Window:
        """
        Build `sg.Window` object

        Args:
            title (str, optional): title of window. Defaults to 'Application'.

        Returns:
            sg.Window: Window object
        """
        window = super().getWindow(title=title, **kwargs)
        for panel in self.panels.values():
            panel.window = window
        return window
    
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
        for panel in self.panels.values():
            update = panel.listenEvents(event, values)
            updates.update(update)
        return updates
