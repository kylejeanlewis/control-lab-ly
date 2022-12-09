# %% -*- coding: utf-8 -*-
"""
Created: Tue 2022/12/09 11:11:00
@author: Chang Jie

Notes / actionables:
-
"""
# Standard library imports
from enum import Enum

# Third party imports

# Local application imports
print(f"Import: OK <{__name__}>")

class ModelInfo(Enum):
    rLine_0     = dict(
                    resolution=0.5, home_position=30, max_position=443, tip_eject_position=-40,
                    speed_codes = [0,60,106,164,260,378,448]
                )
    rLine_200   = dict(
                    resolution=0.5, home_position=30, max_position=443, tip_eject_position=-40,
                    speed_codes = [0,31,52,80,115,150,190]
                )
    rLine_1000  = dict(
                    resolution=2.5, home_position=30, max_position=443, tip_eject_position=-40,
                    speed_codes = [0,150,265,410,650,945,1120]
                )
    rLine_5000  = dict(
                    resolution=10, home_position=30, max_position=580, tip_eject_position=-55,
                    speed_codes = [0,550,1000,1500,2500,3650,4350]
                )

class ErrorCodes(Enum):
    er1 = 'The command has not been understood by the module'
    er2 = 'The command has been understood but would result in out-of-bounds state'
    er3 = 'LRC is configured to be used and the checksum does not match'
    er4 = 'The drive is on and the command or query cannot be answered'

class SpeedCodes(Enum):
    rLine_0     = [0,60,106,164,260,378,448]
    rLine_200   = [0,31,52,80,115,150,190]
    rLine_1000  = [0,150,265,410,650,945,1120]
    rLine_5000  = [0,550,1000,1500,2500,3650,4350]

# %%
