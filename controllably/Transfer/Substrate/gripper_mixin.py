# -*- coding: utf-8 -*-
# Standard library imports
from __future__ import annotations
import logging

logger = logging.getLogger(__name__)
logger.debug(f"Import: OK <{__name__}>")

class GripperMixin:
    """
    """
    
    def __init__(self):
        """"""
        ...
    
    def drop(self):
        """"""
        logger.warning("Dropping object")
        return self.toggleGrip(False)
    
    def grab(self):
        """"""
        logger.warning("Grabbing object")
        return self.toggleGrip(True)
    
    def toggleGrip(self, on:bool):
        """"""
        raise NotImplementedError
    