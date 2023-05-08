# %% -*- coding: utf-8 -*-
"""
This module holds the references for tools from QInstruments.

Classes:

Other types:

Other constants and variables:
"""
# Standard library imports
from collections import namedtuple
from dataclasses import dataclass
from enum import Enum
print(f"Import: OK <{__name__}>")

class ELMStateCode(Enum):
    es0     = "ELM is moving"
    es1     = "ELM is locked"
    es3     = "ELM is unlocked"
    es9     = "ELM error occurred"

class ELMStateString(Enum):
    ELMUndefined    = "ELM is moving"
    ELMLocked       = "ELM is locked"
    ELMUnlocked     = "ELM is unlocked"
    ELMError        = "ELM error occurred"

class ShakeStateCode(Enum):
    ss0     = "Running"
    ss1     = "Detected a stop command"
    ss2     = "Braking mode"
    ss3     = "Stopped and is locked at home position"
    ss4     = "Manual mode for external control"
    ss5     = "Accelerates"
    ss6     = "Decelerates"
    ss7     = "Decelerates to stop"
    ss8     = "Decelerates to stop at home position"
    ss9     = "Stopped and is not locked"
    ss10    = "State is for service purpose only"
    ss90    = "ECO mode"
    ss99    = "Boot process running"

class ShakeStateString(Enum):
    RUN             = "Running"
    STOP            = "Stopped and is locked at home position"
    ESTOP           = "Emergency Stop"
    RAMPt           = "Accelerates"
    RAMP_           = "Decelerates"
    dec_stop        = "Decelerates to stop"
    dec_stop_home   = "Decelerates to stop at home position"
    stopped         = "Stopped and is not locked"
    aligned         = "State is for service purpose only"
