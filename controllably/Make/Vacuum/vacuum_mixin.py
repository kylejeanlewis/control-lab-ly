# -*- coding: utf-8 -*-
"""
This module contains the VacuumMixin class.

## Classes:
    `VacuumMixin`: Mixin class for vacuum control
    
<i>Documentation last updated: 2024-11-14</i>
"""
# Standard library imports
from __future__ import annotations
import logging
import time

logger = logging.getLogger("controllably.Make")
logger.debug(f"Import: OK <{__name__}>")

class VacuumMixin:
    """
    Mixin class for vacuum control
    
    ### Methods
        `evacuate`: Evacuate to create vacuum
        `vent`: Vent to release vacuum
        `toggleVacuum`: Toggle vacuum
    """
    
    def __init__(self):
        """Initialize VacuumMixin class"""
        super().__init__()
        return
    
    def evacuate(self):
        """Evacuate to create vacuum"""
        logger.warning("Pulling vacuum")
        self.toggleVacuum(True)
        time.sleep(3)
        return
    
    def vent(self):
        """Vent to release vacuum"""
        logger.warning("Venting vacuum")
        self.toggleVacuum(False)
        time.sleep(3)
        return
    
    def toggleVacuum(self, on:bool):
        """Toggle vacuum"""
        raise NotImplementedError
    