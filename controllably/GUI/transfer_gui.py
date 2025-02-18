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
TICK_INTERVAL = 200

BUTTON_HEIGHT = 1
BUTTON_WIDTH = 6
SCALE_LENGTH = 200

class Liquid(Protocol):
    capacity: float
    channel: int
    reagent: str
    volume: float
    def aspirate(self, volume:float, speed:float|None = None, reagent:str|None= None, *args, **kwargs):
        raise NotImplementedError
    
    def blowout(self, *args, **kwargs):
        raise NotImplementedError
    
    def dispense(self, volume:float, speed:float|None = None, *args, **kwargs):
        raise NotImplementedError
    
    def empty(self, speed:float|None = None, *args, **kwargs):
        raise NotImplementedError
    
    def fill(self, speed:float|None = None, reagent:str|None = None, *args, **kwargs):
        raise NotImplementedError
    
    def isTipOn(self) -> bool:
        raise NotImplementedError
    
    def eject(self, *args, **kwargs):
        raise NotImplementedError
    
    def attach(self, *args, **kwargs):
        raise NotImplementedError


class LiquidPanel(Panel):
    def __init__(self, principal: Liquid|Proxy|None = None):
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
        # Status
        if not self.getAttribute('is_connected', False):
            self.status = 'Disconnected'
            # return self.refresh()
        elif self.getAttribute('is_busy', False):
            self.status = 'Busy'
            # return self.refresh()
        else:
            self.status = 'Connected'
            
        # Values
        self.capacity = self.getAttribute('capacity') or self.capacity
        self.volume = self.getAttribute('volume') or self.volume
        self.channel = self.getAttribute('channel') or self.channel
        self.tick_interval = self.capacity // 5
        if not hasattr(self.principal, 'isTipOn'):
            self.tip_on = None
        else:
            self.tip_on = self.principal.isTipOn()
        
        # Fields
        # volume = self.entry_volume.get()
        # speed = self.entry_speed.get()
        # self.volume_field = volume if len(volume) else 0
        # self.speed_field = speed if len(speed) else None
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
        
        # self.entry_cycles.delete(0, tk.END)
        # self.entry_cycles.insert(0, str(self.cycles_field))
        
        # self.entry_delay.delete(0, tk.END)
        # self.entry_delay.insert(0, str(self.delay_field))
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
        self.volume = 0
        try:
            self.execute(self.principal.blowout)
        except AttributeError:
            logger.warning('No blowout method found')
            self.update()
        self.refresh()
        return
    
    def dispense(self, volume:float, speed:float|str|None = None):
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
        current_volume = self.volume
        diff = volume - current_volume
        return self.aspirate(volume=diff, speed=speed, reagent=reagent) if diff > 0 else self.dispense(volume=abs(diff), speed=speed)

    def attach(self):
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
        return self.eject() if self.tip_on else self.attach()
        