# -*- coding: utf-8 -*-
"""This module holds the references for QInstruments firmware."""
# Standard library imports
from enum import Enum

class ErrorCode(Enum):
    er1 = "Unknown Command"
    er2 = "Manual Mode (Start, Stop not possible)"
    er3 = "Parameter out of range (set value not allowed)"
    
class MIXdrive(Enum):
    MTP6 = 6
    MTP12 = 12
    MTP24 = 24
    MTP96 = 96
