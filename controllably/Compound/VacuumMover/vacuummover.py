# -*- coding: utf-8 -*-
"""
This module holds the class for liquid mover setups.

Classes:
    LiquidMoverSetup (CompoundSetup)
"""
# Standard library imports
from __future__ import annotations
from types import SimpleNamespace
from typing import Sequence

# Local application imports
from ...Make.Vacuum import VacuumMixin
from ...Move.Cartesian import Gantry
from ...core.position import Position, Deck

class VacuumGantry(VacuumMixin, Gantry):
    _default_flags = SimpleNamespace(busy=False, verbose=False, vented=True)
    def __init__(self, 
        port: str,
        limits: Sequence[Sequence[float]] = ((0,0,0),(0,0,0)),          # in terms of robot coordinate system
        vacuum_on_delay: float = 3,
        vacuum_off_delay: float = 3,
        *, 
        robot_position: Position = Position(),
        home_position: Position = Position(),                           # in terms of robot coordinate system
        tool_offset: Position = Position(),
        calibrated_offset: Position = Position(),
        scale: float = 1.0,
        deck: Deck|None = None,
        safe_height: float|None = None,                                 # in terms of robot coordinate system
        speed_max: float|None = None,                                   # in mm/min
        device_type_name: str = 'GRBL',
        baudrate: int = 115200, 
        movement_buffer: int|None = None,
        movement_timeout: int|None = None,
        verbose: bool = False, 
        simulation: bool = False,
        **kwargs
    ):
        super().__init__(
            port=port, baudrate=baudrate, limits=limits,
            robot_position=robot_position, home_position=home_position,
            tool_offset=tool_offset, calibrated_offset=calibrated_offset, scale=scale, 
            deck=deck, safe_height=safe_height, speed_max=speed_max, 
            device_type_name=device_type_name, movement_buffer=movement_buffer, 
            movement_timeout=movement_timeout, verbose=verbose, simulation=simulation,
            message_end='\r\n',
            **kwargs
        )
        self.vacuum_delays = dict(on=vacuum_on_delay, off=vacuum_off_delay)
        return
    
    # VacuumMixin methods
    def toggleVacuum(self, on:bool):
        return self.toggleCoolantValve(on=on)
    
    def evacuate(self):
        super().evacuate(self.vacuum_delays.get('on',5))
        self.flags.vented = False
        return
    
    def vent(self):
        super().vent(self.vacuum_delays.get('off',5))
        self.flags.vented = True
        return

    # Combined methods
    def reset(self):
        self.vent()
        return super().reset()
    
    def shutdown(self):
        self.vent()
        return super().shutdown()
