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
import copy
import importlib
import inspect
import markdown
import os
from tkhtmlview import html_parser
from typing import Callable

# Third party imports
import PySimpleGUI as sg # pip install PySimpleGUI

# Local application imports
from ... import modules, Helper
from .gui_utils import Panel
print(f"Import: OK <{__name__}>")

DEFAULT_TEXT = "Select an item to view its documentation."
DEFAULT_METHOD = "< Methods >"
DEFAULT_REFERENCE = "< Import reference >"
HOME = "controllably"
MODULE_MAP = dict(
    factory = "Factory",
    helper = "Helper",
    image = "Image",
    layout = "Layout",
    pop_ups = "Popups",
    templates = "Templates",
)

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
    
    _default_flags = {'tree_expanded': False, 'shown_all': False}
    def __init__(self, name: str = 'Guide', **kwargs):
        """
        Instantiate the class

        Args:
            name (str, optional): name of panel. Defaults to 'Guide'.
        """
        super().__init__(name=name, **kwargs)
        self._stored_tree = None
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
        tree_data,_ = self._generate_tree(
            tree_data = tree_data,
            index = 1,
            parent_name = '', 
            modules_dictionary = modules._modules
        )
        selection = [
            [sg.Tree(
                data = tree_data,
                headings = ['type', 'index', 'doc'],
                visible_column_map = [True, True, False],
                num_rows = 20,
                row_height = round(self.font_sizes[2] / 0.6),
                col0_width = 30,
                key = "-TREE-",
                show_expanded = False,
                enable_events = True,
                expand_x = True,
                expand_y = True,
            )],
            [
                sg.Combo(
                    [DEFAULT_METHOD], DEFAULT_METHOD, 
                    key="-METHODS-", size=(40,1), enable_events=True, expand_y=True
                ),
                sg.Button("Show All", key="-TOGGLE-ALL-", size=(10,1), enable_events=True),
                sg.Button("Expand", key="-TOGGLE-REVEAL-", size=(10,1), enable_events=True)
            ]
        ]
        output = [
            [sg.Multiline(
                default_text=DEFAULT_TEXT, key="-MULTILINE-", size=(70,22), 
                disabled=True, write_only=True, expand_y=True
            )],
            [sg.Multiline(
                default_text=DEFAULT_REFERENCE, key="-INPUT-", size=(70,1),
                disabled=True, write_only=True, no_scrollbar=True, expand_y=True
            )]
        ]
        layout = [
            [layout],
            [
                sg.Column(selection, vertical_alignment='center'), 
                sg.Column(output, vertical_alignment='center', expand_y=True)
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
            doc = tree_data.tree_dict[fullname].values[2]
            object_type = tree_data.tree_dict[fullname].values[0]
            methods = [DEFAULT_METHOD]
            ref = DEFAULT_REFERENCE
            if object_type:
                obj: Callable = eval(f"modules.at{fullname}")
                ref = self._get_import_path(obj=obj)
                if object_type == 'class':
                    methods = [DEFAULT_METHOD] + Helper.get_method_names(obj)
                    methods = [m for m in methods if not m.startswith('_')] + [m for m in methods if m.startswith('_')]
            updates['-INPUT-'] = dict(value=ref)
            updates['-METHODS-'] = dict(values=methods, value=methods[0])
            html = self._convert_md_to_html(md_text=doc)
            self._render_html(html)
        
        # 2. Select method from Combo
        if event == '-METHODS-':
            if values['-METHODS-'] != DEFAULT_METHOD and len(values['-TREE-']):
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
        if event == '-TOGGLE-ALL-':
            self._import_all()
            tree: sg.Tree = self.window['-TREE-']
            tree_data = self._update_tree(tree.TreeData)
            shown_all = self.flags.get('shown_all', False)
            label = "Show All" if shown_all else "Show Current"
            updates['-TOGGLE-ALL-'] = dict(text=label)
            updates['-TREE-'] = dict(values=tree_data)
            updates['-METHODS-'] = dict(values=[DEFAULT_METHOD], value=DEFAULT_METHOD)
            updates['-TOGGLE-REVEAL-'] = dict(text='Expand')
            html = self._convert_md_to_html(md_text=DEFAULT_TEXT)
            self._render_html(html)
            self.setFlag(shown_all=(not shown_all), tree_expanded=False)
        
        # 4. Reveal button
        if event == '-TOGGLE-REVEAL-':
            tree: sg.Tree = self.window['-TREE-']
            tree_expanded = self.flags.get('tree_expanded', False)
            if tree_expanded:
                self._collapse_tree(tree)
                updates['-TOGGLE-REVEAL-'] = dict(text='Expand')
            else:
                self._expand_tree(tree)
                updates['-TOGGLE-REVEAL-'] = dict(text='Collapse')
            self.setFlag(tree_expanded=(not tree_expanded))
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
    
    def _generate_tree(self, 
        tree_data: sg.TreeData, 
        index: int, 
        parent_name: str, 
        modules_dictionary: dict
    ) -> tuple[sg.TreeData, int]:
        """
        Generate the tree data

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
            obj_type = ''
            if isinstance(v, dict):
                doc = v.get("_doc_", "< No documentation >")
                doc = doc if doc.strip() else "< No documentation >"
                tree_data.insert(parent_name, fullname, k, values=[obj_type, '', doc])
                tree_data, index = self._generate_tree(tree_data, index, fullname, v)
            elif isinstance(v, str):
                continue
            else:
                obj = eval(f"modules.at{fullname}")
                doc = inspect.getdoc(obj)
                obj_type = "function" if inspect.isfunction(obj) else obj_type
                obj_type = "class" if inspect.isclass(obj) else obj_type
                tree_data.insert(parent_name, fullname, k, values=[obj_type, index, doc])
                index += 1
        self.setFlag(tree_expanded=False)
        return tree_data, index
    
    def _get_import_path(self, obj: Callable) -> str:
        """
        Get the import path (dot notation) of the object

        Args:
            obj (Callable): object to be queried

        Returns:
            str: dot notation of the import path
        """
        mod = obj.__module__.split('.')
        if 'misc' in mod:
            mod.remove('misc')
        import_path = '.'.join(mod[:-1])
        last = mod.pop()
        if last in MODULE_MAP:
            ref = f"from {import_path} import {MODULE_MAP[last]}; {MODULE_MAP[last]}.{obj.__name__}"
        elif obj.__name__ == 'guide_me':
            ref = f"from {HOME} import {obj.__name__}"
        else:
            ref = f"from {import_path} import {obj.__name__}"
        return ref
    
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
    
    def _update_tree(self, current_tree:sg.TreeData) -> sg.TreeData:
        """
        Save current tree and return stored tree. Generates new tree if none is stored.

        Args:
            current_tree (sg.TreeData): tree data

        Returns:
            sg.TreeData: new tree data
        """
        if self._stored_tree is not None:
            new_tree = copy.deepcopy(self._stored_tree)
            self._stored_tree = None
        else:
            new_tree = sg.TreeData()
            new_tree,_ = self._generate_tree(
                tree_data = new_tree,
                index = 1,
                parent_name = '', 
                modules_dictionary = modules._modules
            )
        self._stored_tree = current_tree
        return new_tree
    
def guide_me():
    """Start guide to view documentation"""
    gui = Guide()
    gui.runGUI('Documentation')
    return
