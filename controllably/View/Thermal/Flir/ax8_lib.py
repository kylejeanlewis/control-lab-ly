# %% -*- coding: utf-8 -*-
"""
This module holds the references for AX8 cameras from FLIR.

Classes:
    BoxRegs (Enum)
    SpotmeterRegs (Enum)
    
Functions:
    decode_from_modbus
    encode_to_modbus
"""
# Standard library imports
from __future__ import annotations
from enum import IntEnum
import struct
from typing import Union
print(f"Import: OK <{__name__}>")

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

class SpotmeterRegs(IntEnum):
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

def decode_from_modbus(data:list[int], is_int:bool) -> tuple:
    """
    Parse values from reading modbus holding registers

    Args:
        data (list[int]): data packet
        is_int (bool): whether the expected value is an integer (as opposed to a float)

    Returns:
        tuple: _description_
    """
    form = ">i" if is_int else ">f"
    value = data[0].to_bytes(2, 'big') + data[1].to_bytes(2, 'big')
    return struct.unpack(form, value)

def encode_to_modbus(value:Union[bool, float, int]) -> list[int]:
    """
    Format value to create data packet

    Args:
        value (Union[bool, float, int]): target value

    Returns:
        list[int]: data packet
    """
    if type(value) is bool:
        return [1,int(value)]
    byte_size = 4
    form = '>i' if type(value) is int else '>f'
    packed_big = struct.pack(form, value)
    big_endian = [int(packed_big[:2].hex(), base=16), int(packed_big[-2:].hex(), base=16)]
    little_endian = big_endian[::-1]
    return [byte_size] + little_endian + [byte_size] + big_endian
