# %% -*- coding: utf-8 -*-
"""
This module holds the class for electrical measurement tools.

Classes:
    Electrical (Programmable)
"""
# Standard library imports
import logging

# Local application imports
from ..measure_utils import Programmable

logger = logging.getLogger(__name__)
logger.debug(f"Import: OK <{__name__}>")

class Electrical(Programmable):
    ...
    