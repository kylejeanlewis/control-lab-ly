# -*- coding: utf-8 -*-
"""
This module contains the VacuumMixin class.

Attributes:
    VACUUM_ON_DELAY (int): delay for vacuum on
    VACUUM_OFF_DELAY (int): delay for vacuum off

## Classes:
    `VacuumMixin`: Mixin class for vacuum control
    
<i>Documentation last updated: 2024-11-19</i>
"""
# Standard library imports
from __future__ import annotations
import logging
import time

logger = logging.getLogger("controllably.Make")
logger.debug(f"Import: OK <{__name__}>")

VACUUM_ON_DELAY = 3
VACUUM_OFF_DELAY = 3

class VacuumMixin:
    """
    Mixin class for vacuum control
    
    ### Attributes
        `vacuum_delays` (dict): delays for vacuum control
    
    ### Methods
        `evacuate`: Evacuate to create vacuum
        `vent`: Vent to release vacuum
        `toggleVacuum`: Toggle vacuum
    """
    
    def __init__(self):
        """Initialize VacuumMixin class"""
        super().__init__()
        self.vacuum_delays = dict(on=VACUUM_ON_DELAY, off=VACUUM_OFF_DELAY)
        return
    
    def evacuate(self, wait:float|None = None):
        """
        Evacuate to create vacuum
        
        Args:
            wait (float|None): Time to wait after evacuating. Defaults to None.
        """
        logger.warning("Pulling vacuum")
        self.toggleVacuum(True)
        wait = self.vacuum_delays["on"] if wait is None else wait
        time.sleep(wait)
        return
    
    def vent(self, wait:float|None = None):
        """
        Vent to release vacuum
        
        Args:
            wait (float|None): Time to wait after venting. Defaults to None.
        """
        logger.warning("Venting vacuum")
        self.toggleVacuum(False)
        wait = self.vacuum_delays["off"] if wait is None else wait
        time.sleep(wait)
        return
    
    def toggleVacuum(self, on:bool):
        """Toggle vacuum"""
        raise NotImplementedError
    