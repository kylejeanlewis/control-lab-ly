# -*- coding: utf-8 -*-
""" 
This module contains the view panel for the camera feed.

Attributes:
    BUTTON_HEIGHT (int): Button height
    BUTTON_WIDTH (int): Button width
    
## Classes:
    `View`: Protocol for the view panel
    `ViewPanel`: View panel for the camera feed
    
<i>Documentation last updated: 2025-02-22</i>
"""
# Standard library imports
from __future__ import annotations
from datetime import datetime
import logging
import os
from pathlib import Path
import time
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from typing import Protocol, Iterable

# Third party imports
import cv2
import numpy as np
from PIL import Image, ImageTk

# Local application imports
from ....core.control import Proxy
from .gui import Panel

logger = logging .getLogger(__name__)

BUTTON_HEIGHT = 1
BUTTON_WIDTH = 6

class View(Protocol):
    frame_rate: int|float
    frame_size: tuple[int,int]
    def connectFeed(self):...
    def disconnectFeed(self):...
    def getFrame(self) -> tuple[bool, np.ndarray]:...
    @staticmethod
    def loadImageFile(filename: str) -> np.ndarray:...
    @staticmethod
    def saveFrame(frame: np.ndarray, filename: str|None = None) -> bool:...
    def setFrameSize(self, size:Iterable[int] = (10_000,10_000)):...


