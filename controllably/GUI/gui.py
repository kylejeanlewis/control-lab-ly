# -*- coding: utf-8 -*-
# Standard library imports
from __future__ import annotations
import logging
import tkinter as tk
from tkinter import ttk
import tkinter.messagebox as msgbox
from typing import Any, Callable, Iterable

# Local application imports
from ..core.control import Proxy

logger = logging.getLogger(__name__)

class Panel:
    def __init__(self, principal: Proxy|Any|None = None):
        self.principal = principal
        self.object_id = ''
        
        self.title = ''
        self.drawn = False
        self.top_level = True
        self.widget = None
        self.sub_panels = dict()
        return
    
    def bindObject(self, principal: Proxy|Any):
        self.principal = principal
        self.update()
        return
    
    def releaseObject(self) -> Proxy|Any:
        principal = self.principal
        self.principal = None
        return principal

    def bindWidget(self, widget: tk.Tk):
        assert isinstance(widget, tk.Tk), 'Widget must be a tkinter.Tk object'
        self.widget = widget
        return
    
    def releaseWidget(self) -> tk.Tk|None:
        widget = self.widget if isinstance(self.widget, tk.Tk) else None
        self.widget = None
        return widget
    
    def show(self, title:str = ''):
        self.title = title or (self.title or 'Application')
        if self.top_level:
            root = tk.Tk()
            root.protocol("WM_DELETE_WINDOW", self.close)
            self.addTo(root)
        if not isinstance(self.widget, tk.Tk):
            logger.warning('No widget is bound to this Panel')
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
            logger.warning('No widget is bound to this Panel')
            return
        self.widget.quit()
        self.widget.destroy()
        return
    
    def getAttribute(self, attribute: str, default: Any|None = None) -> Any|None:
        return getattr(self.principal, attribute, default) if self.principal is not None else default
    
    def execute(self, method: Callable, *args, **kwargs) -> Any|None:
        assert callable(method), 'Method must be a callable object'
        try:
            out = method(*args, **kwargs)
            if isinstance(out, Exception):
                logger.warning(out)
                return
        except NotImplementedError:
            out = NotImplementedError(f'Not implemented:\n`{method.__name__}` from\n{method.__self__.__class__}')
        except Exception as e:
            out = e
        if isinstance(out, Exception):
            logger.warning(out)
            msgbox.showerror('Execution error', str(out))
            self.update()
            return
        return out
    
    def addPack(self, panel: Panel, **kwargs):
        return self.addPanel('pack', panel, **kwargs)
    
    def addGrid(self, panel: Panel, **kwargs):
        return self.addPanel('grid', panel, **kwargs)
    
    def addPanel(self, mode:str, panel:Panel, **kwargs):
        assert isinstance(panel, Panel), 'Panel must be a Panel object'
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
    
    def update(self, **kwargs):
        # Update layout
        ...
        return
    
    def refresh(self, **kwargs):
        # Refresh layout
        ...
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
        self.drawn = True
        self.update()
        return size
 