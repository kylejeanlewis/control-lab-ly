# -*- coding: utf-8 -*-
"""
Tables containing the Modbus register mappings for different modules
"""

SPOTMETER_REGS = {
    'UNIT_ID'                   :   0x6C,
    'ENABLE_LOCAL_PARAMS'       :   (1 - 1) * 20,
    'REFLECTED_TEMP'            :   (2 - 1) * 20,
    'EMISSIVITY'                :   (3 - 1) * 20,
    'DISTANCE'                  :   (4 - 1) * 20,
    'ENABLE_SPOTMETER'          :   (5 - 1) * 20,
    'SPOT_X_POSITION'           :   (6 - 1) * 20,
    'SPOT_Y_POSITION'           :   (7 - 1) * 20,
    'SPOT_TEMPERATURE'          :   (8 - 1) * 20,
    'SPOT_TEMP_STATE'           :   (9 - 1) * 20,
    }
