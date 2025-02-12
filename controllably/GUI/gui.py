# -*- coding: utf-8 -*-
# Standard library imports
import logging
import threading
import tkinter as tk
from tkinter import ttk
from typing import Any

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
        self.widget_thread: threading.Thread|None = None
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
        self.widget_thread = threading.Thread(target=self.widget.mainloop, daemon=True)
        return
    
    def releaseWidget(self) -> tk.Tk:
        assert isinstance(self.widget, tk.Tk), 'No widget is bound to this GUI'
        widget = self.widget
        self.widget = None
        self.widget_thread = None
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
        return
    
    def close(self):
        if not isinstance(self.widget, tk.Tk):
            logger.warning('No widget is bound to this GUI')
            return
        self.widget.quit()
        self.widget.destroy()
        return
    
    def refresh(self, **kwargs):
        raise NotImplementedError
    
    def update(self, **kwargs):
        raise NotImplementedError
    
    def addTo(self, master: tk.Tk|tk.Frame, size: tuple[int,int]|None = None) -> tuple[int,int]|None:
        # Add layout
        ...
        
        if isinstance(master, tk.Tk):
            self.top_level = True
            self.bindWidget(master)
            master.title(self.title)
            master.minsize(*size)
        return size
