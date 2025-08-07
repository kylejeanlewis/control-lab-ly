# -*- coding: utf-8 -*-
""" 
This module contains the GUI panel for controlling liquid handling devices.

Attributes:
    PRECISION (int): The number of decimal places to display for liquid volumes
    TICK_INTERVAL (int): The interval between ticks on the volume scale
    BUTTON_HEIGHT (int): The height of the buttons in the panel
    BUTTON_WIDTH (int): The width of the buttons in the panel
    SCALE_LENGTH (int): The length of the volume scale in the panel
    
## Classes:
    Liquid: A protocol for liquid handling devices
    LiquidPanel: A GUI panel for controlling liquid handling devices

<i>Documentation last updated: 2025-02-22</i>
"""
# Standard library imports
import logging
import tkinter as tk
from tkinter import ttk
from typing import Protocol

# Local application imports
from ....core.control import Proxy
from .gui import Panel

logger = logging .getLogger(__name__)

PRECISION = 1
TICK_INTERVAL = 200

BUTTON_HEIGHT = 1
BUTTON_WIDTH = 6
SCALE_LENGTH = 200

class Liquid(Protocol):
    capacity: float
    channel: int
    reagent: str
    volume: float
    def aspirate(self, volume:float, speed:float|None = None, reagent:str|None= None, *args, **kwargs):...
    def blowout(self, *args, **kwargs):...
    def dispense(self, volume:float, speed:float|None = None, *args, **kwargs):...
    def empty(self, speed:float|None = None, *args, **kwargs):...
    def fill(self, speed:float|None = None, reagent:str|None = None, *args, **kwargs):...
    def isTipOn(self) -> bool:...
    def eject(self, *args, **kwargs):...
    def attach(self, *args, **kwargs):...


