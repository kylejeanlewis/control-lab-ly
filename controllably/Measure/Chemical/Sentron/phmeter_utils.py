# %% -*- coding: utf-8 -*-
"""
This module holds the class for pH meter probe from Sentron.

Classes:
    SentronProbe (Measurer)
"""
# Standard library imports
from __future__ import annotations
import time

# Third party imports
import serial # pip install pyserial

# Local application imports
from ...measure_utils import Measurer
print(f"Import: OK <{__name__}>")

class SentronProbe(Measurer):
    ...