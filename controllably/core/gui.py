# -*- coding: utf-8 -*-
# Standard library imports
import tkinter as tk
from typing import Callable

class GUI:
    def __init__(self, principal: Callable):
        self.principal = principal
        self.object_id = ''
        self.widget = None
        return

    def bindWidget(self, widget: tk.Tk):
        self.widget = widget
        return
    
    def unbindWidget(self):
        self.widget = None
        return
    
    def close(self):
        assert isinstance(self.widget, tk.Tk), 'No widget is bound to this GUI'
        self.widget.quit()
        self.widget.destroy()
        return
    
    def updateValues(self):
        raise NotImplementedError
    
    def addTo(self, master: tk.Misc):
        raise NotImplementedError
