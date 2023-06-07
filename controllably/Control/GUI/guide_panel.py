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

# Third party imports
import PySimpleGUI as sg # pip install PySimpleGUI

# Local application imports
from ... import modules, Helper
from .gui_utils import Panel
print(f"Import: OK <{__name__}>")

DEFAULT_TEXT = "Select an item to view its documentation."
HOME = "controllably"
PLACEHOLDER_METHOD = "< Methods >"

class Guide(Panel):
    """
    Guide Panel class

    ### Constructor
    Args:
        `name` (str, optional): name of panel. Defaults to 'Guide'.

    ### Methods
    - `getLayout`: build `sg.Column` object
    - `listenEvents`: listen to events and act on values
    """
    
    _default_flags = {'revealed': False}
    def __init__(self, name: str = 'Guide', **kwargs):
        """
        Instantiate the class

        Args:
            name (str, optional): name of panel. Defaults to 'Guide'.
        """
        super().__init__(name=name, **kwargs)
        return
    
    def getLayout(self, title_font_level: int = 0, **kwargs) -> sg.Column:
        """
        Build `sg.Column` object

        Args:
            title (str, optional): title of layout. Defaults to 'Panel'.
            title_font_level (int, optional): index of font size from levels in font_sizes. Defaults to 0.

        Returns:
            sg.Column: Column object
        """
        font = (self.typeface, self.font_sizes[title_font_level])
        layout = super().getLayout('Guide', justification='center', font=font, **kwargs)
        tree_data = sg.TreeData()
        tree_data,_ = self._update_tree(
            tree_data = tree_data,
            index = 1,
            parent_name = '', 
            modules_dictionary = modules._modules
        )
        selection = [
            [sg.Tree(
                data = tree_data,
                headings = ['index', 'doc'],
                visible_column_map = [True, False],
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
                [PLACEHOLDER_METHOD], PLACEHOLDER_METHOD, key="-METHODS-", size=(40,1), enable_events=True
                ),
                sg.Button("Show All", key="-GET-ALL-", size=(10,1), enable_events=True),
                sg.Button("Expand", key="-TOGGLE-REVEAL-", size=(10,1), enable_events=True)
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
        """
        Listen to events and act on values

        Args:
            event (str): event triggered
            values (dict[str, str]): dictionary of values from window

        Returns:
            dict: dictionary of updates
        """
        updates = {}
        # 1. Select object from Tree
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
            html = self._convert_md_to_html(md_text=doc)
            self._render_html(html)
        
        # 2. Select method from Combo
        if event == '-METHODS-':
            if values['-METHODS-'] != PLACEHOLDER_METHOD and len(values['-TREE-']):
                fullname = values['-TREE-'][0]
                tree: sg.Tree = self.window['-TREE-']
                tree_data: sg.TreeData = tree.TreeData
                method = eval(f"modules.at{fullname}.{values['-METHODS-']}")
                doc = inspect.getdoc(method)
                html = self._convert_md_to_html(md_text=doc)
                self._render_html(html)
            elif len(values['-TREE-']):
                pass
            else:
                html = self._convert_md_to_html(md_text=DEFAULT_TEXT)
                self._render_html(html)
        
        # 3. Show all button
        if event == '-GET-ALL-':
            self._import_all()
            tree_data = sg.TreeData()
            tree_data,_ = self._update_tree(
                tree_data = tree_data,
                index = 1,
                parent_name = '', 
                modules_dictionary = modules._modules
            )
            updates['-TREE-'] = dict(values=tree_data)
            updates['-METHODS-'] = dict(values=[PLACEHOLDER_METHOD], value=PLACEHOLDER_METHOD)
            updates['-TOGGLE-REVEAL-'] = dict(text='Expand')
            html = self._convert_md_to_html(md_text=DEFAULT_TEXT)
            self._render_html(html)
        
        # 4. Reveal button
        if event == '-TOGGLE-REVEAL-':
            tree: sg.Tree = self.window['-TREE-']
            revealed = self.flags.get('revealed', False)
            if revealed:
                self._collapse_tree(tree)
                updates['-TOGGLE-REVEAL-'] = dict(text='Expand')
            else:
                self._expand_tree(tree)
                updates['-TOGGLE-REVEAL-'] = dict(text='Collapse')
            self.setFlag(revealed = (not revealed))
        return updates
    
    # Protected methods
    def _collapse_tree(self, tree: sg.Tree):
        """
        Fully collapse the tree view

        Args:
            tree (sg.Tree): tree to be collapse
        """
        for key in tree.TreeData.tree_dict:
            tree_node_id = tree.KeyToID[key] if key in tree.KeyToID else None
            tree.Widget.item(tree_node_id, open=False)
        return
    
    def _convert_md_to_html(self, md_text:str) -> str:
        """
        Convert the Markdown to HTML

        Args:
            md_text (str): Markdown string to be converted

        Returns:
            str: HTML string
        """
        sub_headers = (
            "Args", 
            "Classes", 
            "Functions", 
            "Kwargs",
            "Modules",
            "Other constants and variables",
            "Other types",
            "Raises", 
            "Returns",
        )
        lines = md_text.split('\n')
        lines = [l.replace('   ','- ') for l in lines]# if l.strip()]
        
        md_text = "\n".join(lines)
        md_text = md_text.replace('<', '&lt;')
        md_text = md_text.replace('>', '&gt;')
        md_text = md_text.replace('`', '*')
        md_text = md_text.replace('Parameters:', 'Parameters')
        for header in sub_headers:
            md_text = md_text.replace(f'{header}:', f'**{header}**\n')
        
        h3,h4,p = self.font_sizes[0:3]
        html = markdown.markdown(md_text)
        html = html.replace('<h3>', f'<h3 style="font-size: {h3}px;">')
        html = html.replace('<h4>', f'<h4 style="font-size: {h4}px;">')
        html = html.replace('<p>', f'<p style="font-size: {p}px;">')
        html = html.replace('<ul>', f'<ul style="font-size: {p}px;">')
        return html
    
    def _expand_tree(self, tree: sg.Tree):
        """
        Fully expand the tree view

        Args:
            tree (sg.Tree): tree to be expanded
        """
        for key in tree.TreeData.tree_dict:
            tree_node_id = tree.KeyToID[key] if key in tree.KeyToID else None
            tree.Widget.item(tree_node_id, open=True)
        return
    
    def _import_all(self):
        """
        Import all the modules in the package
        """
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
    
    def _render_html(self, html:str):
        """
        Render the HTML string in the widget

        Args:
            html (str): HTML string to be rendered
        """
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
        """
        Update the tree data

        Args:
            tree_data (sg.TreeData): tree data
            index (int): object index
            parent_name (str): name of parent node
            modules_dictionary (dict): modules dictionary

        Returns:
            tuple[sg.TreeData, int]: tree data; next index
        """
        search_order = sorted(modules_dictionary.items())
        search_order = [p for p in search_order if not isinstance(p[1], dict)] + [p for p in search_order if isinstance(p[1], dict)]
        for k, v in search_order:
            fullname = '.'.join([parent_name, k])
            if isinstance(v, dict):
                doc = v.get("_doc_", "< No documentation >")
                doc = doc if doc.strip() else "< No documentation >"
                tree_data.insert(parent_name, fullname, k, values=['',doc])
                tree_data, index = self._update_tree(tree_data, index, fullname, v)
            elif isinstance(v, str):
                continue
            else:
                obj = eval(f"modules.at{fullname}")
                doc = inspect.getdoc(obj)
                tree_data.insert(parent_name, fullname, k, values=[index,doc])
                index += 1
        self.setFlag(revealed=False)
        return tree_data, index
    
def guide_me():
    """Start guide to view documentation"""
    gui = Guide()
    gui.runGUI()
    return
