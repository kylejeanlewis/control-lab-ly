# %% -*- coding: utf-8 -*-
"""
This module holds the class for shakers from QInstruments.

Classes:
    BioShakeD30 (Maker)
"""
# Standard library imports
from __future__ import annotations
import numpy as np
from threading import Thread
import time

# Third party imports
import serial   # pip install pyserial

# Local application imports
from ....misc import Helper
from ...make_utils import Maker
print(f"Import: OK <{__name__}>")

class BioShakeD30(Maker):
    ...
