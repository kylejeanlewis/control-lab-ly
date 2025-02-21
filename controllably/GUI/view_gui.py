# -*- coding: utf-8 -*-
# Standard library imports
import logging
import time
import tkinter as tk
from tkinter import ttk
from typing import Protocol, Iterable

# Third party imports
import cv2
import numpy as np
from PIL import Image, ImageTk

# Local application imports
from ..core.control import Proxy
from .gui import Panel

logger = logging .getLogger(__name__)

BUTTON_HEIGHT = 1
BUTTON_WIDTH = 6

class View(Protocol):
    frame_rate: int|float
    frame_size: tuple[int,int]
    def connectFeed(self):
        raise NotImplementedError
    
    def disconnectFeed(self):
        raise NotImplementedError
    
    def getFrame(self) -> tuple[bool, np.ndarray]:
        raise NotImplementedError
    
    @staticmethod
    def loadImageFile(filename: str) -> np.ndarray:
        raise NotImplementedError
    
    @staticmethod
    def saveFrame(frame: np.ndarray, filename: str|None = None) -> bool:
        raise NotImplementedError
    
    def setFrameSize(self, size:Iterable[int] = (10_000,10_000)):
        raise NotImplementedError


class ViewPanel(Panel):
    def __init__(self, principal: View|Proxy|None = None):
        super().__init__(principal)
        self.principal: View|Proxy|None = principal
        self.title = "Camera control"
        self.status = 'Disconnected'
    
        # Initialize view values
        self.fps = getattr(self.principal, 'frame_rate', 24)
        self.size = getattr(self.principal, 'frame_size', (640,360))
        self.is_connected = False
        self.is_connected_previous = False
        self.is_frozen = False
        self.latest_frame: np.ndarray|None = None
        self.tk_image: ImageTk.PhotoImage|None = None
        
        # Settings
        self.button_height = BUTTON_HEIGHT
        self.button_width = BUTTON_WIDTH
        return
    
    @property
    def latest_image(self) -> Image.Image|None:
        return Image.fromarray(self.latest_frame) if self.latest_frame is not None else None
    
    def update(self, **kwargs):
        attributes = self.getAttributes(
            ('is_connected', False)
        )
        # Status
        if not attributes['is_connected']:
            self.status = 'Disconnected'
            self.is_connected = False
        else:
            self.status = 'Connected'
            self.is_connected = True
        
        # Get next frame
        if self.is_connected != self.is_connected_previous:
            time.sleep(1)
        self.getFrame()
        self.is_connected_previous = self.is_connected
        self.refresh()
        if isinstance(self.widget, tk.Tk):
            
            self.widget.after(int(1000/self.fps), self.update)
        return 
    
    def refresh(self, **kwargs):
        if not self.drawn:
            return
        
        # Update labels
        self.label_status.config(text=self.status)
        
        # Update buttons
        self.button_connect.config(text=('Disconnect' if self.is_connected else 'Connect'))
        self.button_freeze.config(text=('Unfreeze' if self.is_frozen else 'Freeze'))
        
        # Redraw canvas
        if self.latest_frame is not None:
            self.tk_image = ImageTk.PhotoImage(image=self.latest_image, master=self.image_frame)
            self.canvas.create_image(0,0, image=self.tk_image, anchor=tk.NW)
        return
    
    def addTo(self, master: tk.Tk|tk.Frame, size: tuple[int,int]|None = None) -> tuple[int,int]|None:
        # Add layout
        master.rowconfigure(1,weight=1, minsize=self.button_height)
        master.columnconfigure(0,weight=1, minsize=self.button_width)
        
        # Create frames for organization
        status_frame = ttk.Frame(master)
        status_frame.grid(row=0, column=0, padx=10, pady=10, sticky='nsew')
        status_frame.columnconfigure(0,weight=1)
        
        button_frame = ttk.Frame(status_frame)
        button_frame.grid(row=0, column=0, padx=10, pady=10, sticky='nsew')
        button_frame.columnconfigure([0,1,2,3],weight=1)
        
        self.image_frame = ttk.Frame(master)
        self.image_frame.grid(row=1, column=0, padx=10, pady=10, sticky='nsew')
        self.image_frame.rowconfigure(0,weight=1)
        self.image_frame.columnconfigure(0,weight=1)
        
        # Status Display
        # self.button_refresh = ttk.Button(status_frame, text='Refresh', command=self.update, state='disabled', width=self.button_width)
        self.label_status = ttk.Label(status_frame, text="Disconnected")
        # self.button_refresh.grid(row=0, column=1)
        self.label_status.grid(row=0, column=1)
        
        # Buttons
        self.button_freeze = ttk.Button(button_frame, text='Freeze', command=self.toggleFreeze, width=self.button_width)
        self.button_save = ttk.Button(button_frame, text='Save', command=lambda: self.save(), width=self.button_width)
        self.button_load = ttk.Button(button_frame, text='Load', command=lambda: 0, width=self.button_width)
        self.button_connect = ttk.Button(button_frame, text='Connect', command=self.toggleConnect, width=self.button_width)
        self.button_freeze.grid(row=0,column=0,sticky='nsew')
        self.button_save.grid(row=0,column=1,sticky='nsew')
        self.button_load.grid(row=0,column=2,sticky='nsew')
        self.button_connect.grid(row=0,column=3,sticky='nsew')
        
        # Canvas
        self.canvas = tk.Canvas(self.image_frame, width=self.size[0], height=self.size[1])
        self.canvas.grid(row=1, column=0, padx=10, pady=10, sticky='nsew')
        
        return super().addTo(master, (self.button_width,self.button_height))
        
    def save(self, filename:str|None = None):
        tag = "canvas"
        self.canvas.itemcget(tag, "image")
        self.principal.saveFrame(self.latest_frame, filename)
        return
    
    def load(self, filename:str):
        image = self.principal.loadImageFile(filename)
        self.is_frozen = True
        self.latest_frame = image
        return
    
    def toggleConnect(self):
        return self.disconnect() if self.is_connected else self.connect()
    
    def toggleFreeze(self):
        self.is_frozen = not self.is_frozen
        return
            
    def connect(self):
        self.principal.connectFeed()
        self.is_connected = True
        return
    
    def disconnect(self):
        self.principal.disconnectFeed()
        self.is_connected = False
        return
        
    def getFrame(self):
        ret, frame = self.principal.getFrame()
        self.latest_frame = frame if (not self.is_frozen and ret) else self.latest_frame
        return
    