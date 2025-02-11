# -*- coding: utf-8 -*-
# Standard library imports
import tkinter as tk
from typing import Callable

# Local application imports
from .gui import GUI


class MoveGUI(GUI):
    def __init__(self, principal: Callable):
        super().__init__(principal)
    
        # Initialize axis values
        self.x = 0
        self.y = 0
        self.z = 0
        self.a = 0  # Rotation around z-axis (yaw)
        self.b = 0  # Rotation around y-axis (pitch)
        self.c = 0  # Rotation around x-axis (roll)
        return
    
    def updateValues(self):
        self.position_label.config(text=f"Position:\nx={self.x}, y={self.y}, z={self.z}\na={self.a}, b={self.b}, c={self.c}")
    
    def addTo(self, master: tk.Misc):
        master.title("Robot Control D-Pad")
        
        # Create frames for organization
        status_frame = tk.Frame(master)
        status_frame.grid(row=0, column=0, columnspan=2, padx=10, pady=10)
        
        translation_frame = tk.Frame(master)
        translation_frame.grid(row=1, column=0, padx=10, pady=10)

        rotation_frame = tk.Frame(master)
        rotation_frame.grid(row=1, column=1, padx=10, pady=10)
        
        # Status Display
        self.position_label = tk.Label(status_frame, text="Position: \nx=0, y=0, z=0\na=0, b=0, c=0")
        self.position_label.grid(row=0, column=0, padx=(0,10), rowspan=2)
        tk.Button(status_frame, text='Terminate', command=self.close).grid(row=0, column=1)
        self.status_label = tk.Label(status_frame, text="Connected")
        self.status_label.grid(row=1, column=1)

        # Translation Controls
        BUTTON_WIDTH = 5
        tk.Label(translation_frame, text="Translation").grid(row=0, column=0, columnspan=7)
        tk.Button(translation_frame, text="Home ", command=self.home, width=BUTTON_WIDTH).grid(row=4, column=3)
        tk.Button(translation_frame, text="Safe ", command=self.safe, width=BUTTON_WIDTH).grid(row=4, column=7)
        
        tk.Button(translation_frame, text="X- 10", command=lambda: self.move(axis='x',value=-10), width=BUTTON_WIDTH).grid(row=4, column=0)
        tk.Button(translation_frame, text="X-  1", command=lambda: self.move(axis='x',value=-1), width=BUTTON_WIDTH).grid(row=4, column=1)
        tk.Button(translation_frame, text="X-0.1", command=lambda: self.move(axis='x',value=-0.1), width=BUTTON_WIDTH).grid(row=4, column=2)
        tk.Button(translation_frame, text="X+0.1", command=lambda: self.move(axis='x',value=0.1), width=BUTTON_WIDTH).grid(row=4, column=4)
        tk.Button(translation_frame, text="X+  1", command=lambda: self.move(axis='x',value=1), width=BUTTON_WIDTH).grid(row=4, column=5)
        tk.Button(translation_frame, text="X+ 10", command=lambda: self.move(axis='x',value=10), width=BUTTON_WIDTH).grid(row=4, column=6)
        
        tk.Button(translation_frame, text="Y+ 10", command=lambda: self.move(axis='y',value=10), width=BUTTON_WIDTH).grid(row=1, column=3)
        tk.Button(translation_frame, text="Y+  1", command=lambda: self.move(axis='y',value=1), width=BUTTON_WIDTH).grid(row=2, column=3)
        tk.Button(translation_frame, text="Y+0.1", command=lambda: self.move(axis='y',value=0.1), width=BUTTON_WIDTH).grid(row=3, column=3)
        tk.Button(translation_frame, text="Y-0.1", command=lambda: self.move(axis='y',value=-0.1), width=BUTTON_WIDTH).grid(row=5, column=3)
        tk.Button(translation_frame, text="Y-  1", command=lambda: self.move(axis='y',value=-1), width=BUTTON_WIDTH).grid(row=6, column=3)
        tk.Button(translation_frame, text="Y- 10", command=lambda: self.move(axis='y',value=-10), width=BUTTON_WIDTH).grid(row=7, column=3)
        
        tk.Button(translation_frame, text="Z+ 10", command=lambda: self.move(axis='z',value=10), width=BUTTON_WIDTH).grid(row=1, column=7)
        tk.Button(translation_frame, text="Z+  1", command=lambda: self.move(axis='z',value=1), width=BUTTON_WIDTH).grid(row=2, column=7)
        tk.Button(translation_frame, text="Z+0.1", command=lambda: self.move(axis='z',value=0.1), width=BUTTON_WIDTH).grid(row=3, column=7)
        tk.Button(translation_frame, text="Z-0.1", command=lambda: self.move(axis='z',value=-0.1), width=BUTTON_WIDTH).grid(row=5, column=7)
        tk.Button(translation_frame, text="Z-  1", command=lambda: self.move(axis='z',value=-1), width=BUTTON_WIDTH).grid(row=6, column=7)
        tk.Button(translation_frame, text="Z- 10", command=lambda: self.move(axis='z',value=-10), width=BUTTON_WIDTH).grid(row=7, column=7)

        # Rotation Controls
        tk.Label(rotation_frame, text="Rotation").grid(row=0, column=0, columnspan=3)
        tk.Button(rotation_frame, text="Roll CW (A+)", command=lambda: self.rotate(axis='a',value=1)).grid(row=1, column=1)
        tk.Button(rotation_frame, text="Roll CCW (A-)", command=lambda: self.rotate(axis='a',value=-1)).grid(row=2, column=1)
        tk.Button(rotation_frame, text="Pitch Up (B+)", command=lambda: self.rotate(axis='b',value=1)).grid(row=3, column=1)
        tk.Button(rotation_frame, text="Pitch Down (B-)", command=lambda: self.rotate(axis='b',value=-1)).grid(row=4, column=1)
        tk.Button(rotation_frame, text="Yaw CW (C+)", command=lambda: self.rotate(axis='c',value=1)).grid(row=5, column=1)
        tk.Button(rotation_frame, text="Yaw CCW (C-)", command=lambda: self.rotate(axis='c',value=-1)).grid(row=6, column=1)
        return

    def move(self, axis:str, value:int|float):
        assert axis in 'xyz', 'Provide one of x,y,z axis'
        if axis == 'x':
            self.x += value
        elif axis == 'y':
            self.y += value
        elif axis == 'z':
            self.z += value
        else:
            return
        self.principal.move(axis,value)
        self.updateValues()
        return

    def rotate(self, axis:str, value:int|float):
        assert axis in 'abc', 'Provide one of a,b,c axis'
        if axis == 'a':
            self.a += value
        elif axis == 'b':
            self.b += value
        elif axis == 'c':
            self.c += value
        else:
            return
        self.principal.rotate(axis,value)
        self.updateValues()
        return 
    
    def home(self):
        self.principal.home()
        self.updateValues()
        return
    
    def safe(self):
        self.principal.moveToSafeHeight()
        self.updateValues()
        return

    def getPosition(self):
        command = dict(
            method = 'getattr',
            args = (self.object_id,'position')
        )
        self.sendCommand(command)
        return
