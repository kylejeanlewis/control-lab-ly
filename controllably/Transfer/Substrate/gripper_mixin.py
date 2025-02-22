# -*- coding: utf-8 -*-
"""
This module contains the GripperMixin class.

Attributes:
    GRIPPER_ON_DELAY (int): delay for gripper on
    GRIPPER_OFF_DELAY (int): delay for gripper off

## Classes:
    `GripperMixin`: Mixin class for gripper control
    
<i>Documentation last updated: 2025-02-22</i>
"""
# Standard library imports
from __future__ import annotations
import logging
import time

logger = logging.getLogger("controllably.Transfer")
logger.debug(f"Import: OK <{__name__}>")

GRIPPER_ON_DELAY = 0
GRIPPER_OFF_DELAY = 0

class GripperMixin:
    """
    Mixin class for vacuum control
    
    ### Methods
        `drop`: Drop to release object
        `grab`: Grab to secure object
        `toggleGrip`: Toggle grip
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        pass
    
    def drop(self, wait:float|None = None):
        """
        Drop to release object
        
        Args:
            wait (float|None): Time to wait after dropping. Defaults to None.
        """
        logger.warning("Dropping object")
        self.toggleGrip(False)
        wait = GRIPPER_OFF_DELAY if wait is None else wait
        time.sleep(wait)
        return 
    
    def grab(self, wait:float|None = None):
        """
        Grab to secure object
        
        Args:
            wait (float|None): Time to wait after grabbing. Defaults to None
        """
        logger.warning("Grabbing object")
        self.toggleGrip(True)
        wait = GRIPPER_ON_DELAY if wait is None else wait
        time.sleep(wait)
        return 
    
    def toggleGrip(self, on:bool):
        """
        Toggle grip
        
        Args:
            on (bool): True to turn on, False to turn off
        """
        raise NotImplementedError
    