class ViewPanel(Panel):
    """ 
    View panel for the camera feed
    
    ### Constructor:
        `principal` (View|Proxy|None): The principal object for the view panel
        
    ### Attributes:
        `fps` (int|float): Frames per second
        `size` (tuple[int,int]): Frame size
        `is_connected` (bool): Connection status
        `is_connected_previous` (bool): Previous connection status
        `is_frozen` (bool): Freeze status
        `latest_frame` (np.ndarray|None): Latest frame
        `latest_image` (Image.Image|None): Latest image as a PIL Image
        `tk_image` (ImageTk.PhotoImage|None): Latest image as a Tkinter image
        `loaded_filename` (str): Loaded filename
        `last_visited_load_dir` (str): Last visited directory for loading files
        `last_visited_save_dir` (str): Last visited directory for saving files
        `button_height` (int): Button height
        `button_width` (int): Button width
        
    ### Methods:
        `updateStream`: Update the stream
        `refresh`: Refresh the view
        `addTo`: Add the view to the master widget
        `getSaveDirectory`: Get the directory to save the image
        `save`: Save the current image
        `load`: Load an image file
        `toggleConnect`: Toggle connection to the feed
        `toggleFreeze`: Toggle the freeze state
        `connect`: Connect to the feed
        `disconnect`: Disconnect from the feed
        `getFrame`: Get the next frame
    """
    
    def __init__(self, principal: View|Proxy|None = None):
        """ 
        Initialize the view panel
        
        Args:
            principal (View|Proxy|None): The principal object for the view panel
        """
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
        
        # Dialog values
        self.loaded_filename = 'Feed'
        self.last_visited_load_dir = os.getcwd()
        self.last_visited_save_dir = os.getcwd()
        
        # Settings
        self.button_height = BUTTON_HEIGHT
        self.button_width = BUTTON_WIDTH
        return
    
    @property
    def latest_image(self) -> Image.Image|None:
        """Latest image as a PIL Image"""
        return Image.fromarray(self.latest_frame) if self.latest_frame is not None else None
    
    def updateStream(self, **kwargs):
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
            self.widget.after(int(1000/self.fps), self.updateStream)
        return 
    
    def refresh(self, **kwargs):
        if not self.drawn:
            return
        
        # Update labels
        self.label_status.config(text=self.status)
        self.label_canvas.config(text=self.loaded_filename)
        
        # Update buttons
        self.button_connect.config(text=('Disconnect' if self.is_connected else 'Connect'))
        self.button_freeze.config(text=('Unfreeze' if self.is_frozen else 'Freeze'))
        
        # Update entries
        self.entry_save.delete(0, tk.END)
        self.entry_save.insert(0, str(self.last_visited_save_dir).replace('None',''))
        
        # Redraw canvas
        if self.latest_frame is not None and all(self.latest_frame.shape):
            # width = self.image_frame.winfo_width()
            # height = self.image_frame.winfo_height()
            # image_height,image_width,_ = self.latest_frame.shape
            # aspect_ratio = image_width/image_height
            # width,height = (height/aspect_ratio,height) if (width/height > aspect_ratio) else (width, width*aspect_ratio)
            # image = self.latest_image.resize((int(width),int(height)))
            image = self.latest_image
            self.tk_image = ImageTk.PhotoImage(image=image, master=self.image_frame)
            self.canvas.delete("all")
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
        button_frame.columnconfigure([0,1,2],weight=1)
        
        self.image_frame = ttk.Frame(master)
        self.image_frame.grid(row=1, column=0, padx=10, pady=10, sticky='nsew')
        self.image_frame.rowconfigure(1,weight=1)
        self.image_frame.columnconfigure(0,weight=1)
        
        save_frame = ttk.Frame(master)
        save_frame.grid(row=2, column=0, padx=10, pady=10, sticky='nsew')
        save_frame.columnconfigure(0,weight=1)
        
        # Status Display
        self.label_status = ttk.Label(status_frame, text="Disconnected")
        self.label_status.grid(row=0, column=1)
        
        # Buttons
        self.button_freeze = ttk.Button(button_frame, text='Freeze', command=self.toggleFreeze, width=self.button_width)
        self.button_load = ttk.Button(button_frame, text='Load', command=self.load, width=self.button_width)
        self.button_connect = ttk.Button(button_frame, text='Connect', command=self.toggleConnect, width=self.button_width)
        self.button_freeze.grid(row=0,column=0,sticky='nsew')
        self.button_load.grid(row=0,column=1,sticky='nsew')
        self.button_connect.grid(row=0,column=2,sticky='nsew')
        
        # Canvas
        self.label_canvas = ttk.Label(self.image_frame, text='')
        self.label_canvas.grid(row=0, column=0, sticky='nsew')
        self.canvas = tk.Canvas(self.image_frame, width=self.size[0], height=self.size[1])
        self.canvas.grid(row=1, column=0,    sticky='nsew')
        
        # Save options
        self.button_save = ttk.Button(save_frame, text='Save', command=self.save, width=self.button_width)
        self.button_save.grid(row=0, column=1, sticky='nsew')
        self.entry_save = ttk.Entry(save_frame, width=2*self.button_width, justify=tk.LEFT)
        self.entry_save.grid(row=0, column=0, sticky='nsew')
        self.entry_save.bind("<ButtonPress-1>", lambda event: self.getSaveDirectory())
        
        return super().addTo(master, (self.button_width,self.button_height))
    
    def getSaveDirectory(self):
        """Get the directory to save the image"""
        self.last_visited_save_dir = filedialog.askdirectory(initialdir=self.last_visited_save_dir)
        return
    
    def save(self):
        """Save the current image"""
        now = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f'image-{now}.png'
        filepath = Path(self.last_visited_save_dir)/filename
        self.principal.saveFrame(self.latest_frame, str(filepath))
        return
    
    def load(self):
        """Load an image file"""
        filename = filedialog.askopenfilename(initialdir=self.last_visited_load_dir)
        if not filename:
            return
        self.last_visited_load_dir = str(Path(filename).parent)
        self.loaded_filename = filename
        image = cv2.cvtColor(cv2.imread(filename), cv2.COLOR_BGR2RGB)
        self.is_frozen = True
        self.latest_frame = image
        return
    
    def toggleConnect(self):
        """Toggle connection to the feed"""
        return self.disconnect() if self.is_connected else self.connect()
    
    def toggleFreeze(self):
        """Toggle the freeze state"""
        self.is_frozen = not self.is_frozen
        if not self.is_frozen:
            self.loaded_filename = 'Feed'
        return
            
    def connect(self):
        """Connect to the feed"""
        self.principal.connectFeed()
        self.is_connected = True
        return
    
    def disconnect(self):
        """Disconnect from the feed"""
        self.principal.disconnectFeed()
        self.is_connected = False
        return
        
    def getFrame(self):
        """Get the next frame"""
        next_frame = self.latest_frame
        if not self.is_frozen:
            ret, frame = self.principal.getFrame()
            if ret:
                next_frame = frame
        self.latest_frame = next_frame
        return
    