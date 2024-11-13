# -*- coding: utf-8 -*-
# Standard library imports
from __future__ import annotations
import logging

logger = logging.getLogger(__name__)
logger.debug(f"Import: OK <{__name__}>")

class VacuumMixin:
    """
    """
    
    def __init__(self):
        """"""
        ...
    
    def evacuate(self):
        """"""
        logger.warning("Pulling vacuum")
        raise NotImplementedError
    
    def vent(self):
        """"""
        logger.warning("Venting vacuum")
        raise NotImplementedError
    
    def toggleVacuum(self, on:bool):
        """"""
        _ = self.evacuate() if on else self.vent()
        return
    