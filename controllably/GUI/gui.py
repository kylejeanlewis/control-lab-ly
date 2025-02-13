# -*- coding: utf-8 -*-
# Standard library imports
from __future__ import annotations
import logging
import tkinter as tk
from tkinter import ttk
from typing import Any, Callable, Iterable

# Local application imports
from ..core.control import Proxy

logger = logging.getLogger(__name__)

class GUI:
    def __init__(self, principal: Proxy|Any|None = None):
        self.principal = principal
        self.object_id = ''
        
        self.title = ''
        self.top_level = True
        self.widget = None
        self.sub_panels = dict()
        return
    
    def bindObject(self, principal: Proxy|Any):
        self.principal = principal
        return
    
    def releaseObject(self) -> Proxy|Any:
        principal = self.principal
        self.principal = None
        return principal

    def bindWidget(self, widget: tk.Tk):
        assert isinstance(widget, tk.Tk), 'Widget must be a tkinter.Tk object'
        self.widget = widget
        return
    
    def releaseWidget(self) -> tk.Tk:
        assert isinstance(self.widget, tk.Tk), 'No widget is bound to this GUI'
        widget = self.widget
        self.widget = None
        return widget
    
    def show(self, title:str = ''):
        self.title = title or (self.title or 'Application')
        if self.top_level:
            self.addTo(tk.Tk())
        if not isinstance(self.widget, tk.Tk):
            logger.warning('No widget is bound to this GUI')
            return
        self.update()
        try:
            self.widget.mainloop()
        except Exception as e:
            logger.warning(e)
            self.close()
        finally:
            self.releaseWidget()
            for panels in self.sub_panels.values():
                for panel, _ in panels:
                    panel.releaseWidget()
        return
    
    def close(self):
        if not isinstance(self.widget, tk.Tk):
            logger.warning('No widget is bound to this GUI')
            return
        self.widget.quit()
        self.widget.destroy()
        self.widget = None
        return
    
    def getAttribute(self, attribute: str, default: Any|None = None) -> Any|None:
        return getattr(self.principal, attribute, default) if self.principal is not None else default
    
    def execute(self, func: Callable, *args, **kwargs) -> Any|None:
        assert callable(func), 'Method must be a callable object'
        try:
            out = func(*args, **kwargs)
            if isinstance(out, Exception):
                logger.warning(out)
                return
        except AttributeError as e:
            return
        except NotImplementedError as e:
            logger.warning(e)
            self.update()
            return
        return out
    
    def refresh(self, **kwargs):
        # Refresh layout
        ...
        return
    
    def update(self, **kwargs):
        # Update layout
        ...
        return
    
    def addPack(self, panel: GUI, **kwargs):
        return self.addPanel('pack', panel, **kwargs)
    
    def addGrid(self, panel: GUI, **kwargs):
        return self.addPanel('grid', panel, **kwargs)
    
    def addPanel(self, mode:str, panel:GUI, **kwargs):
        assert isinstance(panel, GUI), 'Panel must be a GUI object'
        assert mode in ['pack','grid'], 'Mode must be either "pack" or "grid"'
        if mode not in self.sub_panels:
            if len(self.sub_panels):
                raise RuntimeError(f'Current geometry manager is already {list(self.sub_panels.keys())[0]}')
            self.sub_panels[mode] = []
        self.sub_panels[mode].append((panel,kwargs))
        return
    
    def clearPanels(self):
        self.sub_panels.clear()
        return
    
    def addTo(self, master: tk.Tk|tk.Frame, size: Iterable[int,int]|None = None) -> tuple[int,int]|None:
        # Add layout
        ...
        
        all_sizes = []
        for layout, panels in self.sub_panels.items():
            for panel, kwargs in panels:
                frame = ttk.Frame(master)
                sub_size = panel.addTo(frame)
                if isinstance(master, tk.Tk):
                    panel.bindWidget(master)
                all_sizes.append(sub_size)
                if layout == 'pack':
                    frame.pack(**kwargs)
                elif layout == 'grid':
                    frame.grid(**kwargs)
        
        if isinstance(master, tk.Tk):
            self.top_level = True
            self.bindWidget(master)
            master.title(self.title)
            if isinstance(size, Iterable) and len(size) == 2:
                master.minsize(*size)
        return size
 