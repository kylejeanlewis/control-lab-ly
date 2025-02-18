# -*- coding: utf-8 -*-
# Standard library imports
import logging
import tkinter as tk
from tkinter import ttk
from typing import Protocol

# Local application imports
from ..core.position import Position
from ..core.control import Proxy
from .gui import Panel

logger = logging .getLogger(__name__)

PRECISION = 1
TICK_INTERVAL = 90

BUTTON_HEIGHT = 1
BUTTON_WIDTH = 6

class Move(Protocol):
    position: Position
    def move(self, axis:str, by:int|float, **kwargs):
        raise NotImplementedError
    
    def safeMoveTo(self, to, **kwargs):
        raise NotImplementedError
    
    def rotate(self, axis:str, by:int|float, **kwargs):
        raise NotImplementedError
    
    def rotateTo(self, to, **kwargs):
        raise NotImplementedError
    
    def home(self):
        raise NotImplementedError
    
    def moveToSafeHeight(self):
        raise NotImplementedError

class MovePanel(Panel):
    def __init__(self, principal: Move|Proxy|None = None):
        super().__init__(principal)
        self.principal: Move|Proxy|None = principal
        self.title = "Robot Control D-Pad"
        self.status = 'Disconnected'
    
        # Initialize axis values
        self.x = 0.0
        self.y = 0.0
        self.z = 0.0
        self.a = 0.0  # Rotation around x-axis (roll)
        self.b = 0.0  # Rotation around y-axis (pitch)
        self.c = 0.0  # Rotation around z-axis (yaw)
        
        # Settings
        self.button_height = BUTTON_HEIGHT
        self.button_width = BUTTON_WIDTH
        self.precision = PRECISION
        self.tick_interval = TICK_INTERVAL
        return
    
    def update(self, **kwargs):
        attributes = self.getAttributes(
            ('is_connected', False), 
            ('is_busy', False), 
            ('position', None)
        )
        # Status
        if not attributes['is_connected']:
            self.status = 'Disconnected'
        elif attributes['is_busy']:
            self.status = 'Busy'
        else:
            self.status = 'Connected'
            
        # Position
        position = attributes['position']
        if isinstance(position, Position):
            self.x, self.y, self.z = position.coordinates.round(self.precision)
            self.c, self.b, self.a = position.rotation.round(self.precision)
        return self.refresh()
    
    def refresh(self, **kwargs):
        if not self.drawn:
            return
        
        # Update labels
        self.label_position.config(text=f"Position:\nx={self.x}, y={self.y}, z={self.z}\na={self.a}, b={self.b}, c={self.c}")
        self.label_status.config(text=self.status)
        
        # Update scales
        self.scale_a.set(self.a)
        self.scale_b.set(self.b)
        self.scale_c.set(self.c)
        
        # Update entries
        self.entry_x.delete(0, tk.END)
        self.entry_x.insert(0, str(self.x))
        self.entry_y.delete(0, tk.END)
        self.entry_y.insert(0, str(self.y))
        self.entry_z.delete(0, tk.END)
        self.entry_z.insert(0, str(self.z))
        self.entry_a.delete(0, tk.END)
        self.entry_a.insert(0, str(self.a))
        self.entry_b.delete(0, tk.END)
        self.entry_b.insert(0, str(self.b))
        self.entry_c.delete(0, tk.END)
        self.entry_c.insert(0, str(self.c))
        return
    
    def addTo(self, master: tk.Tk|tk.Frame, size: tuple[int,int]|None = None) -> tuple[int,int]|None:
        # Add layout
        master.rowconfigure(1,weight=1, minsize=10*self.button_height)
        master.columnconfigure(0,weight=1, minsize=9*self.button_width)
        
        # Add keyboard events
        master.bind('<Up>', lambda event: self.move(axis='y', value=0.1))
        master.bind('<Down>', lambda event: self.move(axis='y', value=-0.1))
        master.bind('<Left>', lambda event: self.move(axis='x', value=-0.1))
        master.bind('<Right>', lambda event: self.move(axis='x', value=0.1))
        master.bind('<Shift-Up>', lambda event: self.move(axis='z', value=0.1))
        master.bind('<Shift-Down>', lambda event: self.move(axis='z', value=-0.1))
        
        master.bind(',', lambda event: self.rotate(axis='c', value=-1))
        master.bind('.', lambda event: self.rotate(axis='c', value=1))
        master.bind(';', lambda event: self.rotate(axis='b', value=-1))
        master.bind("'", lambda event: self.rotate(axis='b', value=1))
        master.bind('[', lambda event: self.rotate(axis='a', value=-1))
        master.bind(']', lambda event: self.rotate(axis='a', value=1))
        
        # Create frames for organization
        status_frame = ttk.Frame(master)
        status_frame.grid(row=0, column=0, padx=10, pady=10, sticky='nsew')
        status_frame.columnconfigure(0,weight=1)
        
        control_frame = ttk.Frame(master)
        control_frame.grid(row=1, column=0, padx=10, pady=10, sticky='nsew')
        control_frame.grid_rowconfigure(1,weight=7, minsize=7*self.button_height)
        control_frame.grid_rowconfigure([0,2,3],weight=1, minsize=self.button_height)
        control_frame.grid_columnconfigure(1,weight=7, minsize=7*self.button_width)
        control_frame.grid_columnconfigure([0,2],weight=1, minsize=self.button_width)
        
        translation_xy_frame = ttk.Frame(control_frame)
        translation_xy_frame.grid(row=1, column=1, padx=10, pady=10, sticky='nsew')
        translation_xy_frame.grid_rowconfigure([0,1,2,3,4,5,6],weight=1, minsize=self.button_height)
        translation_xy_frame.grid_columnconfigure([0,1,2,3,4,5,6],weight=1, minsize=self.button_width)
        
        translation_z_frame = ttk.Frame(control_frame)
        translation_z_frame.grid(row=1, column=2, padx=10, pady=10, sticky='nsew')
        translation_z_frame.grid_rowconfigure([0,1,2,3,4,5,6],weight=1, minsize=self.button_height)
        translation_z_frame.grid_columnconfigure(0,weight=1, minsize=self.button_width)

        rotation_a_frame = ttk.Frame(control_frame)
        rotation_a_frame.grid(row=1, column=0, padx=10, pady=10, sticky='nsew')
        rotation_a_frame.grid_rowconfigure(1,weight=7, minsize=5*self.button_height)
        rotation_a_frame.grid_rowconfigure([0,2],weight=1, minsize=self.button_height)
        rotation_a_frame.grid_columnconfigure(0,weight=1, minsize=self.button_width)
        
        rotation_b_frame = ttk.Frame(control_frame)
        rotation_b_frame.grid(row=0, column=1, padx=10, pady=10, sticky='nsew')
        rotation_b_frame.grid_columnconfigure(1,weight=7, minsize=5*self.button_width)
        rotation_b_frame.grid_columnconfigure([0,2],weight=1, minsize=self.button_width)
        rotation_b_frame.grid_rowconfigure(0,weight=1, minsize=self.button_width)
        
        rotation_c_frame = ttk.Frame(control_frame)
        rotation_c_frame.grid(row=2, column=1, padx=10, pady=10, sticky='nsew')
        rotation_c_frame.grid_columnconfigure(1,weight=7, minsize=5*self.button_width)
        rotation_c_frame.grid_columnconfigure([0,2],weight=1, minsize=self.button_width)
        rotation_c_frame.grid_rowconfigure(0,weight=1, minsize=self.button_width)
        
        entry_frame = ttk.Frame(control_frame)
        entry_frame.grid(row=3, column=1, padx=10, pady=10, sticky='nsew')
        entry_frame.grid_columnconfigure([0,1,2,3],weight=1, minsize=self.button_width)
        entry_frame.grid_rowconfigure([0,1],weight=1, minsize=self.button_width)
        
        # Status Display
        self.label_position = ttk.Label(status_frame, text="Position: \nx=0, y=0, z=0\na=0, b=0, c=0")
        self.button_refresh = ttk.Button(status_frame, text='Refresh', command=self.update)
        self.label_status = ttk.Label(status_frame, text="Disconnected")
        self.label_position.grid(row=0, column=0, padx=(0,10), rowspan=2)
        self.button_refresh.grid(row=0, column=1)
        self.label_status.grid(row=1, column=1)

        # Translation Controls
        ttk.Button(translation_xy_frame, text="Home", command=self.home, width=self.button_width).grid(row=3, column=3, sticky='nsew')
        ttk.Button(translation_z_frame, text="Safe", command=self.safe, width=self.button_width).grid(row=3, column=0, sticky='nsew')
        
        ttk.Button(translation_xy_frame, text="X- 10", command=lambda: self.move(axis='x',value=-10), width=self.button_width).grid(row=3, column=0, sticky='nsew')
        ttk.Button(translation_xy_frame, text="X-  1", command=lambda: self.move(axis='x',value=-1), width=self.button_width).grid(row=3, column=1, sticky='nsew')
        ttk.Button(translation_xy_frame, text="X-0.1", command=lambda: self.move(axis='x',value=-0.1), width=self.button_width).grid(row=3, column=2, sticky='nsew')
        ttk.Button(translation_xy_frame, text="X+0.1", command=lambda: self.move(axis='x',value=0.1), width=self.button_width).grid(row=3, column=4, sticky='nsew')
        ttk.Button(translation_xy_frame, text="X+  1", command=lambda: self.move(axis='x',value=1), width=self.button_width).grid(row=3, column=5, sticky='nsew')
        ttk.Button(translation_xy_frame, text="X+ 10", command=lambda: self.move(axis='x',value=10), width=self.button_width).grid(row=3, column=6, sticky='nsew')
        
        ttk.Button(translation_xy_frame, text="Y+ 10", command=lambda: self.move(axis='y',value=10), width=self.button_width).grid(row=0, column=3, sticky='nsew')
        ttk.Button(translation_xy_frame, text="Y+  1", command=lambda: self.move(axis='y',value=1), width=self.button_width).grid(row=1, column=3, sticky='nsew')
        ttk.Button(translation_xy_frame, text="Y+0.1", command=lambda: self.move(axis='y',value=0.1), width=self.button_width).grid(row=2, column=3, sticky='nsew')
        ttk.Button(translation_xy_frame, text="Y-0.1", command=lambda: self.move(axis='y',value=-0.1), width=self.button_width).grid(row=4, column=3, sticky='nsew')
        ttk.Button(translation_xy_frame, text="Y-  1", command=lambda: self.move(axis='y',value=-1), width=self.button_width).grid(row=5, column=3, sticky='nsew')
        ttk.Button(translation_xy_frame, text="Y- 10", command=lambda: self.move(axis='y',value=-10), width=self.button_width).grid(row=6, column=3, sticky='nsew')
        
        ttk.Button(translation_z_frame, text="Z+ 10", command=lambda: self.move(axis='z',value=10), width=self.button_width).grid(row=0, column=0, sticky='nsew')
        ttk.Button(translation_z_frame, text="Z+  1", command=lambda: self.move(axis='z',value=1), width=self.button_width).grid(row=1, column=0, sticky='nsew')
        ttk.Button(translation_z_frame, text="Z+0.1", command=lambda: self.move(axis='z',value=0.1), width=self.button_width).grid(row=2, column=0, sticky='nsew')
        ttk.Button(translation_z_frame, text="Z-0.1", command=lambda: self.move(axis='z',value=-0.1), width=self.button_width).grid(row=4, column=0, sticky='nsew')
        ttk.Button(translation_z_frame, text="Z-  1", command=lambda: self.move(axis='z',value=-1), width=self.button_width).grid(row=5, column=0, sticky='nsew')
        ttk.Button(translation_z_frame, text="Z- 10", command=lambda: self.move(axis='z',value=-10), width=self.button_width).grid(row=6, column=0, sticky='nsew')

        # Rotation Controls
        ttk.Button(rotation_a_frame, text="A+", command=lambda: self.rotate(axis='a',value=1), width=self.button_width).grid(row=0, column=0, sticky='nsew')
        ttk.Button(rotation_a_frame, text="A-", command=lambda: self.rotate(axis='a',value=-1), width=self.button_width).grid(row=2, column=0, sticky='nsew')
        ttk.Button(rotation_b_frame, text="B-", command=lambda: self.rotate(axis='b',value=-1), width=self.button_width).grid(row=0, column=0, sticky='nsew')
        ttk.Button(rotation_b_frame, text="B+", command=lambda: self.rotate(axis='b',value=1), width=self.button_width).grid(row=0, column=2, sticky='nsew')
        ttk.Button(rotation_c_frame, text="C-", command=lambda: self.rotate(axis='c',value=-1), width=self.button_width).grid(row=0, column=0, sticky='nsew')
        ttk.Button(rotation_c_frame, text="C+", command=lambda: self.rotate(axis='c',value=1), width=self.button_width).grid(row=0, column=2, sticky='nsew')
        
        self.scale_a = tk.Scale(rotation_a_frame, from_=180, to=-180, orient=tk.VERTICAL, length=self.button_height*5, tickinterval=self.tick_interval)
        self.scale_b = tk.Scale(rotation_b_frame, from_=-180, to=180, orient=tk.HORIZONTAL, length=self.button_width*5, tickinterval=self.tick_interval)
        self.scale_c = tk.Scale(rotation_c_frame, from_=-180, to=180, orient=tk.HORIZONTAL, length=self.button_width*5, tickinterval=self.tick_interval)
        self.scale_a.bind("<ButtonRelease-1>", lambda event: self.rotateTo(a=self.scale_a.get()))
        self.scale_b.bind("<ButtonRelease-1>", lambda event: self.rotateTo(b=self.scale_b.get()))
        self.scale_c.bind("<ButtonRelease-1>", lambda event: self.rotateTo(c=self.scale_c.get()))
        self.scale_a.grid(row=1, column=0, sticky='nsew')
        self.scale_b.grid(row=0, column=1, sticky='nsew')
        self.scale_c.grid(row=0, column=1, sticky='nsew')
        
        # Input fields
        self.entry_x = ttk.Entry(entry_frame, width=self.button_width, justify=tk.CENTER)
        self.entry_y = ttk.Entry(entry_frame, width=self.button_width, justify=tk.CENTER)
        self.entry_z = ttk.Entry(entry_frame, width=self.button_width, justify=tk.CENTER)
        self.entry_a = ttk.Entry(entry_frame, width=self.button_width, justify=tk.CENTER)
        self.entry_b = ttk.Entry(entry_frame, width=self.button_width, justify=tk.CENTER)
        self.entry_c = ttk.Entry(entry_frame, width=self.button_width, justify=tk.CENTER)
        self.entry_x.grid(row=0, column=0, sticky='nsew')
        self.entry_y.grid(row=0, column=1, sticky='nsew')
        self.entry_z.grid(row=0, column=2, sticky='nsew')
        self.entry_a.grid(row=1, column=0, sticky='nsew')
        self.entry_b.grid(row=1, column=1, sticky='nsew')
        self.entry_c.grid(row=1, column=2, sticky='nsew')
        
        ttk.Button(
            entry_frame, text="Go", 
            command=lambda: self.moveTo(
                x=self.entry_x.get(), 
                y=self.entry_y.get(), 
                z=self.entry_z.get(), 
                a=self.entry_a.get(), 
                b=self.entry_b.get(), 
                c=self.entry_c.get()
            ),
            width=self.button_width
        ).grid(row=0, column=3, sticky='nsew')
        ttk.Button(entry_frame, text="Clear", command=self.refresh, width=self.button_width).grid(row=1, column=3, sticky='nsew')
        
        return super().addTo(master, (9*self.button_width,11*self.button_height))

    def move(self, axis:str, value:int|float):
        assert axis in 'xyz', 'Provide one of x,y,z axis'
        initial = getattr(self, axis)
        setattr(self, axis, round(getattr(self, axis) + value,self.precision))
        try:
            self.execute(self.principal.move, axis, value)
        except AttributeError:
            logger.warning('No move method found')
            setattr(self, axis, initial)
        self.refresh()
        return

    def rotate(self, axis:str, value:int|float):
        assert axis in 'abc', 'Provide one of a,b,c axis'
        initial = getattr(self, axis)
        setattr(self, axis, round(getattr(self, axis) + value,self.precision))
        try:
            self.execute(self.principal.rotate, axis, value)
        except AttributeError:
            logger.warning('No rotate method found')
            setattr(self, axis, initial)
        self.refresh()
        return
    
    def moveTo(self, 
        x: int|float|str|None = None, 
        y: int|float|str|None = None, 
        z: int|float|str|None = None,
        a: int|float|str|None = None,
        b: int|float|str|None = None,
        c: int|float|str|None = None
    ):
        inputs = [x,y,z,c,b,a] # TODO: Validate input
        axes = 'xyzcba'
        for i,input_ in enumerate(inputs):
            try:
                inputs[i] = float(input_)
            except ValueError:
                logger.warning(f'Ensure input for {axes[i]} is of type float')
        initials = {}
        for axis,value in zip(axes,inputs):
            initials[axis] = getattr(self, axis)
            if value is not None:
                setattr(self, axis, round(value, self.precision))
        try:
            self.execute(self.principal.safeMoveTo, [getattr(self,axis) for axis in axes])
        except AttributeError:
            logger.warning('No moveTo method found')
            for axis,initial in initials.items():
                setattr(self, axis, initial)
        self.refresh()
        return
    
    def rotateTo(self, a:int|float|None = None, b:int|float|None = None, c:int|float|None = None):
        inputs = [c,b,a]
        initials = {}
        for axis,value in zip('cba',inputs):
            initials[axis] = getattr(self, axis)
            if value is not None:
                setattr(self, axis, round(value, self.precision))
        try:
            self.execute(self.principal.rotateTo, [getattr(self,axis) for axis in 'cba'])
        except AttributeError:
            logger.warning('No rotateTo method found')
            for axis,initial in initials.items():
                setattr(self, axis, initial)
        self.refresh()
        return
    
    def home(self):
        try:
            self.execute(self.principal.home)
        except AttributeError:
            logger.warning('No home method found')
        else:
            for axis in 'xyzabc':
                setattr(self, axis, 0)
        self.update()
        self.refresh()
        return
    
    def safe(self):
        try:
            self.execute(self.principal.moveToSafeHeight)
        except AttributeError:
            logger.warning('No safeMoveTo method found')
        else:
            self.z = 0
        self.update()
        self.refresh()
        return
    