# %% -*- coding: utf-8 -*-
"""
This module holds the references for AX8 cameras from FLIR.

## Classes:
    `SpotMeterRegs`: Contains register addresses for the spot meter functionality.
    `BoxRegs`: Contains register addresses for the box functionality.
    
<i>Documentation last updated: 2025-02-22</i>
"""
# Standard library imports
from __future__ import annotations
from enum import IntEnum

class SpotMeterRegs(IntEnum):
    UNIT_ID             = int('6C', base=16)
    ENABLE_LOCAL_PARAMS = (1-1) * 20
    REFLECTED_TEMP      = (2-1) * 20
    EMISSIVITY          = (3-1) * 20
    DISTANCE            = (4-1) * 20
    ENABLE_SPOTMETER    = (5-1) * 20
    SPOT_X_POSITION     = (6-1) * 20
    SPOT_Y_POSITION     = (7-1) * 20
    SPOT_TEMPERATURE    = (8-1) * 20
    SPOT_TEMP_STATE     = (9-1) * 20

class BoxRegs(IntEnum):
    UNIT_ID             = int('6D', base=16)
    ENABLE_LOCAL_PARAMS = ( 1-1) * 20
    REFLECTED_TEMP      = ( 2-1) * 20
    EMISSIVITY          = ( 3-1) * 20
    DISTANCE            = ( 4-1) * 20
    ENABLE_BOX          = ( 5-1) * 20
    BOX_MIN_TEMP        = ( 6-1) * 20
    BOX_MIN_TEMP_STATE  = ( 7-1) * 20
    BOX_MAX_TEMP        = ( 8-1) * 20
    BOX_MAX_TEMP_STATE  = ( 9-1) * 20
    BOX_AVG_TEMP        = (10-1) * 20
    BOX_AVG_TEMP_STATE  = (11-1) * 20
    BOX_X_POSITION      = (12-1) * 20
    BOX_Y_POSITION      = (13-1) * 20
    BOX_MIN_TEMP_X      = (14-1) * 20
    BOX_MIN_TEMP_Y      = (15-1) * 20
    BOX_MAX_TEMP_X      = (16-1) * 20
    BOX_MAX_TEMP_Y      = (17-1) * 20
    BOX_WIDTH           = (18-1) * 20
    BOX_HEIGHT          = (19-1) * 20
    TEMP_DISP_OPTION    = (20-1) * 20


