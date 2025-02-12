# -*- coding: utf-8 -*-
# Standard library imports
import threading
import tkinter as tk
from typing import Any

# Local application imports
from ..core.control import Proxy

class GUI:
    def __init__(self, principal: Proxy|Any|None = None):
        self.principal = principal
        self.object_id = ''
        
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
    
    def show(self):
        if self.top_level:
            self.addTo(tk.Tk())
        assert isinstance(self.widget, tk.Tk), 'No widget is bound to this GUI'
        self.update()
        self.widget.mainloop()
        return
    
    def close(self):
        assert isinstance(self.widget, tk.Tk), 'No widget is bound to this GUI'
        self.widget.quit()
        self.widget.destroy()
        return
    
    def refresh(self, **kwargs):
        raise NotImplementedError
    
    def update(self, **kwargs):
        raise NotImplementedError
    
    def addTo(self, master: tk.Misc):
        self.top_level = isinstance(master, tk.Tk)
        if self.top_level:
            self.bindWidget(master)
        
        # Add layout
        ...
        return
