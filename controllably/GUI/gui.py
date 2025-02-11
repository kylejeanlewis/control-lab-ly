# -*- coding: utf-8 -*-
# Standard library imports
import tkinter as tk
from typing import Any

# Local application imports
from ..core.control import Proxy

class GUI:
    def __init__(self, principal: Proxy|Any|None = None):
        self.principal = principal
        self.object_id = ''
        self.widget = None
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
    
    def close(self):
        assert isinstance(self.widget, tk.Tk), 'No widget is bound to this GUI'
        self.widget.quit()
        self.widget.destroy()
        return
    
    def update(self, **kwargs):
        raise NotImplementedError
    
    def addTo(self, master: tk.Misc):
        raise NotImplementedError
