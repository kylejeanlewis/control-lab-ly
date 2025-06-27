# -*- coding: utf-8 -*-
"""
This module contains the VacuumMixin class.

Attributes:
    VACUUM_ON_DELAY (int): delay for vacuum on
    VACUUM_OFF_DELAY (int): delay for vacuum off

## Classes:
    `VacuumMixin`: Mixin class for vacuum control
    
<i>Documentation last updated: 2025-02-22</i>
"""
# Standard library imports
from __future__ import annotations
import logging
import time

VACUUM_ON_DELAY = 3
VACUUM_OFF_DELAY = 3

class VacuumMixin:
    """
    Mixin class for vacuum control
    
    ### Methods:
        `evacuate`: Evacuate to create vacuum
        `vent`: Vent to release vacuum
        `toggleVacuum`: Toggle vacuum
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        pass
    
    def evacuate(self, wait:float|None = None):
        """
        Evacuate to create vacuum
        
        Args:
            wait (float|None): Time to wait after evacuating. Defaults to None.
        """
        logger: logging.Logger = getattr(self, '_logger', logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}.{id(self)}"))
        logger.warning("Pulling vacuum")
        self.toggleVacuum(True)
        wait = VACUUM_ON_DELAY if wait is None else wait
        time.sleep(wait)
        return
    
    def vent(self, wait:float|None = None):
        """
        Vent to release vacuum
        
        Args:
            wait (float|None): Time to wait after venting. Defaults to None.
        """
        logger: logging.Logger = getattr(self, '_logger', logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}.{id(self)}"))
        logger.warning("Venting vacuum")
        self.toggleVacuum(False)
        wait = VACUUM_OFF_DELAY if wait is None else wait
        time.sleep(wait)
        return
    
    def toggleVacuum(self, on:bool):
        """Toggle vacuum"""
        raise NotImplementedError
    