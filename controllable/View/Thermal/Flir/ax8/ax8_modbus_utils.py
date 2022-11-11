"""
Utilities for Modbus return parsing

Written By : Sharath (IMRE Singapore)
Date       : 23-07-2021
"""

import struct

def parse_float(data:list):
    val = data[1].to_bytes(2, 'little') + data[0].to_bytes(2, 'little')
    return struct.unpack('f', val)

def float_to_modbus(val:float):
    packed = struct.pack('<f', val)
    ff = [int((packed[3:4] + packed[2:3]).hex(), 16), int((packed[1:2] + packed[0:1]).hex(), 16)]
    return [4] + ff[::-1] + [4] + ff

def parse_int(data:list):
    val = data[1].to_bytes(2, 'little') + data[0].to_bytes(2, 'little')
    return struct.unpack('i', val)

def int_to_modbus(val:int):
    packed = struct.pack('i', val)
    ff = [int((packed[3:4] + packed[2:3]).hex(), 16), int((packed[1:2] + packed[0:1]).hex(), 16)]
    return [4] + ff[::-1] + [4] + ff