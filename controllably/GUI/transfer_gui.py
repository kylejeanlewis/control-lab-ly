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
TICK_INTERVAL = 100

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


class LiquidPanel(Panel):
    def __init__(self, principal: Liquid|Proxy|None = None):
        super().__init__(principal)
        self.principal: Liquid|Proxy|None = principal
        self.title = "Liquid Handler Control"
        self.status = 'Disconnected'
    
        # Initialize volume values
        self.reagent: str|None =  None
        self.capacity = 1000
        self.volume = 0
        
        # Fields
        self.reagent_field = '<empty>'
        self.volume_field = 0
        self.speed_field = None
        self.cycles_field = 1
        self.delay_field = 0
        
        # Settings
        self.precision = PRECISION
        self.tick_interval = TICK_INTERVAL
        return
    
    def update(self, **kwargs):
        # Status
        if not self.getAttribute('is_connected', False):
            self.status = 'Disconnected'
            return self
        elif self.getAttribute('is_busy', False):
            self.status = 'Busy'
            return self.refresh()
        else:
            self.status = 'Connected'
            
        # Values
        self.capacity = self.getAttribute('capacity') or self.capacity
        self.volume = self.getAttribute('volume') or self.volume
        
        # Fields
        reagent = self.entry_reagent.get()
        volume = self.entry_volume.get()
        speed = self.entry_speed.get()
        cycles = self.entry_cycles.get()
        delay = self.entry_delay.get()
        print(f"{reagent=}")
        print(f"{volume=}")
        print(f"{speed=}")
        print(f"{cycles=}")
        print(f"{delay=}")
        self.reagent_field = reagent if len(reagent) else self.reagent
        self.volume_field = volume if len(volume) else 0
        self.speed_field = speed if len(speed) else None
        self.cycles_field = cycles if len(cycles) else 1
        self.delay_field = delay if len(delay) else 0
        return self.refresh()
    
    def refresh(self, **kwargs):
        if not self.drawn:
            return
        
        # Update labels
        self.label_status.config(text=self.status)
        self.label_current_reagent.config(text=self.reagent)
        self.label_capacity.config(text=f"{self.capacity} µL")
        
        # Update scales
        self.scale_volume.set(self.volume)
        
        # Update entries
        self.entry_reagent.delete(0, tk.END)
        self.entry_reagent.insert(0, self.reagent_field)
        self.entry_volume.delete(0, tk.END)
        self.entry_volume.insert(0, str(self.volume_field))
        self.entry_speed.delete(0, tk.END)
        self.entry_speed.insert(0, str(self.speed_field))
        self.entry_cycles.delete(0, tk.END)
        self.entry_cycles.insert(0, str(self.cycles_field))
        self.entry_delay.delete(0, tk.END)
        self.entry_delay.insert(0, str(self.delay_field))
        return
    
    def addTo(self, master: tk.Tk|tk.Frame, size: tuple[int,int]|None = None) -> tuple[int,int]|None:
        BUTTON_HEIGHT = 1
        BUTTON_WIDTH = 6
        
        # Add layout
        master.rowconfigure(1,weight=1, minsize=13*BUTTON_WIDTH)
        master.columnconfigure(0,weight=1, minsize=9*BUTTON_WIDTH)
        
        # Add keyboard events
        master.bind('<Up>', lambda event: self.aspirate(axis='y', value=0.1))
        master.bind('<Down>', lambda event: self.dispense(axis='y', value=-0.1))
        master.bind('<Shift-Up>', lambda event: self.fill(axis='z', value=0.1))
        master.bind('<Shift-Down>', lambda event: self.empty(axis='z', value=-0.1))
        master.bind('.', lambda event: self.blowout())
        
        # Create frames for organization
        status_frame = ttk.Frame(master)
        status_frame.grid(row=0, column=0, padx=10, pady=10, sticky='nsew')
        status_frame.columnconfigure(0,weight=1)
        
        volume_frame = ttk.Frame(master)
        volume_frame.grid(row=1, column=0, padx=10, pady=10, sticky='nsew')
        volume_frame.grid_rowconfigure([0,1],weight=1)
        volume_frame.grid_columnconfigure(1,weight=1)
        
        scale_frame = ttk.Frame(volume_frame)
        scale_frame.grid(row=0, column=0, padx=10, pady=10, sticky='nsew')
        scale_frame.grid_rowconfigure(2,weight=1)
        
        button_frame = ttk.Frame(volume_frame)
        button_frame.grid(row=0, column=1, padx=10, pady=10, sticky='nsew')
        button_frame.grid_rowconfigure([0,1,2,3,4],weight=1)
        button_frame.grid_columnconfigure(0,weight=1)
        
        label_frame = ttk.Frame(volume_frame)
        label_frame.grid(row=1, column=0, padx=(10,0), pady=10, sticky='nsew')
        label_frame.grid_rowconfigure([0,1,2,3,4],weight=1)
        
        input_frame = ttk.Frame(volume_frame)
        input_frame.grid(row=1, column=1, padx=(0,10), pady=10, sticky='nsew')
        input_frame.grid_rowconfigure([0,1,2,3,4],weight=1)
        input_frame.grid_columnconfigure(0,weight=1)
        
        # Status Display
        self.button_close = ttk.Button(status_frame, text='Terminate', command=self.close)
        self.button_refresh = ttk.Button(status_frame, text='Refresh', command=self.update)
        self.label_status = ttk.Label(status_frame, text="Disconnected")
        self.button_close.grid(row=0, column=1)
        self.button_refresh.grid(row=1, column=1)
        self.label_status.grid(row=2, column=1)

        # Volume Controls
        self.label_current_reagent = ttk.Label(scale_frame, text="<empty>")
        self.label_capacity = ttk.Label(scale_frame, text=f"{self.capacity} µL")
        self.label_zero = ttk.Label(scale_frame, text="0 µL")
        self.label_current_reagent.grid(row=0, column=0)
        self.label_capacity.grid(row=1, column=0)
        self.label_zero.grid(row=3, column=0)
        
        self.scale_volume = tk.Scale(scale_frame, from_=1000, to=0, orient=tk.VERTICAL, length=BUTTON_HEIGHT*10, width=BUTTON_WIDTH, tickinterval=100)
        self.scale_volume.bind("<ButtonRelease-1>", lambda event: self.volumeTo(volume=float(self.scale_volume.get())))
        self.scale_volume.grid(row=2, column=0, sticky='nsew')
        
        # Buttons
        ttk.Button(button_frame, text="⏫", command=lambda: self.fill(speed=self.entry_speed.get(), reagent=self.entry_reagent.get()), width=BUTTON_WIDTH).grid(row=0, column=0, sticky='nsew')
        ttk.Button(button_frame, text="🔼", command=lambda: self.aspirate(volume=float(self.entry_volume.get()), speed=self.entry_speed.get(), reagent=self.entry_reagent.get()), width=BUTTON_WIDTH).grid(row=1, column=0, sticky='nsew')
        ttk.Button(button_frame, text="🔽", command=lambda: self.dispense(volume=float(self.entry_volume.get()), speed=self.entry_speed.get()), width=BUTTON_WIDTH).grid(row=2, column=0, sticky='nsew')
        ttk.Button(button_frame, text="⏬", command=lambda: self.empty(speed=self.entry_speed.get()), width=BUTTON_WIDTH).grid(row=3, column=0, sticky='nsew')
        ttk.Button(button_frame, text="⏺️", command=lambda: self.blowout(), width=BUTTON_WIDTH).grid(row=4, column=0, sticky='nsew')
        
        # Input fields
        self.label_reagent = ttk.Label(label_frame, text="Reagent", justify=tk.RIGHT)
        self.label_volume = ttk.Label(label_frame, text="Volume", justify=tk.RIGHT)
        self.label_speed = ttk.Label(label_frame, text="Speed", justify=tk.RIGHT)
        self.label_cycles = ttk.Label(label_frame, text="Cycles", justify=tk.RIGHT)
        self.label_delay = ttk.Label(label_frame, text="Delay", justify=tk.RIGHT)
        self.label_reagent.grid(row=0, column=0, sticky='e')
        self.label_volume.grid(row=1, column=0, sticky='e')
        self.label_speed.grid(row=2, column=0, sticky='e')
        self.label_cycles.grid(row=3, column=0, sticky='e')
        self.label_delay.grid(row=4, column=0, sticky='e')
        
        self.entry_reagent = ttk.Entry(input_frame, width=BUTTON_WIDTH, justify=tk.CENTER)#, textvariable=self.reagent_field)
        self.entry_volume = ttk.Entry(input_frame, width=BUTTON_WIDTH, justify=tk.CENTER)#, textvariable=self.volume_field)
        self.entry_speed = ttk.Entry(input_frame, width=BUTTON_WIDTH, justify=tk.CENTER)#, textvariable=self.speed_field)
        self.entry_cycles = ttk.Entry(input_frame, width=BUTTON_WIDTH, justify=tk.CENTER)#, textvariable=self.cycles_field)
        self.entry_delay = ttk.Entry(input_frame, width=BUTTON_WIDTH, justify=tk.CENTER)#, textvariable=self.delay_field)
        self.entry_reagent.grid(row=0, column=0, sticky='nsew')
        self.entry_volume.grid(row=1, column=0, sticky='nsew')
        self.entry_speed.grid(row=2, column=0, sticky='nsew')
        self.entry_cycles.grid(row=3, column=0, sticky='nsew')
        self.entry_delay.grid(row=4, column=0, sticky='nsew')
        return super().addTo(master, (2*BUTTON_WIDTH,13*BUTTON_HEIGHT))

    def aspirate(self, volume:float, speed:float|None = None, reagent:str|None = None):
        try:
            speed = float(speed)
        except ValueError:
            if isinstance(speed, str) and speed=='None':
                speed = None
            else:
                logger.warning('Ensure input for speed is of type float')
        self.volume = min(self.volume + volume, self.capacity)
        self.reagent = reagent
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
    
    def dispense(self, volume:float, speed:float|None = None):
        try:
            speed = float(speed)
        except ValueError:
            if isinstance(speed, str) and speed=='None':
                speed = None
            else:
                logger.warning('Ensure input for speed is of type float')
        self.volume = max(self.volume - volume, 0)
        try:
            self.execute(self.principal.dispense, volume=volume, speed=speed)
        except AttributeError:
            logger.warning('No dispense method found')
            self.update()
        self.refresh()
        return
    
    def empty(self, speed:float|None = None):
        try:
            speed = float(speed)
        except ValueError:
            if isinstance(speed, str) and speed=='None':
                speed = None
            else:
                logger.warning('Ensure input for speed is of type float')
        self.volume = 0
        try:
            self.execute(self.principal.empty, speed=speed)
        except AttributeError:
            logger.warning('No empty method found')
            self.update()
        self.refresh()
        return
    
    def fill(self, speed:float|None = None, reagent:str|None = None):
        try:
            speed = float(speed)
        except ValueError:
            if isinstance(speed, str) and speed=='None':
                speed = None
            else:
                logger.warning('Ensure input for speed is of type float')
        self.volume = self.capacity
        self.reagent = reagent
        try:
            self.execute(self.principal.fill, speed=speed, reagent=reagent)
        except AttributeError:
            logger.warning('No fill method found')
            self.update()
        self.refresh()
        return
    
    def volumeTo(self, volume:float, speed:float|None = None):
        current_volume = self.volume
        return self.aspirate(volume=volume, speed=speed) if (volume - current_volume) > 0 else self.dispense(volume=volume, speed=speed)
