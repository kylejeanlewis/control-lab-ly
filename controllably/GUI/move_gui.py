# -*- coding: utf-8 -*-
# Standard library imports
import logging
import tkinter as tk
from tkinter import ttk
from typing import Protocol

# Local application imports
from ..core.position import Position
from ..core.control import Proxy
from .gui import GUI

logger = logging .getLogger(__name__)

class Move(Protocol):
    position: Position
    def move(self, axis:str, value:int|float):
        raise NotImplementedError
    
    def rotate(self, axis:str, value:int|float):
        raise NotImplementedError
    
    def home(self):
        raise NotImplementedError
    
    def moveToSafeHeight(self):
        raise NotImplementedError

class MoveGUI(GUI):
    def __init__(self, principal: Move|Proxy|None = None):
        super().__init__(principal)
        self.principal: Move|Proxy|None = principal
        self.title = "Robot Control D-Pad"
    
        # Initialize axis values
        self.x = 0
        self.y = 0
        self.z = 0
        self.a = 0  # Rotation around x-axis (roll)
        self.b = 0  # Rotation around y-axis (pitch)
        self.c = 0  # Rotation around z-axis (yaw)
        
        self.status = 'Disconnected'
        return
    
    def refresh(self, **kwargs):
        self.position_label.config(text=f"Position:\nx={self.x:}, y={self.y:}, z={self.z:}\na={self.c:}, b={self.b:}, c={self.a:}")
        self.status_label.config(text=self.status)
        return
    
    def update(self, **kwargs):
        # Position
        position = self.getPosition()
        if isinstance(position, Position):
            self.x, self.y, self.z = position.coordinates
            self.c, self.b, self.a = position.rotation
        
        # Status
        if not self.getConnected():
            self.status = 'Disconnected'
        elif self.getBusy():
            self.status = 'Busy'
        else:
            self.status = 'Connected'
        
        self.refresh()
        return
    
    def addTo(self, master: tk.Tk|tk.Frame, size: tuple[int,int]|None = None) -> tuple[int,int]|None:
        BUTTON_HEIGHT = 1
        BUTTON_WIDTH = 6
        
        # Add layout
        master.rowconfigure(1,weight=1, minsize=10*BUTTON_HEIGHT)
        master.columnconfigure(0,weight=1, minsize=9*BUTTON_WIDTH)
        
        # Create frames for organization
        status_frame = ttk.Frame(master)
        status_frame.grid(row=0, column=0, padx=10, pady=10, sticky='nsew')
        status_frame.columnconfigure(0,weight=1)
        
        control_frame = ttk.Frame(master)
        control_frame.grid(row=1, column=0, padx=10, pady=10, sticky='nsew')
        control_frame.grid_rowconfigure(1,weight=7, minsize=7*BUTTON_HEIGHT)
        control_frame.grid_rowconfigure([0,2],weight=1, minsize=BUTTON_HEIGHT)
        control_frame.grid_columnconfigure(1,weight=7, minsize=7*BUTTON_WIDTH)
        control_frame.grid_columnconfigure([0,2],weight=1, minsize=BUTTON_WIDTH)
        
        translation_xy_frame = ttk.Frame(control_frame)
        translation_xy_frame.grid(row=1, column=1, padx=10, pady=10, sticky='nsew')
        translation_xy_frame.grid_rowconfigure([0,1,2,3,4,5,6],weight=1, minsize=BUTTON_HEIGHT)
        translation_xy_frame.grid_columnconfigure([0,1,2,3,4,5,6],weight=1, minsize=BUTTON_WIDTH)
        translation_z_frame = ttk.Frame(control_frame)
        translation_z_frame.grid(row=1, column=2, padx=10, pady=10, sticky='nsew')
        translation_z_frame.grid_rowconfigure([0,1,2,3,4,5,6],weight=1, minsize=BUTTON_HEIGHT)
        translation_z_frame.grid_columnconfigure(0,weight=1, minsize=BUTTON_WIDTH)

        rotation_a_frame = ttk.Frame(control_frame)
        rotation_a_frame.grid(row=1, column=0, padx=10, pady=10, sticky='nsew')
        rotation_a_frame.grid_rowconfigure(1,weight=7, minsize=5*BUTTON_HEIGHT)
        rotation_a_frame.grid_rowconfigure([0,2],weight=1, minsize=BUTTON_HEIGHT)
        rotation_a_frame.grid_columnconfigure(0,weight=1, minsize=BUTTON_WIDTH)
        rotation_b_frame = ttk.Frame(control_frame)
        rotation_b_frame.grid(row=0, column=1, padx=10, pady=10, sticky='nsew')
        rotation_b_frame.grid_columnconfigure(1,weight=7, minsize=5*BUTTON_WIDTH)
        rotation_b_frame.grid_columnconfigure([0,2],weight=1, minsize=BUTTON_WIDTH)
        rotation_b_frame.grid_rowconfigure(0,weight=1, minsize=BUTTON_WIDTH)
        rotation_c_frame = ttk.Frame(control_frame)
        rotation_c_frame.grid(row=2, column=1, padx=10, pady=10, sticky='nsew')
        rotation_c_frame.grid_columnconfigure(1,weight=7, minsize=5*BUTTON_WIDTH)
        rotation_c_frame.grid_columnconfigure([0,2],weight=1, minsize=BUTTON_WIDTH)
        rotation_c_frame.grid_rowconfigure(0,weight=1, minsize=BUTTON_WIDTH)
        
        # Status Display
        self.close_button = ttk.Button(status_frame, text='Terminate', command=self.close)
        self.close_button.grid(row=0, column=1)
        self.position_label = ttk.Label(status_frame, text="Position: \nx=0, y=0, z=0\na=0, b=0, c=0")
        self.position_label.grid(row=0, column=0, padx=(0,10), rowspan=2)
        self.status_label = ttk.Label(status_frame, text="Connected")
        self.status_label.grid(row=1, column=1)

        # Translation Controls
        ttk.Button(translation_xy_frame, text="Home ", command=self.home, width=BUTTON_WIDTH).grid(row=3, column=3, sticky='nsew')
        ttk.Button(translation_z_frame, text="Safe ", command=self.safe, width=BUTTON_WIDTH).grid(row=3, column=0, sticky='nsew')
        
        ttk.Button(translation_xy_frame, text="X- 10", command=lambda: self.move(axis='x',value=-10), width=BUTTON_WIDTH).grid(row=3, column=0, sticky='nsew')
        ttk.Button(translation_xy_frame, text="X-  1", command=lambda: self.move(axis='x',value=-1), width=BUTTON_WIDTH).grid(row=3, column=1, sticky='nsew')
        ttk.Button(translation_xy_frame, text="X-0.1", command=lambda: self.move(axis='x',value=-0.1), width=BUTTON_WIDTH).grid(row=3, column=2, sticky='nsew')
        ttk.Button(translation_xy_frame, text="X+0.1", command=lambda: self.move(axis='x',value=0.1), width=BUTTON_WIDTH).grid(row=3, column=4, sticky='nsew')
        ttk.Button(translation_xy_frame, text="X+  1", command=lambda: self.move(axis='x',value=1), width=BUTTON_WIDTH).grid(row=3, column=5, sticky='nsew')
        ttk.Button(translation_xy_frame, text="X+ 10", command=lambda: self.move(axis='x',value=10), width=BUTTON_WIDTH).grid(row=3, column=6, sticky='nsew')
        
        ttk.Button(translation_xy_frame, text="Y+ 10", command=lambda: self.move(axis='y',value=10), width=BUTTON_WIDTH).grid(row=0, column=3, sticky='nsew')
        ttk.Button(translation_xy_frame, text="Y+  1", command=lambda: self.move(axis='y',value=1), width=BUTTON_WIDTH).grid(row=1, column=3, sticky='nsew')
        ttk.Button(translation_xy_frame, text="Y+0.1", command=lambda: self.move(axis='y',value=0.1), width=BUTTON_WIDTH).grid(row=2, column=3, sticky='nsew')
        ttk.Button(translation_xy_frame, text="Y-0.1", command=lambda: self.move(axis='y',value=-0.1), width=BUTTON_WIDTH).grid(row=4, column=3, sticky='nsew')
        ttk.Button(translation_xy_frame, text="Y-  1", command=lambda: self.move(axis='y',value=-1), width=BUTTON_WIDTH).grid(row=5, column=3, sticky='nsew')
        ttk.Button(translation_xy_frame, text="Y- 10", command=lambda: self.move(axis='y',value=-10), width=BUTTON_WIDTH).grid(row=6, column=3, sticky='nsew')
        
        ttk.Button(translation_z_frame, text="Z+ 10", command=lambda: self.move(axis='z',value=10), width=BUTTON_WIDTH).grid(row=0, column=0, sticky='nsew')
        ttk.Button(translation_z_frame, text="Z+  1", command=lambda: self.move(axis='z',value=1), width=BUTTON_WIDTH).grid(row=1, column=0, sticky='nsew')
        ttk.Button(translation_z_frame, text="Z+0.1", command=lambda: self.move(axis='z',value=0.1), width=BUTTON_WIDTH).grid(row=2, column=0, sticky='nsew')
        ttk.Button(translation_z_frame, text="Z-0.1", command=lambda: self.move(axis='z',value=-0.1), width=BUTTON_WIDTH).grid(row=4, column=0, sticky='nsew')
        ttk.Button(translation_z_frame, text="Z-  1", command=lambda: self.move(axis='z',value=-1), width=BUTTON_WIDTH).grid(row=5, column=0, sticky='nsew')
        ttk.Button(translation_z_frame, text="Z- 10", command=lambda: self.move(axis='z',value=-10), width=BUTTON_WIDTH).grid(row=6, column=0, sticky='nsew')

        # Rotation Controls
        ttk.Scale(rotation_a_frame, from_=-180, to=180, orient=tk.VERTICAL, length=BUTTON_HEIGHT*5).grid(row=1, column=0, sticky='nsew')
        ttk.Scale(rotation_b_frame, from_=-180, to=180, orient=tk.HORIZONTAL, length=BUTTON_WIDTH*5).grid(row=0, column=1, sticky='nsew')
        ttk.Scale(rotation_c_frame, from_=-180, to=180, orient=tk.HORIZONTAL, length=BUTTON_WIDTH*5).grid(row=0, column=1, sticky='nsew')
        
        ttk.Button(rotation_a_frame, text="A+", command=lambda: self.rotate(axis='a',value=1), width=BUTTON_WIDTH).grid(row=0, column=0, sticky='nsew')
        ttk.Button(rotation_a_frame, text="A-", command=lambda: self.rotate(axis='a',value=-1), width=BUTTON_WIDTH).grid(row=2, column=0, sticky='nsew')
        ttk.Button(rotation_b_frame, text="B-", command=lambda: self.rotate(axis='b',value=-1), width=BUTTON_WIDTH).grid(row=0, column=0, sticky='nsew')
        ttk.Button(rotation_b_frame, text="B+", command=lambda: self.rotate(axis='b',value=1), width=BUTTON_WIDTH).grid(row=0, column=2, sticky='nsew')
        ttk.Button(rotation_c_frame, text="C-", command=lambda: self.rotate(axis='c',value=-1), width=BUTTON_WIDTH).grid(row=0, column=0, sticky='nsew')
        ttk.Button(rotation_c_frame, text="C+", command=lambda: self.rotate(axis='c',value=1), width=BUTTON_WIDTH).grid(row=0, column=2, sticky='nsew')
        
        size = (9*BUTTON_WIDTH,11*BUTTON_HEIGHT)
        return super().addTo(master, size)

    def move(self, axis:str, value:int|float):
        assert axis in 'xyz', 'Provide one of x,y,z axis'
        setattr(self, axis, round(getattr(self, axis) + value,2))
        try:
            out = self.principal.move(axis,value)
            if isinstance(out, Exception):
                logger.warning(out)
        except AttributeError as e:
            pass
        except NotImplementedError as e:
            logger.warning(e)
            self.update()
        self.refresh()
        return

    def rotate(self, axis:str, value:int|float):
        assert axis in 'abc', 'Provide one of a,b,c axis'
        setattr(self, axis, round(getattr(self, axis) + value,2))
        try:
            out = self.principal.rotate(axis,value)
            if isinstance(out, Exception):
                logger.warning(out)
        except AttributeError as e:
            pass
        except NotImplementedError as e:
            logger.warning(e)
            self.update()
        self.refresh()
        return 
    
    def home(self):
        try:
            out = self.principal.home()
            if isinstance(out, Exception):
                logger.warning(out)
        except AttributeError as e:
           pass
        except NotImplementedError as e:
            logger.warning(e)
            self.update()
        self.update()
        return
    
    def safe(self):
        try:
            out = self.principal.moveToSafeHeight()
            if isinstance(out, Exception):
                logger.warning(out)
        except AttributeError as e:
            pass
        except NotImplementedError as e:
            logger.warning(e)
            self.update()
        self.update()
        return

    def getPosition(self) -> Position|None:
        attr_name = 'position'
        if isinstance(self.principal, Proxy):
            return self.principal.getAttr(attr_name)
        return getattr(self.principal, attr_name, None)

    def getBusy(self) -> bool:
        attr_name = 'is_busy'
        if isinstance(self.principal, Proxy):
            return self.principal.getAttr(attr_name, False)
        return getattr(self.principal, attr_name, False)
    
    def getConnected(self) -> bool:
        attr_name = 'is_connected'
        if isinstance(self.principal, Proxy):
            return self.principal.getAttr(attr_name, False)
        return getattr(self.principal, attr_name, False)
    