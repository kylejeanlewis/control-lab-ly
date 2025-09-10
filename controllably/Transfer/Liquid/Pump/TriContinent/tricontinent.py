# -*- coding: utf-8 -*-
""" 
This module provides a class for handling TriContinent pumps.

## Classes:
    `TriContinent`: Class for handling TriContinent pumps.
    `Multi_TriContinent`: Class for handling multiple TriContinent pumps.
    `Parallel_TriContinent`: Class for handling multiple TriContinent pumps in parallel.

<i>Documentation last updated: 2025-02-22</i>
"""
# Standard library imports
from __future__ import annotations
import time

# Local application imports
from .....core.compound import Multichannel, Ensemble
from ...liquid import LiquidHandler
from .tricontinent_api import TriContinentDevice

class TriContinent(LiquidHandler):
    """
    TriContinent class for handling TriContinent pumps.
    
    ### Constructor:
        `port` (str): The port of the pump.
        `capacity` (float, optional): The capacity of the pump. Defaults to 1000.0.
        `channel` (int, optional): The channel of the pump. Defaults to 1.
        `verbose` (bool, optional): Whether to output extra information. Defaults to False.
        `simulation` (bool, optional): Whether to simulate the pump. Defaults to False.
        
    ### Attributes and properties:
        `capacity` (float): The capacity of the pump.
        `channel` (int): The channel of the pump.
        `volume_resolution` (float): The volume resolution of the pump.
        `pullback_steps` (int): The number of pullback steps.
        `speed_in` (int): The speed of the pump when aspirating.
        `speed_out` (int): The speed of the pump when dispensing.
        `start_speed` (int): The start speed of the pump.
        `acceleration` (int): The acceleration of the pump.
        `valve_position` (str): The valve position of the pump.
        `init_status` (bool): The initialization status of the pump.
        
    ### Methods:
        `connect`: Connect to the pump.
        `aspirate`: Aspirate desired volume of reagent.
        `dispense`: Dispense desired volume of reagent.
        `getState`: Get the settings of the pump.
        `home`: Home the pump.
        `setSpeed`: Set the speed of the pump.
        `reverse`: Reverse the pump.
        `setChannel`: Set the channel
        `disconnect`: Disconnect from the device
        `resetFlags`: Reset all flags to to default
        `shutdown`: Shutdown procedure for tool
        `cycle`: Cycle between aspirate and dispense
        `empty`: Empty the channel
        `fill`: Fill the channel
        `rinse`: Rinse the channel with aspirate and dispense cycles
    """
    
    def __init__(self,
        port: str,
        capacity: float = 1000.0,  # uL
        *,
        output_right: bool,
        channel: int = 1,
        verbose: bool = False,
        simulation: bool = False,
        **kwargs
    ):
        """
        Initialize the TriContinent class.

        Args:
            port (str): The port of the pump.
            capacity (float, optional): The capacity of the pump. Defaults to 1000.0.
            output_right (bool): Whether the output valve is to the right.
            channel (int, optional): The channel of the pump. Defaults to 1.
            verbose (bool, optional): Whether to output extra information. Defaults to False.
            simulation (bool, optional): Whether to simulate the pump. Defaults to False.
        """
        super().__init__(
            device_type=TriContinentDevice, port=port, channel=channel, 
            verbose=verbose, simulation=simulation, **kwargs
        )
        assert isinstance(self.device, TriContinentDevice), "Ensure device is of type `TriContinentDevice`"
        self.device: TriContinentDevice = self.device
        
        # Category specific attributes
        self.capacity = capacity
        self.channel = channel
        self.volume_resolution = self.capacity / self.device.max_position
        self.pullback_steps = 0
        
        self.speed_in = self.device.speed
        self.speed_out = self.device.speed
        self.output_right = output_right

        self.connect()
        return
    
    @property
    def volume(self) -> float:
        return self.device.position * self.volume_resolution
    
    @property
    def start_speed(self) -> int|str:
        """Start speed of the pump"""
        self.setChannel()
        return self.device.start_speed
    
    @property
    def acceleration(self) -> int|str:
        """Acceleration of the pump"""
        self.setChannel()
        return self.device.acceleration
    
    @property
    def valve_position(self) -> str|None:
        """Valve position of the pump"""
        self.setChannel()
        return self.device.valve_position
    
    @property
    def init_status(self) -> bool|str:
        """Initialization status of the pump"""
        self.setChannel()
        return self.device.init_status
    
    def connect(self):
        super().connect()
        self.getState()
        return
    
    def aspirate(self, 
        volume: float, 
        speed: float|None = None, 
        reagent: str|None = None,
        *,
        start_speed: int|None = None,
        pullback: bool = False,
        delay: int = 0, 
        pause: bool = False, 
        ignore: bool = False,
        blocking: bool = True,
        **kwargs
    ) -> bool:
        """
        Aspirate desired volume of reagent

        Args:
            volume (float): target volume
            speed (float|None, optional): speed to aspirate at. Defaults to None.
            reagent (str|None, optional): name of reagent. Defaults to None.
            start_speed (int|None, optional): start speed of the pump. Defaults to None.
            pullback (bool, optional): whether to perform pullback. Defaults to False.
            delay (int, optional): time delay after aspirate. Defaults to 0.
            pause (bool, optional): whether to pause for user intervention. Defaults to False.
            ignore (bool, optional): whether to aspirate reagent regardless. Defaults to False.
            blocking (bool, optional): whether to block the thread until the action is complete. Defaults to True.

        Returns:
            bool: whether the action is successful
        """
        self.setChannel()
        if (reagent and self.reagent) and reagent != self.reagent:
            self._logger.warning(f"Reagent {reagent} does not match current reagent {self.reagent}.")
            return False
        if volume > (self.capacity - self.volume) and ignore:
            volume = self.capacity - self.volume
            self._logger.warning("Volume exceeds capacity. Aspirating up to capacity.")
        elif volume > (self.capacity - self.volume):
            self._logger.warning("Volume exceeds capacity.")
            return False
        if volume < self.volume_resolution and not ignore:
            self._logger.warning("Volume is too small. Ensure volume is greater than resolution.")
            return False
        volume = round(volume/self.volume_resolution)*self.volume_resolution
        speed = speed or self.speed_in
        start_speed = start_speed or self.start_speed
        
        # Replace with actual aspirate implementation
        steps = round(volume/self.volume_resolution)
        _ = self.device.setStartSpeed(start_speed, immediate=False) if start_speed else None
        _ = self.device.setTopSpeed(speed, immediate=False) if speed else None
        # self.device.setAcceleration(self.acceleration, immediate=False)
        self.device.aspirate(steps, immediate=False, blocking=blocking)
        self.device.wait(delay, immediate=False)
        self.device.run()
        
        # Update values
        time.sleep(delay)
        # self.volume = min(self.volume + volume, self.capacity)
        # self.volume = self.device.position * self.volume_resolution
        if pause:
            input("Press 'Enter' to proceed.")
        return True
    
    def dispense(self, 
        volume: float, 
        speed: float|None = None, 
        *,
        start_speed: int|None = None,
        blowout: bool = False,
        delay: int = 0, 
        pause: bool = False, 
        ignore: bool = False,
        blocking: bool = True,
        **kwargs
    ) -> bool:
        """
        Dispense desired volume of reagent

        Args:
            volume (float): target volume
            speed (float|None, optional): speed to dispense at. Defaults to None.
            start_speed (int|None, optional): start speed of the pump. Defaults to None.
            blowout (bool, optional): whether perform blowout. Defaults to False.
            delay (int, optional): time delay after dispense. Defaults to 0.
            pause (bool, optional): whether to pause for user intervention. Defaults to False.
            ignore (bool, optional): whether to dispense reagent regardless. Defaults to False.
            blocking (bool, optional): whether to block the thread until the action is complete. Defaults to True.

        Returns:
            bool: whether the action is successful
        """
        self.setChannel()
        if volume > self.capacity:
            self._logger.warning("Volume exceeds maximum capacity.")
            return False
        if volume > self.volume and ignore:
            volume = self.volume
            self._logger.warning("Volume exceeds available volume. Dispensing up to available volume.")
        elif volume > self.volume:
            self._logger.warning("Volume exceeds available volume. Pump will refill before dispensing")
        if volume < self.volume_resolution and not ignore:
            self._logger.warning("Volume is too small. Ensure volume is greater than resolution.")
            return False
        volume = round(volume/self.volume_resolution)*self.volume_resolution
        # speed = speed or self.speed_out
        # start_speed = start_speed or self.start_speed
        
        # Replace with actual dispense implementation
        steps = round(volume/self.volume_resolution)
        _ = self.device.setStartSpeed(start_speed, immediate=False) if start_speed else None
        _ = self.device.setTopSpeed(speed, immediate=False) if speed else None
        # self.device.setAcceleration(self.acceleration, immediate=False)
        if volume > self.volume and not ignore:
            self.device.setValvePosition('I', immediate=False)
            self.device.moveTo(self.device.max_position, immediate=False)
        self.device.dispense(steps, immediate=False, blocking=blocking)
        self.device.wait(delay, immediate=False)
        self.device.run()
        
        # Update values
        time.sleep(delay)
        # self.volume = max(self.volume - volume, 0)
        # self.volume = self.device.position * self.volume_resolution
        if pause:
            input("Press 'Enter' to proceed.")
        return True
    
    def getState(self) -> dict[str, int|str|bool]:
        """
        Get the settings of the pump.
        
        Returns:
            dict[str, int|str|bool]: The settings of the pump.
        """
        self.setChannel()
        state = self.device.getState()
        speed = state['speed']
        self.speed_in = self.speed_in or speed
        self.speed_out = self.speed_out or speed
        return state
    
    def home(self):
        """Home the pump."""
        self.setChannel()
        self.device.initialize(self.device.output_right)
        # self.volume = self.device.position * self.volume_resolution
        return
    
    def setSpeed(self, speed: float):
        """
        Set the speed of the pump.

        Args:
            speed (float): The speed of the pump.
        """
        self.setChannel()
        self.device.setTopSpeed(round(speed/self.volume_resolution))
        return
    
    def reverse(self):
        """Reverse the pump."""
        self.setChannel()
        self.device.reverse()
        return
    
    def setChannel(self):
        """Set the channel of the pump."""
        self.device.setChannel(self.channel)
        self.device.output_right = self.output_right
        # if self.channel != self.device.channel:
        #     self.device.setChannel(self.channel)
        #     self.device.output_right = self.output_right
        return
    
Multi_TriContinent = Multichannel.factory(TriContinent)
Parallel_TriContinent = Ensemble.factory(TriContinent)
