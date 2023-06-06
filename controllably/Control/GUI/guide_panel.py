# %% -*- coding: utf-8 -*-
"""
This module holds the class for guide control panels.

Classes:
    Guide (Panel)

Functions:
    guide_me
"""
# Standard library imports
from __future__ import annotations
import importlib
import inspect
import markdown
from tkhtmlview import html_parser
from typing import Optional, Protocol

# Third party imports
import PySimpleGUI as sg # pip install PySimpleGUI

# Local application imports
from ... import modules, Helper
from ...misc import Factory
from .gui_utils import Panel
print(f"Import: OK <{__name__}>")

ICON_CLASS = ''
ICON_FUNCTION = ''
ICON_MODULE = ''
PLACEHOLDER_METHOD = "<Methods>"

class Guide(Panel):
    def __init__(self, name: str = 'Guide', **kwargs):
        super().__init__(name=name, **kwargs)
        return
    
    def getLayout(self, title_font_level: int = 0, **kwargs) -> sg.Column:
        font = (self.typeface, self.font_sizes[title_font_level])
        layout = super().getLayout('Guide', justification='center', font=font, **kwargs)
        tree_data = sg.TreeData()
        index = 0
        
        def add_objects_in_modules(parent_name, d):
            nonlocal index, tree_data
            for k, v in list(d.items()):
                fullname = '.'.join([parent_name, k])
                doc = "<No documentation>"
                if isinstance(v, dict):
                    for root in Factory.HOME_PACKAGES:
                        try:
                            mod = importlib.import_module(name=f'{root}{fullname}')
                        except ModuleNotFoundError:
                            pass
                        else:
                            doc = inspect.getdoc(mod)
                            doc = doc if doc is not None else "<No documentation>"
                            break
                    tree_data.insert(parent_name, fullname, k, values=['',doc])
                    add_objects_in_modules(fullname, v)
                else:
                    obj = eval(f"modules.at{fullname}")
                    doc = inspect.getdoc(obj)
                    tree_data.insert(parent_name, fullname, k, values=[index,doc])
                    index += 1
                    
        add_objects_in_modules('', modules._modules)
        selection = [
            [sg.Tree(
                data = tree_data,
                headings = ['index', ],
                num_rows = 20,
                col0_width = 30,
                key = "-TREE-",
                show_expanded = False,
                enable_events = True,
                expand_x = True,
                expand_y = True,
            )],
            [sg.Combo(
                ['<Methods>'], '<Methods>', key="-METHODS-", size=(60,1), enable_events=True
            )]
        ]
        layout = [
            [layout],
            [
                sg.Column(selection, vertical_alignment='top'), 
                sg.Multiline(key="-MULTILINE-", size=(60,22), disabled=True)
            ]
        ]
        layout = sg.Column(layout, vertical_alignment='top')
        return layout
    
    def listenEvents(self, event: str, values: dict[str, str]) -> dict[str, str]:
        updates = {}
        if event == '-TREE-':
            fullname = values.get('-TREE-', [''])[0]
            tree: sg.Tree = self.window['-TREE-']
            tree_data: sg.TreeData = tree.TreeData
            doc = tree_data.tree_dict[fullname].values[1]
            if tree_data.tree_dict[fullname].values[0]:
                obj = eval(f"modules.at{fullname}")
                methods = [PLACEHOLDER_METHOD] + Helper.get_method_names(obj)
                methods = [m for m in methods if not m.startswith('_')] + [m for m in methods if m.startswith('_')]
                updates['-METHODS-'] = dict(values=methods, value=methods[0])
            else:
                updates['-METHODS-'] = dict(values=[PLACEHOLDER_METHOD], value=PLACEHOLDER_METHOD)
            # updates['-MULTILINE-'] = dict(value=doc)
            self._update_html(doc)
                
        if event == '-METHODS-' and values['-METHODS-'] != PLACEHOLDER_METHOD:
            fullname = values.get('-TREE-', [''])[0]
            tree: sg.Tree = self.window['-TREE-']
            tree_data: sg.TreeData = tree.TreeData
            method = eval(f"modules.at{fullname}.{values['-METHODS-']}")
            doc = inspect.getdoc(method)
            # updates['-MULTILINE-'] = dict(value=doc)
            self._update_html(doc)
        return updates
    
    # Protected methods
    def _update_html(self, md_text:str):
        html = self._get_html(md_text=md_text)
        html_widget = self.window['-MULTILINE-'].Widget
        parser = html_parser.HTMLTextParser()
        def set_html(widget, html, strip=True):
            nonlocal parser
            prev_state = widget.cget('state')
            widget.config(state=sg.tk.NORMAL)
            widget.delete('1.0', sg.tk.END)
            widget.tag_delete(widget.tag_names)
            parser.w_set_html(widget, html, strip=strip)
            widget.config(state=prev_state)
        
        set_html(html_widget, html)
        return
    
    def _get_html(self, md_text:str) -> str:
        md_text = md_text.replace('`', '*')
        md_text = md_text.replace('\n    ', '\n- ')
        md_text = md_text.replace('Args:', '**Args:**')
        md_text = md_text.replace('Returns:', '**Returns:**')
        md_text = md_text.replace('Raises:', '**Raises:**')
        print(md_text)
        html = markdown.markdown(md_text)
        html = html.replace('<p>', '<p style="font-size: 12px;">')
        html = html.replace('<ul>', '<ul style="font-size: 12px;">')
        html = html.replace('\n', '<br>')
        print(html)
        return html
    
def guide_me():
    """Start guide"""
    gui = Guide()
    gui.runGUI()
    return
