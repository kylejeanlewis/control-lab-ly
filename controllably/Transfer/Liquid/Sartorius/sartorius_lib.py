# %% -*- coding: utf-8 -*-
"""
Created: Tue 2022/12/09 11:11:00
@author: Chang Jie

Notes / actionables:
-
"""
# Standard library imports
from collections import namedtuple
from dataclasses import dataclass
from enum import Enum

# Local application imports
print(f"Import: OK <{__name__}>")

PresetSpeeds = namedtuple('PresetSpeeds', ['s1','s2','s3','s4','s5','s6'])
SpeedParameters = namedtuple('SpeedParameters', ['preset', 'intervals', 'step_size', 'delay'])

@dataclass
class Model:
    name: str
    capacity: int
    home_position: int
    max_position: int
    tip_eject_position: int 
    resolution: float
    preset_speeds: PresetSpeeds

class ErrorCode(Enum):
    er1 = 'The command has not been understood by the module'
    er2 = 'The command has been understood but would result in out-of-bounds state'
    er3 = 'LRC is configured to be used and the checksum does not match'
    er4 = 'The drive is on and the command or query cannot be answered'
    
class ModelInfo(Enum):
    BRL0        = Model('BRL0',0,30,443,-40,0.5,PresetSpeeds(60,106,164,260,378,448))
    BRL200      = Model('BRL200',200,30,443,-40,0.5,PresetSpeeds(31,52,80,115,150,190))
    BRL1000     = Model('BRL1000',1000,30,443,-40,2.5,PresetSpeeds(150,265,410,650,945,1120))
    BRL5000     = Model('BRL5000',5000,30,580,-55,10,PresetSpeeds(550,1000,1500,2500,3650,4350))

class StatusCode(Enum):
    Normal          = 0
    Braking         = 1
    Running         = 2
    Drive_Busy      = 4
    Running_Busy    = 6
    General_Error   = 8

class StaticQueryCode(Enum):
    Version         = 'DV'
    Model           = 'DM'
    Cycles          = 'DX'
    Speed_In        = 'DI'
    Speed_Out       = 'DO'
    Resolution      = 'DR'
    
class StatusQueryCode(Enum):
    Status          = 'DS'
    Errors          = 'DE'
    Position        = 'DP'
    Liquid_Sensor   = 'DN'

STATIC_QUERIES  = [static_query.value for static_query in StaticQueryCode]
STATUS_QUERIES  = [status_query.value for status_query in StatusQueryCode]
QUERIES         = STATUS_QUERIES + STATIC_QUERIES
