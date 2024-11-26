# -*- coding: utf-8 -*-
"""
This module contains the GripperMixin class.

Attributes:
    GRIPPER_ON_DELAY (int): delay for gripper on
    GRIPPER_OFF_DELAY (int): delay for gripper off

## Classes:
    `GripperMixin`: Mixin class for gripper control
    
<i>Documentation last updated: 2024-11-19</i>
"""
# Standard library imports
from __future__ import annotations
import logging
import time

logger = logging.getLogger(__name__)
logger.debug(f"Import: OK <{__name__}>")

GRIPPER_ON_DELAY = 0
GRIPPER_OFF_DELAY = 0

class GripperMixin:
    """
    Mixin class for vacuum control
    
    ### Constructor
        `gripper_on_delay (int|float)`: delay for gripper on. Defaults to 0.
        `gripper_off_delay (int|float)`: delay for gripper off. Defaults to 0.
    
    ### Attributes
        `gripper_delays` (dict): delays for gripper control
    
    ### Methods
        `drop`: Drop to release object
        `grab`: Grab to secure object
        `toggleGrip`: Toggle grip
    """
    
    def __init__(self, *, gripper_on_delay:int|float = 0, gripper_off_delay:int|float = 0, **kwargs):
        """
        Initialize GripperMixin class
        
        Args:
            gripper_on_delay (int|float): delay for gripper on. Defaults to 0.
            gripper_off_delay (int|float): delay for gripper off. Defaults to 0.
        """
        super().__init__()
        self.gripper_delays = dict(on=gripper_on_delay, off=gripper_off_delay)
        logger.debug("GripperMixin initialized")
        return
    
    def drop(self, wait:float|None = None):
        """
        Drop to release object
        
        Args:
            wait (float|None): Time to wait after dropping. Defaults to None.
        """
        logger.warning("Dropping object")
        self.toggleGrip(False)
        wait = self.gripper_delays["off"] if wait is None else wait
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
        wait = self.gripper_delays["on"] if wait is None else wait
        time.sleep(wait)
        return 
    
    def toggleGrip(self, on:bool):
        """Toggle grip"""
        raise NotImplementedError
    