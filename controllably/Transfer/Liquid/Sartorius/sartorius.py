# -*- coding: utf-8 -*-
"""
This module holds the class for pipette tools from Sartorius.

Classes:
    Sartorius (LiquidHandler)

Other constants and variables:
    STEP_RESOLUTION (int)
"""
# Standard library imports
from __future__ import annotations
import logging

# Local application imports
from ..liquid import LiquidHandler
from .sartorius_api import SartoriusDevice

_logger = logging.getLogger("controllably.Transfer")
_logger.debug(f"Import: OK <{__name__}>")

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
logger.addHandler(handler)

class Sartorius(LiquidHandler):
    """
    Class for Sartorius pipette tools.

    This class is a subclass of LiquidHandler and is specifically designed to
    handle Sartorius pipette tools.

    Attributes:
        device (SartoriusDevice): The Sartorius device that is being used.
        volume (float): The volume of the pipette tool.
        step_resolution (int): The step resolution of the pipette tool.
        speed (float): The speed of the pipette tool.
    """

    def __init__(self,
        port: str,
        *,
        channel: int = 1,
        verbose: bool = False,
        simulation: bool = False,
        **kwargs
    ):
        """
        Initialize the Sartorius class.

        Args:
            device (SartoriusDevice): The Sartorius device that is being used.
            volume (float): The volume of the pipette tool.
            step_resolution (int): The step resolution of the pipette tool.
            speed (float): The speed of the pipette tool.
        """
        super().__init__(
            device_type=SartoriusDevice, port=port, channel=channel, 
            verbose=verbose, simulation=simulation, **kwargs
        )
        assert isinstance(self.device, SartoriusDevice), "Ensure device is of type `SartoriusDevice`"
        self.device: SartoriusDevice = self.device
        
        # Category specific attributes
        self.speed_in = self.device.preset_speeds[self.device.speed_code_in-1]
        self.speed_out = self.device.preset_speeds[self.device.speed_code_out-1]
        self.capacity = self.device.capacity
        self.channel = self.device.channel
        self.volume_resolution = self.device.volume_resolution
        
        self.pullback_steps = 10
        return

    def aspirate(self, volume: float, speed: float) -> bool:
        """
        Aspirate a certain volume of liquid.

        Args:
            volume (float): The volume of liquid to aspirate.
            speed (float): The speed at which to aspirate the liquid.
        """
        logger.debug(f"Aspirating {volume} uL at {speed} uL/s")
        self.device.aspirate(volume, speed)
        return

    def dispense(self, volume: float, speed: float) -> bool:
        """
        Dispense a certain volume of liquid.

        Args:
            volume (float): The volume of liquid to dispense.
            speed (float): The speed at which to dispense the liquid.
        """
        logger.debug(f"Dispensing {volume} uL at {speed} uL/s")
        self.device.dispense(volume, speed)
        return
        
    def blowout(self, home:bool = True) -> bool:
        """
        Blow out the liquid from the pipette tool.
        """
        logger.debug("Blowing out")
        out = self.device.blowout(home=home)
        return out == 'ok'
    
    def pullback(self) -> bool:
        out = self.device.move(self.pullback_steps)
        return out == 'ok'
    
    def addAirGap(self, steps: int = 10) -> bool:
        out = self.device.move(steps)
        return out == 'ok'
    
    def eject(self) -> bool:
        """
        Eject the tip from the pipette tool.
        """
        logger.debug("Ejecting tip")
        out = self.device.eject()
        return out == 'ok'
        
    def home(self) -> bool:
        """
        Home the pipette tool.
        """
        logger.debug("Homing")
        out = self.device.home()
        return out == 'ok'
        
    def setSpeed(self, speed: int|float):
        """
        Set the speed of the pipette tool.

        Args:
            speed (float): The speed to set the pipette tool to.
        """
        assert abs(speed) in self.device.preset_speeds, f"Speed must be one of {self.device.preset_speeds}"
        logger.debug(f"Setting speed to {speed} uL/s")
        speed_code = self.device.preset_speeds.index(abs(speed))+1
        if speed > 0:
            self.device.setSpeedIn(speed_code)
        else:
            self.device.setSpeedOut(speed_code)
        return
    
    def isTipOn(self) -> bool:
        """
        Check if the tip is on the pipette tool.

        Returns:
            bool: True if the tip is on the pipette tool, False otherwise.
        """
        return self.device.isTipOn()
    