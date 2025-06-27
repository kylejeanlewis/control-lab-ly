# -*- coding: utf-8 -*-
"""
This module contains the TwoMagStirrer class, which is a wrapper for the TwoMagDevice class.

## CLasses:
    `TwoMagStirrer`: A class that wraps the TwoMagDevice class and provides a higher level of abstraction for the 2Mag stirrer.
    
<i>Documentation last updated: 2025-02-22</i>
"""
# Standard library imports
from __future__ import annotations

# Local application imports
from ... import Maker
from .twomag_api import TwoMagDevice, MIXdrive

class TwoMagStirrer(Maker):
    """ 
    2Mag stirrer class
    
    ### Constructor:
        `port` (str): The port to which the device is connected
        `address` (str, optional): The address of the device. Defaults to 'A'.
        `model` (str, optional): The model of the device. Defaults to MIXdrive.MTP6.
        `verbose` (bool, optional): Whether to print out debug information. Defaults to False.
        `simulation` (bool, optional): Whether to simulate the device. Defaults to False.
        
    ### Attributes and properties:
        `address` (str): The address of the device
        `model` (str): The model of the device
        `power` (int): Power of device in percentage
        `speed` (int): Speed of device in RPM
        `connection_details` (dict): connection details for the device
        `device` (Device): device object that communicates with physical tool
        `flags` (SimpleNamespace[str, bool]): flags for the class
        `is_busy` (bool): whether the device is busy
        `is_connected` (bool): whether the device is connected
        `verbose` (bool): verbosity of class
        
    ### Methods:
        `connect`: connect to the device
        `disconnect`: disconnect from the device
        `execute`: execute task
        `resetFlags`: reset all flags to class attribute `_default_flags`
        `run`: alias for `execute()`
        `shutdown`: shutdown procedure for tool
        `getPower`: get the power of the device
        `getSpeed`: get the speed of the device
        `getStatus`: get the status of the device
        `setDefault`: set the device to default
        `setPower`: set the power of the device
        `setSpeed`: set the speed of the device
        `start`: start the device
        `stop`: stop the device
    """
    
    def __init__(self, 
        port: str, 
        address: str = 'A', 
        model: str = MIXdrive.MTP6,
        *,
        verbose: bool = False, 
        simulation: bool = False, 
        **kwargs
    ):
        """ 
        Initialize a TwoMagStirrer object
        
        Args:
            port (str): The port to which the device is connected
            address (str, optional): The address of the device. Defaults to 'A'.
            model (str, optional): The model of the device. Defaults to MIXdrive.MTP6.
            verbose (bool, optional): Whether to print out debug information. Defaults to False.
            simulation (bool, optional): Whether to simulate the device. Defaults to False.
        """
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
        """Power of device in percentage"""
        return self.device.power
    
    @property
    def speed(self) -> int:
        """Speed of device in RPM"""
        return self.device.speed
    
    def getPower(self) -> int:
        """
        Get the power of the device
        
        Returns:
            int: The power of the device in percentage
        """
        return self.device.getPower()
    
    def getSpeed(self) -> int:
        """
        Get the speed of the device
        
        Returns:
            int: The speed of the device in RPM
        """
        return self.device.getSpeed()
    
    def getStatus(self) -> tuple[str,str]:
        """
        Get the status of the device
        
        Returns:
            tuple[str,str]: A tuple containing the status of the device
        """
        return self.device.getStatus()
    
    def setDefault(self) -> bool:
        """
        Set the device to default
        
        Returns:
            bool: Whether the device was set to default
        """
        return self.device.setDefault()
    
    def setPower(self, power:int) -> int:
        """
        Set the power of the device
        
        Args:
            power (int): The power to set the device to
            
        Returns:
            int: The power of the device in percentage
        """
        return self.device.setPower(power)
    
    def setSpeed(self, speed:int) -> int:
        """
        Set the speed of the device
        
        Args:
            speed (int): The speed to set the device to
            
        Returns:
            int: The speed of the device in RPM
        """
        if self.model == MIXdrive.MTP96:
            if self.power != 100:
                self.setPower(100)
        elif self.speed >= 1400 and self.power < 50:
            self.setPower(50)
        return self.device.setSpeed(speed)
    
    def start(self) -> bool:
        """
        Start the device
        
        Returns:
            bool: Whether the device was started
        """
        return self.device.start()
    
    def stop(self) -> bool:
        """
        Stop the device
        
        Returns:
            bool: Whether the device was stopped
        """
        return self.device.stop()
    