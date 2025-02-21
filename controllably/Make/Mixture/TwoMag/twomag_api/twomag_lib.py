# -*- coding: utf-8 -*-
"""This module holds the references for QInstruments firmware."""
# Standard library imports
from enum import Enum

class ErrorCodes(Enum):
    er1 = "Unknown Command"
    er2 = "Manual Mode (Start, Stop not possible)"
    er3 = "Parameter out of range (set value not allowed)"
    
