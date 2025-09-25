# -*- coding: utf-8 -*-
""" 
This module contains the Panel class for creating GUI panels.

## Classes:
    `Panel`: Panel class for creating GUI panels.

<i>Documentation last updated: 2025-02-22</i>
"""
# Standard library imports
from __future__ import annotations
import logging
import tkinter as tk
from tkinter import ttk
import tkinter.messagebox as msgbox
from typing import Any, Callable, Iterable

# Local application imports
from ....core.control import Proxy

logger = logging.getLogger(__name__)

class Panel:
    """ 
    Panel class for creating GUI panels.
    
    ### Constructor:
        `principal` (Proxy|Any|None): The principal object to bind to the Panel.
        
    ### Attributes:
        `principal` (Proxy|Any|None): The principal object bound to the Panel.
        `object_id` (str): The ID of the principal object.
        `title` (str): The title of the Panel.
        `drawn` (bool): A flag indicating if the Panel is drawn.
        `top_level` (bool): A flag indicating if the Panel is a top-level window.
        `widget` (tk.Tk): The tkinter.Tk object bound to the Panel.
        `sub_panels` (dict[str, list[tuple[Panel, dict]]]): A dictionary of sub-panels.
        `stream_update_callbacks` (list[Callable]): A list of stream update callbacks.
        
    ### Methods:
        `bindObject`: Bind a principal object to the Panel.
        `releaseObject`: Release the principal object from the Panel.
        `bindWidget`: Bind a tkinter.Tk object to the Panel.
        `releaseWidget`: Release the tkinter.Tk object from the Panel.
        `show`: Show the Panel.
        `close`: Close the Panel.
        `getAttribute`: Get an attribute from the principal object.
        `getAttributes`: Get multiple attributes from the principal object.
        `execute`: Execute a method from the principal object.
        `addPack`: Add a Panel to the layout using the pack geometry manager.
        `addGrid`: Add a Panel to the layout using the grid geometry manager.
        `addPanel`: Add a Panel to the layout.
        `clearPanels`: Clear all the Panels from the layout.
        `updateStream`: Update the Panel continuously.
        `update`: Update the Panel values.
        `refresh`: Refresh the Panel layout.
        `addTo`: Add the Panel to a tkinter.Tk or tkinter.Frame object.
    """
    
    def __init__(self, principal: Proxy|Any|None = None):
        """ 
        Initialize a Panel object.
        
        Args:
            principal (Proxy|Any|None): The principal object to bind to the Panel.
        """
        self.principal = principal
        self.object_id = ''
        
        self.title = ''
        self.drawn = False
        self.top_level = True
        self.widget = None
        self.sub_panels: dict[str, list[tuple[Panel, dict]]] = dict()
        
        self.stream_update_callbacks: list[Callable] = []
        return
    
    def bindObject(self, principal: Proxy|Any):
        """ 
        Bind a principal object to the Panel.
        
        Args:
            principal (Proxy|Any): The principal object to bind to the Panel.
        """
        self.principal = principal
        self.update()
        return
    
    def releaseObject(self) -> Proxy|Any:
        """
        Release the principal object from the Panel.
        
        Returns:
            Proxy|Any: The principal object that was released.
        """
        principal = self.principal
        self.principal = None
        return principal

    def bindWidget(self, widget: tk.Tk):
        """
        Bind a tkinter.Tk object to the Panel.
        
        Args:
            widget (tk.Tk): The tkinter.Tk object to bind to the Panel.
        """
        assert isinstance(widget, tk.Tk), 'Widget must be a tkinter.Tk object'
        self.widget = widget
        return
    
    def releaseWidget(self) -> tk.Tk|None:
        """
        Release the tkinter.Tk object from the Panel.
        
        Returns:
            tk.Tk|None: The tkinter.Tk object that was released.
        """
        widget = self.widget if isinstance(self.widget, tk.Tk) else None
        self.widget = None
        self.drawn = False
        return widget
    
    def show(self, title:str = ''):
        """ 
        Show the Panel.
        
        Args:
            title (str): The title of the Panel.
        """
        self.title = title or (self.title or 'Application')
        if self.top_level:
            try:
                root = tk.Tk()
                root.protocol("WM_DELETE_WINDOW", self.close)
                self.addTo(root)
            except Exception as e:
                self.close()
                raise e
        
        if not isinstance(self.widget, tk.Tk):
            logger.warning('No widget is bound to this Panel')
            return
        
        try:
            self.update()
            self.widget.lift()
            self.widget.attributes('-topmost',True)
            self.widget.after_idle(self.widget.attributes,'-topmost',False)
            self.updateStream()
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
        """ Close the Panel. """
        if not isinstance(self.widget, tk.Tk):
            logger.warning('No widget is bound to this Panel')
            return
        self.widget.quit()
        self.widget.destroy()
        self.drawn = False
        return
    
    def getAttribute(self, attribute: str, default: Any|None = None) -> Any|None:
        """
        Get an attribute from the principal object.
        
        Args:
            attribute (str): The attribute to get.
            default (Any|None): The default value to return if the attribute is not found.
            
        Returns:
            Any|None: The value of the attribute or the default value.
        """
        return getattr(self.principal, attribute, default) if self.principal is not None else default
    
    def getAttributes(self, *attr_defaults: tuple[str, Any]) -> dict[str,Any]:
        """
        Get multiple attributes from the principal object.
        
        Args:
            *attr_defaults (tuple[str, Any]): The attributes to get and their default values.
            
        Returns:
            dict[str,Any]: A dictionary of the attributes and their values.
        """
        out = {attr: default for attr, default in attr_defaults}
        if self.principal is None:
            return out
        if not isinstance(self.principal, Proxy):
            return {attr: getattr(self.principal, attr, default) for attr, default in attr_defaults}
        
        # Proxy object
        assert self.principal.controller is not None, 'Principal object is not bound to a controller'
        assert self.principal.remote, 'Principal object is not in remote mode'
        command = dict(method='getattr', args=[self.principal.object_id, list(out.keys())])
        target = self.principal.controller.registry.get(self.principal.object_id, [])
        request_id = self.principal.controller.transmitRequest(command,target=target)
        data = self.principal.controller.retrieveData(request_id)
        out.update(data)
        return out
    
    def execute(self, method: Callable, *args, **kwargs) -> Any|None:
        """
        Execute a method from the principal object.
        
        Args:
            method (Callable): The method to execute.
            *args (tuple): The positional arguments to pass to the method.
            **kwargs (dict): The keyword arguments to pass to the method.
            
        Returns:
            Any|None: The output of the method or None if an error occurred.
        """
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
        """ 
        Add a Panel to the layout using the pack geometry manager.
        
        Args:
            panel (Panel): The Panel to add.
            **kwargs (dict): The keyword arguments to pass to the pack geometry manager.
        """
        return self.addPanel('pack', panel, **kwargs)
    
    def addGrid(self, panel: Panel, **kwargs):
        """
        Add a Panel to the layout using the grid geometry manager.
        
        Args:
            panel (Panel): The Panel to add.
            **kwargs (dict): The keyword arguments to pass to the grid
        """
        return self.addPanel('grid', panel, **kwargs)
    
    def addPanel(self, mode:str, panel:Panel, **kwargs):
        """
        Add a Panel to the layout.
        
        Args:
            mode (str): The geometry manager to use.
            panel (Panel): The Panel to add.
            **kwargs (dict): The keyword arguments to pass to the geometry manager.
        """
        assert isinstance(panel, Panel), 'Panel must be a Panel object'
        assert mode in ['pack','grid'], 'Mode must be either "pack" or "grid"'
        if mode not in self.sub_panels:
            if len(self.sub_panels):
                raise RuntimeError(f'Current geometry manager is already {list(self.sub_panels.keys())[0]}')
            self.sub_panels[mode] = []
        self.sub_panels[mode].append((panel,kwargs))
        return
    
    def clearPanels(self):
        """Clear all the Panels from the layout."""
        self.sub_panels.clear()
        return
    
    def updateStream(self, **kwargs):
        """Update the Panel continuously"""
        if isinstance(self.widget, tk.Tk):
            for callback in self.stream_update_callbacks:
                callback()
        return
    
    def update(self, **kwargs):
        """Update the Panel values"""
        # Update layout
        ...
        return
    
    def refresh(self, **kwargs):
        """Refresh the Panel layout"""
        # Refresh layout
        ...
        return
    
    def addTo(self, master: tk.Tk|tk.Frame, size: Iterable[int,int]|None = None) -> tuple[int,int]|None:
        """
        Add the Panel to a tkinter.Tk or tkinter.Frame object.
        
        Args:
            master (tk.Tk|tk.Frame): The tkinter.Tk or tkinter.Frame object to add the Panel to.
            size (Iterable[int,int]|None): The size of the Panel.
            
        Returns:
            tuple[int,int]|None: The size of the Panel or None if an error occurred.
        """
        # Add layout
        ...
        
        all_sizes = []
        for layout, panels in self.sub_panels.items():
            for panel, kwargs in panels:
                frame = ttk.Frame(master)
                sub_size = panel.addTo(frame)
                if isinstance(master, tk.Tk):
                    panel.bindWidget(master)
                    self.stream_update_callbacks.append(panel.updateStream)
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
