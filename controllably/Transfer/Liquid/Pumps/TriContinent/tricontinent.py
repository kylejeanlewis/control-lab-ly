# -*- coding: utf-8 -*-
# Standard library imports
from __future__ import annotations
import logging

# Local application imports
from ...liquid import LiquidHandler
from .tricontinent_api import TriContinentDevice

logger = logging.getLogger(__name__)
logger.debug(f"Import: OK <{__name__}>")

class TriContinent(LiquidHandler):
    def __init__(self,
        port: str,
        capacity: float = 1000.0,  # uL
        *,
        channel: int = 1,
        verbose: bool = False,
        simulation: bool = False,
        **kwargs
    ):
        """
        Initialize the TriContinent class.

        Args:
            device (TriContinentDevice): The TriContinent device that is being used.
            volume (float): The volume of the pipette tool.
            step_resolution (int): The step resolution of the pipette tool.
            speed (float): The speed of the pipette tool.
        """
        super().__init__(
            device_type=TriContinentDevice, port=port, channel=channel, 
            verbose=verbose, simulation=simulation, **kwargs
        )
        assert isinstance(self.device, TriContinentDevice), "Ensure device is of type `TriContinentDevice`"
        self.device: TriContinentDevice = self.device
        
        # Category specific attributes
        self.capacity = capacity
        self.channel = self.device.channel
        self.volume_resolution = self.capacity / self.device.max_position
        
        self.pullback_steps = 0
        return
    
    def aspirate(self, 
        volume: float, 
        speed: float|None = None, 
        reagent: str|None = None,
        *,
        start_speed: int = 50,
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
            delay (int, optional): time delay after aspirate. Defaults to 0.
            pause (bool, optional): whether to pause for user intervention. Defaults to False.
            reagent (str|None, optional): name of reagent. Defaults to None.
            channel (Optional[Union[int, tuple[int]]], optional): channel id. Defaults to None.

        Returns:
            bool: whether the action is successful
        """
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
        
        # Replace with actual aspirate implementation
        steps = round(volume/self.volume_resolution)
        self.device.setStartSpeed(start_speed, immediate=False)
        self.device.setTopSpeed(speed, immediate=False)
        self.device.setAcceleration(2500, immediate=False)
        self.device.aspirate(steps, immediate=False, blocking=blocking)
        self.device.wait(delay, immediate=False)
        self.device.run()
        
        # Update values
        # time.sleep(delay)
        # self.volume = min(self.volume + volume, self.capacity)
        self.volume = self.device.position * self.volume_resolution
        if pause:
            input("Press 'Enter' to proceed.")
        return
    
    def dispense(self, 
        volume: float, 
        speed: float|None = None, 
        *,
        start_speed: int = 50,
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
            delay (int, optional): time delay after dispense. Defaults to 0.
            pause (bool, optional): whether to pause for user intervention. Defaults to False.
            blowout (bool, optional): whether perform blowout. Defaults to False.
            ignore (bool, optional): whether to dispense reagent regardless. Defaults to False.
            channel (Optional[Union[int, tuple[int]]], optional): channel id. Defaults to None.

        Returns:
            bool: whether the action is successful
        """
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
        speed = speed or self.speed_out
        
        # Replace with actual dispense implementation
        steps = round(volume/self.volume_resolution)
        self.device.setStartSpeed(start_speed, immediate=False)
        self.device.setTopSpeed(speed, immediate=False)
        self.device.setAcceleration(2500, immediate=False)
        if volume > self.volume and not ignore:
            self.device.setValvePosition('I', immediate=False)
            self.device.moveTo(self.device.max_position, immediate=False)
        self.device.dispense(steps, immediate=False, blocking=blocking)
        self.device.wait(delay, immediate=False)
        self.device.run()
        
        # Update values
        # time.sleep(delay)
        # self.volume = max(self.volume - volume, 0)
        self.volume = self.device.position * self.volume_resolution
        if pause:
            input("Press 'Enter' to proceed.")
        return
    
    def home(self):
        """
        Home the pump.
        """
        self.device.initialize(self.device.output_right)
        return
    
    def setSpeed(self, speed: float):
        """
        Set the speed of the pump.

        Args:
            speed (float): The speed of the pump.
        """
        self.device.setTopSpeed(round(speed/self.volume_resolution))
        return
    
    def reverse(self):
        """
        Reverse the pump.
        """
        self.device.reverse()
        return