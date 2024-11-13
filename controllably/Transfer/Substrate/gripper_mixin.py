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
        raise NotImplementedError
    
    def grab(self):
        """"""
        logger.warning("Grabbing object")
        raise NotImplementedError
    
    def toggleGrip(self, on:bool):
        """"""
        _ = self.grab() if on else self.drop()
        return
    