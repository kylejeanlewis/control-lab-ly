# %% -*- coding: utf-8 -*-
"""
This module holds the references for pipette tools from Sartorius.

Attributes:
    QUERIES (list): List of all query codes available for the pipette

Classes:
    `ErrorCode`: Enum for error codes returned by the pipette
    `Model`: Enum for pipette models, each containing a `ModelInfo` dataclass
    `StaticQueryCode`: Enum for static query codes
    `StatusCode`: Enum for status codes returned by the pipette
    `StatusQueryCode`: Enum for status query codes
    `ModelInfo`: Dataclass representing a pipette model with its specifications
"""
# Standard library imports
from dataclasses import dataclass
from enum import Enum

@dataclass
class ModelInfo:
    """
    ModelInfo dataclass represents a single model of pipette from Sartorius
    
    ### Constructor
    Args:
        name (str): model name
        capacity (int): capacity of pipette
        home_position (int): home position of pipette
        max_position (int): maximum position of pipette
        tip_eject_position (int): tip eject position of pipette
        resolution (float): volume resolution of pipette (i.e. uL per step)
        preset_speeds (PresetSpeeds): preset speeds of pipette
    """
    
    name: str
    capacity: int
    home_position: int
    max_position: int
    tip_eject_position: int 
    resolution: float
    preset_speeds: tuple[int|float]

class ErrorCode(Enum):
    er1 = 'The command has not been understood by the module'
    er2 = 'The command has been understood but would result in out-of-bounds state'
    er3 = 'LRC is configured to be used and the checksum does not match'
    er4 = 'The drive is on and the command or query cannot be answered'
    
class Model(Enum):
    BRL0        = ModelInfo('BRL0',0,30,443,-40,0.5,(60,106,164,260,378,448))
    BRL200      = ModelInfo('BRL200',200,30,443,-40,0.5,(31,52,80,115,150,190))
    BRL1000     = ModelInfo('BRL1000',1000,30,443,-40,2.5,(150,265,410,650,945,1120))
    BRL5000     = ModelInfo('BRL5000',5000,30,580,-55,10,(550,1000,1500,2500,3650,4350))

class StatusCode(Enum):
    Normal          = 0
    Braking         = 1
    Running         = 2
    Drive_Busy      = 4
    Running_Busy    = 6
    General_Error   = 8
    
class StaticQueryCode(Enum):
    DV  = 'Version'
    DM  = 'Model'
    DX  = 'Cycles'
    DI  = 'Speed In'
    DO  = 'Speed_Out'
    DR  = 'Resolution'
    
class StatusQueryCode(Enum):
    DS  = 'Status'
    DE  = 'Errors'
    DP  = 'Position'
    DN  = 'Liquid Sensor'

QUERIES = StatusQueryCode._member_names_ + StaticQueryCode._member_names_
"""List of all query codes"""
