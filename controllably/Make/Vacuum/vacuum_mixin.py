# -*- coding: utf-8 -*-
# Standard library imports
from __future__ import annotations
import logging
import time

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
        self.toggleVacuum(True)
        time.sleep(3)
        return
    
    def vent(self):
        """"""
        logger.warning("Venting vacuum")
        self.toggleVacuum(False)
        time.sleep(3)
        return
    
    def toggleVacuum(self, on:bool):
        """"""
        raise NotImplementedError
    