class LiquidPanel(Panel):
    """ 
    LiquidPanel is a GUI panel for controlling liquid handling devices
    
    ### Constructor:
        `principal` (Liquid|Proxy|None): The liquid handling device to control
        
    ### Attributes:
        `principal` (Liquid|Proxy|None): The liquid handling device to control
        `title` (str): The title of the panel
        `status` (str): The status of the liquid handling device
        `reagent` (str): The current reagent in the liquid handling device
        `capacity` (float): The capacity of the liquid handling device
        `volume` (float): The current volume of liquid in the liquid handling device
        `channel` (int): The current channel of the liquid handling device
        `tip_on` (bool): The status of the tip on the liquid handling device
        `volume_field` (float): The volume to aspirate/dispense
        `speed_field` (float): The speed to aspirate/dispense
        `button_height` (int): The height of the buttons in the GUI panel.
        `button_width` (int): The width of the buttons in the GUI panel.
        `precision` (int): The number of decimal places to which to round the robot's position and orientation.
        `tick_interval` (int): The interval between tick marks on the rotation scales.
        
    ### Methods:
        `update`: Update the status of the liquid handling device
        `refresh`: Refresh the GUI panel
        `addTo`: Add the GUI panel to a master widget
        `aspirate`: Aspirate a volume of liquid from a container
        `blowout`: Blowout the liquid from the pipette
        `dispense`: Dispense a volume of liquid from the pipette
        `empty`: Empty the liquid from the pipette
        `fill`: Fill the pipette with liquid
        `volumeTo`: Adjust the volume of liquid in the pipette to a specific value
        `attach`: Attach a tip to the pipette
        `eject`: Eject the tip from the pipette
        `toggleTip`: Toggle the tip on the pipette
        
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
    """
    
    def __init__(self, principal: Liquid|Proxy|None = None):
        """ 
        Initialize the LiquidPanel
        
        Args:
            principal (Liquid|Proxy|None): The liquid handling device to control
        """
        super().__init__(principal)
        self.principal: Liquid|Proxy|None = principal
        self.title = "Liquid Handler Control"
        self.status = 'Disconnected'
    
        # Initialize values
        self.reagent: str|None =  None
        self.capacity = 1000
        self.volume = 0
        self.channel = 0
        self.tip_on: bool|None = None
        
        # Fields
        self.volume_field = 0
        self.speed_field = None
        
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
            ('capacity', None),
            ('volume', None),
            ('channel', None)
        )
        # Status
        if not attributes['is_connected']:
            self.status = 'Disconnected'
        elif attributes['is_busy']:
            self.status = 'Busy'
        else:
            self.status = 'Connected'
            
        # Values
        self.capacity = attributes['capacity'] or self.capacity
        self.volume = attributes['volume'] or self.volume
        self.channel = attributes['channel'] or self.channel
        self.tick_interval = self.capacity // 5
        if not hasattr(self.principal, 'isTipOn'):
            self.tip_on = None
        else:
            self.tip_on = self.principal.isTipOn()
        return self.refresh()
    
    def refresh(self, **kwargs):
        if not self.drawn:
            return
        
        # Update labels
        self.label_status.config(text=self.status)
        self.label_current_reagent.config(text=(self.reagent or "<None>"))
        self.label_capacity.config(text=f"{self.capacity} µL")
        
        # Update scales
        self.scale_volume.config(from_=self.capacity, to=0, tickinterval=self.tick_interval)
        self.scale_volume.set(self.volume)
        
        # Update entries
        self.entry_reagent.delete(0, tk.END)
        self.entry_reagent.insert(0, str(self.reagent).replace('None',''))
        entry_reagent_state = tk.DISABLED if self.reagent else tk.NORMAL
        self.entry_reagent.config(state=entry_reagent_state)
        
        self.entry_volume.delete(0, tk.END)
        self.entry_volume.insert(0, str(self.volume_field))
        
        self.entry_speed.delete(0, tk.END)
        self.entry_speed.insert(0, str(self.speed_field).replace('None',''))
        
        button_eject_text = "Eject" if self.tip_on else "Attach"
        button_eject_state = tk.NORMAL if self.tip_on is not None else tk.DISABLED
        self.button_eject.config(text=button_eject_text, state=button_eject_state)
        return
    
    def addTo(self, master: tk.Tk|tk.Frame, size: tuple[int,int]|None = None) -> tuple[int,int]|None:
        # Add layout
        master.rowconfigure(1,weight=1, minsize=13*self.button_width)
        master.columnconfigure(0,weight=1, minsize=9*self.button_width)
        
        # Add keyboard events
        master.bind('<Up>', lambda event: self.aspirate(volume=float(self.entry_volume.get()), speed=self.entry_speed.get(), reagent=self.entry_reagent.get()))
        master.bind('<Down>', lambda event: self.dispense(volume=float(self.entry_volume.get()), speed=self.entry_speed.get()))
        master.bind('<Shift-Up>', lambda event: self.fill(speed=self.entry_speed.get(), reagent=self.entry_reagent.get()))
        master.bind('<Shift-Down>', lambda event: self.empty(speed=self.entry_speed.get()))
        master.bind('.', lambda event: self.blowout())
        
        # Create frames for organization
        status_frame = ttk.Frame(master)
        status_frame.grid(row=0, column=0, padx=10, pady=10, sticky='nsew')
        status_frame.grid_columnconfigure(0,weight=1)
        
        volume_frame = ttk.Frame(master)
        volume_frame.grid(row=1, column=0, padx=10, pady=10, sticky='nsew')
        volume_frame.grid_rowconfigure(0,weight=1)
        # volume_frame.grid_columnconfigure(1,weight=1)
        
        scale_frame = ttk.Frame(volume_frame)
        scale_frame.grid(row=0, column=0, padx=10, pady=10, sticky='nsew')
        scale_frame.grid_rowconfigure(2,weight=1)
        
        button_frame = ttk.Frame(volume_frame)
        button_frame.grid(row=0, column=1, padx=10, pady=10, sticky='nse')
        button_frame.grid_rowconfigure([0,1,2,3,4],weight=1)
        # button_frame.grid_columnconfigure(0,weight=1)
        
        label_frame = ttk.Frame(volume_frame)
        label_frame.grid(row=1, column=0, padx=(10,0), pady=10, sticky='nsew')
        # label_frame.grid_rowconfigure([0,1,2,3,4],weight=1)
        
        input_frame = ttk.Frame(volume_frame)
        input_frame.grid(row=1, column=1, padx=(0,10), pady=10, sticky='nsew')
        # input_frame.grid_rowconfigure([0,1,2,3,4],weight=1)
        # input_frame.grid_columnconfigure(0,weight=1)
        
        # Status Display
        self.button_refresh = ttk.Button(status_frame, text='Refresh', command=self.update)
        self.label_status = ttk.Label(status_frame, text="Disconnected")
        self.button_refresh.grid(row=0, column=1)
        self.label_status.grid(row=1, column=1)

        # Volume Controls
        self.label_channel = ttk.Label(scale_frame, text=f"Channel {self.channel}")
        self.label_capacity = ttk.Label(scale_frame, text=f"{self.capacity} µL")
        self.label_current_reagent = ttk.Label(scale_frame, text="<None>")
        self.label_channel.grid(row=0, column=0)
        self.label_capacity.grid(row=1, column=0)
        self.label_current_reagent.grid(row=3, column=0)
        
        self.scale_volume = tk.Scale(scale_frame, from_=self.capacity, to=0, orient=tk.VERTICAL, length=SCALE_LENGTH, width=self.button_width, tickinterval=self.tick_interval)
        self.scale_volume.bind("<ButtonRelease-1>", lambda event: self.volumeTo(volume=float(self.scale_volume.get()), speed=self.entry_speed.get(), reagent=self.entry_reagent.get()))
        self.scale_volume.grid(row=2, column=0, sticky='nsew')
        
        # Buttons
        ttk.Button(button_frame, text="⏫", command=lambda: self.fill(speed=self.entry_speed.get(), reagent=self.entry_reagent.get()), width=self.button_width).grid(row=0, column=0, sticky='nsew')
        ttk.Button(button_frame, text="🔼", command=lambda: self.aspirate(volume=float(self.entry_volume.get()), speed=self.entry_speed.get(), reagent=self.entry_reagent.get()), width=self.button_width).grid(row=1, column=0, sticky='nsew')
        ttk.Button(button_frame, text="🔽", command=lambda: self.dispense(volume=float(self.entry_volume.get()), speed=self.entry_speed.get()), width=self.button_width).grid(row=2, column=0, sticky='nsew')
        ttk.Button(button_frame, text="⏬", command=lambda: self.empty(speed=self.entry_speed.get()), width=self.button_width).grid(row=3, column=0, sticky='nsew')
        ttk.Button(button_frame, text="⏺️", command=self.blowout, width=self.button_width).grid(row=4, column=0, sticky='nsew')
        
        # Input fields
        self.label_reagent = ttk.Label(label_frame, text="Reagent", justify=tk.RIGHT)
        self.label_volume = ttk.Label(label_frame, text="Volume", justify=tk.RIGHT)
        self.label_speed = ttk.Label(label_frame, text="Speed", justify=tk.RIGHT)
        self.label_ = ttk.Label(label_frame, text="", justify=tk.RIGHT)
        self.label_reagent.grid(row=0, column=0, sticky='nse')
        self.label_volume.grid(row=1, column=0, sticky='nse')
        self.label_speed.grid(row=2, column=0, sticky='nse')
        self.label_.grid(row=3, column=0, sticky='nse')
        
        self.entry_reagent = ttk.Entry(input_frame, width=2*self.button_width, justify=tk.CENTER)
        self.entry_volume = ttk.Entry(input_frame, width=2*self.button_width, justify=tk.CENTER)
        self.entry_speed = ttk.Entry(input_frame, width=2*self.button_width, justify=tk.CENTER)
        self.entry_reagent.grid(row=0, column=0, sticky='nsew')
        self.entry_volume.grid(row=1, column=0, sticky='nsew')
        self.entry_speed.grid(row=2, column=0, sticky='nsew')
        self.button_eject = ttk.Button(input_frame, text="Attach", command=self.toggleTip, width=2*self.button_width)
        self.button_eject.grid(row=3, column=0, sticky='nsew')
        return super().addTo(master, (5*self.button_width,13*self.button_height))

    def aspirate(self, volume:float, speed:float|str|None = None, reagent:str|None = None):
        """ 
        Aspirate a volume of liquid from a container
        
        Args:
            volume (float): The volume of liquid to aspirate
            speed (float|str): The speed at which to aspirate the liquid
            reagent (str): The reagent to aspirate
        """
        speed = float(speed) if (isinstance(speed,str) and len(speed)) else self.speed_field
        reagent = self.reagent or reagent
        self.volume = min(self.volume + volume, self.capacity)
        self.reagent = reagent
        
        self.volume_field = volume
        self.speed_field = speed
        try:
            self.execute(self.principal.aspirate, volume=volume, speed=speed, reagent=reagent)
        except AttributeError:
            logger.warning('No aspirate method found')
            self.update()
        self.refresh()
        return
    
    def blowout(self):
        """Blowout the liquid from the pipette"""
        self.volume = 0
        try:
            self.execute(self.principal.blowout)
        except AttributeError:
            logger.warning('No blowout method found')
            self.update()
        self.refresh()
        return
    
    def dispense(self, volume:float, speed:float|str|None = None):
        """ 
        Dispense a volume of liquid from the pipette
        
        Args:
            volume (float): The volume of liquid to dispense
            speed (float|str): The speed at which to dispense the liquid
        """
        speed = float(speed) if (isinstance(speed,str) and len(speed)) else self.speed_field
        self.volume = max(self.volume - volume, 0)
        
        self.volume_field = volume
        self.speed_field = speed
        try:
            self.execute(self.principal.dispense, volume=volume, speed=speed)
        except AttributeError:
            logger.warning('No dispense method found')
            self.update()
        self.refresh()
        return
    
    def empty(self, speed:float|str|None = None):
        """ 
        Empty the liquid from the pipette
        
        Args:
            speed (float|str): The speed at which to empty the liquid
        """
        speed = float(speed) if (isinstance(speed,str) and len(speed)) else self.speed_field
        self.volume = 0
        self.speed_field = speed
        try:
            self.execute(self.principal.empty, speed=speed)
        except AttributeError:
            logger.warning('No empty method found')
            self.update()
        self.refresh()
        return
    
    def fill(self, speed:float|str|None = None, reagent:str|None = None):
        """ 
        Fill the pipette with liquid
        
        Args:
            speed (float|str): The speed at which to fill the pipette
            reagent (str): The reagent to fill the pipette with
        """
        speed = float(speed) if (isinstance(speed,str) and len(speed)) else self.speed_field
        reagent = self.reagent or reagent
        self.volume = self.capacity
        self.reagent = reagent
        self.speed_field = speed
        try:
            self.execute(self.principal.fill, speed=speed, reagent=reagent)
        except AttributeError:
            logger.warning('No fill method found')
            self.update()
        self.refresh()
        return
    
    def volumeTo(self, volume:float, speed:float|str|None = None, reagent:str|None = None):
        """
        Adjust the volume of liquid in the pipette to a specific value
        
        Args:
            volume (float): The volume to adjust to
            speed (float|str): The speed at which to adjust the volume
            reagent (str): The reagent to use for the adjustment
        """
        current_volume = self.volume
        diff = volume - current_volume
        return self.aspirate(volume=diff, speed=speed, reagent=reagent) if diff > 0 else self.dispense(volume=abs(diff), speed=speed)

    def attach(self):
        """Attach a tip to the pipette"""
        self.tip_on = True
        self.reagent = None
        try:
            self.execute(self.principal.attach, tip_length=90)  # TODO: Add tip length to settings
        except AttributeError:
            logger.warning('No attach method found')
            self.update()
        self.refresh()
        return
        
    def eject(self):
        """Eject the tip from the pipette"""
        self.tip_on = False
        self.reagent = None
        try:
            self.execute(self.principal.eject)
        except AttributeError:
            logger.warning('No eject method found')
            self.update()
        self.refresh()
        return
    
    def toggleTip(self):
        """Toggle the tip on the pipette"""
        return self.eject() if self.tip_on else self.attach()
        