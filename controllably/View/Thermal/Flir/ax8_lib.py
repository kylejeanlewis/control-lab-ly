# %% -*- coding: utf-8 -*-
"""
This module holds the references for AX8 cameras from FLIR.

Classes:
    SpotmeterRegs (Enum)
    
Functions:
    parse_value
    value_to_modbus
"""
# Standard library imports
from __future__ import annotations
from enum import IntEnum
import struct
from typing import Union
print(f"Import: OK <{__name__}>")

class SpotmeterRegs(IntEnum):
    UNIT_ID             = 108
    ENABLE_LOCAL_PARAMS = 0 * 20
    REFLECTED_TEMP      = 1 * 20
    EMISSIVITY          = 2 * 20
    DISTANCE            = 3 * 20
    ENABLE_SPOTMETER    = 4 * 20
    SPOT_X_POSITION     = 5 * 20
    SPOT_Y_POSITION     = 6 * 20
    SPOT_TEMPERATURE    = 7 * 20
    SPOT_TEMP_STATE     = 8 * 20

def parse_value(data:list[Union[float, int]]):
    form = 'i' if type(data[0]) is int else 'f'
    val = data[1].to_bytes(2, 'little') + data[0].to_bytes(2, 'little')
    return struct.unpack(form, val)

def value_to_modbus(value:Union[float, int]):
    form = 'i' if type(value) is int else '<f'
    packed = struct.pack(form, value)
    ff = [int((packed[3:4] + packed[2:3]).hex(), 16), int((packed[1:2] + packed[0:1]).hex(), 16)]
    return [4] + ff[::-1] + [4] + ff

# def float_to_modbus(val:float):
#     packed = struct.pack('<f', val)
#     ff = [int((packed[3:4] + packed[2:3]).hex(), 16), int((packed[1:2] + packed[0:1]).hex(), 16)]
#     return [4] + ff[::-1] + [4] + ff

# def int_to_modbus(val:int):
#     packed = struct.pack('i', val)
#     ff = [int((packed[3:4] + packed[2:3]).hex(), 16), int((packed[1:2] + packed[0:1]).hex(), 16)]
#     return [4] + ff[::-1] + [4] + ff

# def parse_float(data:list):
#     val = data[1].to_bytes(2, 'little') + data[0].to_bytes(2, 'little')
#     return struct.unpack('f', val)

# def parse_int(data:list):
#     val = data[1].to_bytes(2, 'little') + data[0].to_bytes(2, 'little')
#     return struct.unpack('i', val)
