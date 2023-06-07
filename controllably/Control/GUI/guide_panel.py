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
import os
from tkhtmlview import html_parser
from typing import Optional, Protocol

# Third party imports
import PySimpleGUI as sg # pip install PySimpleGUI

# Local application imports
from ... import modules, Helper
from .gui_utils import Panel
print(f"Import: OK <{__name__}>")

HOME = "controllably"
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
        tree_data,_ = self._update_tree(
            tree_data = tree_data,
            index = 0,
            parent_name = '', 
            modules_dictionary = modules._modules
        )
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
            [
                sg.Combo(
                ['<Methods>'], '<Methods>', key="-METHODS-", size=(45,1), enable_events=True
                ),
                sg.Button("Show All", key="-GET-ALL-", size=(15,1), enable_events=True)
            ]
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
            self._update_html(doc)
            # updates['-MULTILINE-'] = dict(value=doc)
                
        if event == '-METHODS-' and values['-METHODS-'] != PLACEHOLDER_METHOD:
            fullname = values.get('-TREE-', [''])[0]
            tree: sg.Tree = self.window['-TREE-']
            tree_data: sg.TreeData = tree.TreeData
            method = eval(f"modules.at{fullname}.{values['-METHODS-']}")
            doc = inspect.getdoc(method)
            self._update_html(doc)
            # updates['-MULTILINE-'] = dict(value=doc)
        
        if event == '-GET-ALL-':
            self._import_all()
            tree_data = sg.TreeData()
            tree_data,_ = self._update_tree(
                tree_data = tree_data,
                index = 0,
                parent_name = '', 
                modules_dictionary = modules._modules
            )
            updates['-TREE-'] = dict(values=tree_data)
        return updates
    
    # Protected methods
    def _get_html(self, md_text:str) -> str:
        sub_headers = (
            "Args", 
            "Classes", 
            "Functions", 
            "Modules",
            "Other constants and variables",
            "Other types",
            "Raises", 
            "Returns",
        )
        lines = md_text.split('\n')
        lines = [l.replace('   ','- ') for l in lines]
        
        md_text = "\n".join(lines)
        md_text = md_text.replace('`', '*')
        md_text = md_text.replace('Parameters:', 'Parameters')
        for header in sub_headers:
            md_text = md_text.replace(f'{header}:', f'**{header}**\n')
        
        html = markdown.markdown(md_text)
        html = html.replace('<p>', '<p style="font-size: 12px;">')
        html = html.replace('<ul>', '<ul style="font-size: 12px;">')
        return html
    
    def _import_all(self):
        root_dir = __file__.split(HOME)[0] + HOME
        for root, _, files in os.walk(root_dir):
            if "__init__.py" in files and "templates" not in root:
                files.remove("__init__.py")
                if any([f for f in files if f.endswith(".py")]):
                    dot_notation = root.replace(root_dir,HOME).replace("\\",".")
                    try:
                        importlib.import_module(dot_notation)
                    except (ModuleNotFoundError, ImportError):
                        print(f"Unable to import {dot_notation}")
        return
    
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
    
    def _update_tree(self, 
        tree_data: sg.TreeData, 
        index: int, 
        parent_name: str, 
        modules_dictionary: dict
    ) -> tuple[sg.TreeData, int]:
        for k, v in list(modules_dictionary.items()):
            fullname = '.'.join([parent_name, k])
            if isinstance(v, dict):
                doc = v.get("_doc_", "<No documentation>")
                tree_data.insert(parent_name, fullname, k, values=['',doc])
                tree_data, index = self._update_tree(tree_data, index, fullname, v)
            elif isinstance(v, str):
                continue
            else:
                obj = eval(f"modules.at{fullname}")
                doc = inspect.getdoc(obj)
                tree_data.insert(parent_name, fullname, k, values=[index,doc])
                index += 1
        return tree_data, index
    
def guide_me():
    """Start guide"""
    gui = Guide()
    gui.runGUI()
    return
