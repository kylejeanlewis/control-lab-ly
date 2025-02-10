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


class Proxy:
    def __new__(cls, prime:Callable, object_id:str|None = None):
        new_class = cls.factory(prime, object_id)
        return super(Proxy,cls).__new__(new_class)
    
    def __init__(self, prime:Callable, object_id:str|None = None):
        self.prime = prime
        self.object_id = object_id or id(prime)
        self.controller = None
        self.remote = False
        return
    
    @classmethod
    def factory(cls, prime:Callable, object_id:str|None = None):
        name = prime.__name__ if inspect.isclass(prime) else prime.__class__.__name__
        object_id = object_id or id(prime)
        attrs = {attr:cls.makeEmitter(getattr(prime,attr)) for attr in dir(prime) if callable(getattr(prime,attr)) and (attr not in dir(cls))}
        attrs.update({"_channel_class":prime})
        new_class = type(f"{name}_Proxy-{object_id}", (cls,), attrs)
        return new_class
    
    @staticmethod
    def makeEmitter(method):
        method_signature = inspect.signature(method)
        def emitter(self, *args, **kwargs):
            assert isinstance(self.controller, Controller), 'No controller is bound to this Proxy.'
            command = dict(
                object_id = self.object_id,
                method = method.__name__,
                args = args,
                kwargs = kwargs
            )
            if not self.remote and not inspect.isclass(self.prime):
                prime_method = getattr(self.prime, method.__name__)
                return prime_method(*args, **kwargs)
            return self.controller.transmitRequest(command)
        emitter.__name__ = method.__name__
        emitter.__doc__ = method.__doc__
        emitter.__signature__ = method_signature
        return emitter
    
    def bindController(self, controller: Controller):
        self.controller = controller
        return
    
    def unbindController(self):
        self.controller = None
        return
