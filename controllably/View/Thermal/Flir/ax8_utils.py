# %% -*- coding: utf-8 -*-
"""
WIP: This module holds the class for thermal cameras by FLIR.

Classes:
    Thermal (Camera)
"""
# Standard library imports
from __future__ import annotations
import numpy as np

# Third party imports
from pyModbusTCP.client import ModbusClient # pip install pyModbusTCP

# Local application imports
from ...view_utils import Camera
from ..thermal_utils import Thermal
print(f"Import: OK <{__name__}>")

class AX8(Camera):
    def __init__(self,
        ip_address: str, 
        encoding: str = "avc", 
        overlay: bool = False, 
        verbose: bool = True
    ):
        
        
        self.verbose = verbose
        return
    
    def getInternalTemperature(self):
        return
    
    def configureSpotmeter(self):
        return
    
    def enableSpotmeter(self):
        return
    
    def disableSpotmeter(self):
        return
    
    def getSpotTemperatures(self):
        return
    
    def getSpotPositions(self):
        return
    
    def getCutline(self):
        return
    
    # Protected methods
    def _connect(self, ip_address:str):
        modbus = None
        self.connection_details = dict(ip_address=ip_address)
        try:
            modbus = ModbusClient(
                host=ip_address, port=502,
                auto_open=True, auto_close=True
            )
        except Exception as e:
            print("Unable to establish Modbus TCP! Error-", str(e))
        else:
            self.device = modbus
            self.getInternalTemperature()
            self.setFlag(connected=True)
            if self.verbose:
                print(f"Established Modbus TCP at: {modbus.host}")
        return
    def _read(self) -> tuple[bool, np.ndarray]:
        return super()._read()
    