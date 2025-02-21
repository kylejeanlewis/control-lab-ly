# -*- coding: utf-8 -*-
"""
"""
# Standard library imports
from __future__ import annotations

# Local application imports
from ...make_utils import Maker
from .twomag_api import TwoMagDevice, MIXdrive

class TwoMagStirrer(Maker):
    def __init__(self, 
        port: str, 
        address: str = 'A', 
        model: str = MIXdrive.MTP6,
        *,
        verbose: bool = False, 
        simulation: bool = False, 
        **kwargs
    ):
        super().__init__(device_type=TwoMagDevice, port=port, verbose=verbose, simulation=simulation, **kwargs)
        assert isinstance(self.device, TwoMagDevice), "Ensure device is of type `TwoMagDevice`"
        self.device: TwoMagDevice = self.device
        
        self.address = address
        self.model = model
        self.connect()
        if self.address != self.device.address:
            self.device.setAddress(self.address)
        return
    
    @property
    def power(self) -> int:
        return self.device.power
    
    @property
    def speed(self) -> int:
        return self.device.speed
    
    def getPower(self) -> int:
        return self.device.getPower()
    
    def getSpeed(self) -> int:
        return self.device.getSpeed()
    
    def getStatus(self) -> tuple[str,str]:
        return self.device.getStatus()
    
    def setDefault(self) -> bool:
        return self.device.setDefault()
    
    def setPower(self, power:int) -> int:
        return self.device.setPower(power)
    
    def setSpeed(self, speed:int) -> int:
        if self.model == MIXdrive.MTP96:
            if self.power != 100:
                self.setPower(100)
        elif self.speed >= 1400 and self.power < 50:
            self.setPower(50)
        return self.device.setSpeed(speed)
    
    def start(self) -> bool:
        return self.device.start()
    
    def stop(self) -> bool:
        return self.device.stop()
    