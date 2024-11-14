# -*- coding: utf-8 -*-
"""
This module contains the GripperMixin class.

## Classes:
    `GripperMixin`: Mixin class for gripper control
    
<i>Documentation last updated: 2024-11-14</i>
"""
# Standard library imports
from __future__ import annotations
import logging

logger = logging.getLogger(__name__)
logger.debug(f"Import: OK <{__name__}>")

class GripperMixin:
    """
    Mixin class for vacuum control
    
    ### Methods
        `drop`: Drop to release object
        `grab`: Grab to secure object
        `toggleGrip`: Toggle grip
    """
    
    def __init__(self):
        """Initialize GripperMixin class"""
        super().__init__()
        return
    
    def drop(self):
        """Drop to release object"""
        logger.warning("Dropping object")
        return self.toggleGrip(False)
    
    def grab(self):
        """Grab to secure object"""
        logger.warning("Grabbing object")
        return self.toggleGrip(True)
    
    def toggleGrip(self, on:bool):
        """Toggle grip"""
        raise NotImplementedError
    