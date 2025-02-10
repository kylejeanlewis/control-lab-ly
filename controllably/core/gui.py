# -*- coding: utf-8 -*-
# Standard library imports
import inspect
import tkinter as tk
from typing import Callable

# Local imports
from controllably.core.control import Controller

class GUI:
    def __init__(self, principal: Callable):
        self.principal = principal
        self.object_id = ''
        self.widget = None
        return
    
    # def bindObject(self, object_id: str):
    #     self.object_id = object_id
    #     return
    
    # def unbindObject(self):
    #     self.object_id = ''
    #     return
    
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

    def sendCommand(self, command: dict):
        # assert len(self.object_id), 'No tool is bound to this GUI'
        # request = dict(object_id=self.object_id)
        # request.update(command)
        # self.controller.transmitRequest(request)
        return
    
    def updateValues(self):
        raise NotImplementedError
    
    def addTo(self, master: tk.Misc):
        raise NotImplementedError
