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
import time

# Local application imports
from ..liquid import LiquidHandler
from .sartorius_api import SartoriusDevice, interpolate_speed

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
        tip_inset_mm: int = 12,
        tip_capacitance: int = 276,
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
            tip_inset_mm=tip_inset_mm, tip_capacitance=tip_capacitance,
            verbose=verbose, simulation=simulation, **kwargs
        )
        assert isinstance(self.device, SartoriusDevice), "Ensure device is of type `SartoriusDevice`"
        self.device: SartoriusDevice = self.device
        
        # Category specific attributes
        self.speed_in: int|float = self.device.preset_speeds[self.device.speed_code_in-1]
        self.speed_out: int|float = self.device.preset_speeds[self.device.speed_code_out-1]
        self.capacity = self.device.capacity
        self.channel = self.device.channel
        self.volume_resolution = self.device.volume_resolution
        self.tip_length = 0
        self.pullback_steps = 10
        
        constraints = dict(
            speed_presets=self.device.preset_speeds, volume_resolution=self.volume_resolution,
            step_resolution=self.device.step_resolution, time_resolution=self.device.response_time
        )
        self.speed_interpolation = {(self.capacity,speed): interpolate_speed(self.capacity,speed,**constraints) for speed in self.device.preset_speeds}
        return
    
    # Properties
    @property
    def tip_inset_mm(self) -> float:
        return self.device.tip_inset_mm

    def aspirate(self, 
        volume: float, 
        speed: float|None = None, 
        reagent: str|None = None,
        *,
        pullback: bool = False,
        delay: int = 0, 
        pause: bool = False,
        ignore: bool = False, 
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
        if not self.isTipOn():
            self._logger.warning("Ensure tip is attached.")
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
        
        # Implement actual aspirate function
        constraints = dict(
            speed_presets=self.device.preset_speeds, volume_resolution=self.volume_resolution,
            step_resolution=self.device.step_resolution, time_resolution=self.device.response_time
        )
        parameters = self.speed_interpolation.get((volume,speed), interpolate_speed(volume,speed,**constraints))
        if (volume,speed) not in self.speed_interpolation:
            self.speed_interpolation[(volume,speed)] = parameters
        if parameters['n_intervals'] == 0:
            return False
        if self.speed_in != parameters['preset_speed']:
            self.setSpeed(parameters['preset_speed'], as_default=False)
        
        remaining_steps = round(volume/self.volume_resolution)
        for i in range(parameters['n_intervals']):
            start_time = time.perf_counter()
            step = parameters['step_size'] if (i+1 != parameters['n_intervals']) else remaining_steps
            move_time = step*self.volume_resolution / parameters['preset_speed']
            out = self.device.aspirate(step)
            if out != 'ok':
                return False
            remaining_steps -= step
            sleep_time = max(move_time + delay - (time.perf_counter()-start_time), 0)
            time.sleep(sleep_time)
        
        # Update values
        time.sleep(delay)
        self.volume = min(self.volume + volume, self.capacity)
        if pullback and self.volume < self.capacity:
            self.pullback(**kwargs)
        if pause:
            input("Press 'Enter' to proceed.")
        self.setSpeed(self.speed_in)
        return True

    def dispense(self, 
        volume: float, 
        speed: float|None = None, 
        *,
        blowout: bool = False,
        delay: int = 0, 
        pause: bool = False, 
        ignore: bool = False,
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
        if not self.isTipOn():
            self._logger.warning("Ensure tip is attached.")
            return False
        if volume > self.volume and ignore:
            volume = self.volume
            self._logger.warning("Volume exceeds available volume. Dispensing up to available volume.")
        elif volume > self.volume:
            self._logger.warning("Volume exceeds available volume.")
            return False
        if volume < self.volume_resolution and not ignore:
            self._logger.warning("Volume is too small. Ensure volume is greater than resolution.")
            return False
        volume = round(volume/self.volume_resolution)*self.volume_resolution
        speed = speed or self.speed_out
        
        # Implement actual dispense function
        constraints = dict(
            speed_presets=self.device.preset_speeds, volume_resolution=self.volume_resolution,
            step_resolution=self.device.step_resolution, time_resolution=self.device.response_time
        )
        parameters = self.speed_interpolation.get((volume,speed), interpolate_speed(volume,speed,**constraints))
        if (volume,speed) not in self.speed_interpolation:
            self.speed_interpolation[(volume,speed)] = parameters
        if parameters['n_intervals'] == 0:
            return False
        if self.speed_out != parameters['preset_speed']:
            self.setSpeed(-1 * parameters['preset_speed'], as_default=False)
        
        remaining_steps = round(volume/self.volume_resolution)
        for i in range(parameters['n_intervals']):
            start_time = time.perf_counter()
            step = parameters['step_size'] if (i+1 != parameters['n_intervals']) else remaining_steps
            move_time = step*self.volume_resolution / parameters['preset_speed']
            out = self.device.dispense(step)
            if out != 'ok':
                return False
            remaining_steps -= step
            sleep_time = max(move_time + delay - (time.perf_counter()-start_time), 0)
            time.sleep(sleep_time)
        
        # Update values
        time.sleep(delay)
        self.volume = max(self.volume - volume, 0)
        if blowout and self.volume == 0:
            self.blowout(**kwargs)
        if pause:
            input("Press 'Enter' to proceed.")
        self.setSpeed(self.speed_out)
        return True
        
    def blowout(self, home:bool = True, **kwargs) -> bool:
        """
        Blow out the liquid from the pipette tool.
        """
        logger.debug("Blowing out")
        out = self.device.blowout(home=home)
        return out == 'ok'
    
    def pullback(self, **kwargs) -> bool:
        out = self.device.move(self.pullback_steps)
        return out == 'ok'
    
    def addAirGap(self, steps: int = 10) -> bool:
        assert steps > 0, "Steps must be greater than 0"
        out = self.device.move(steps)
        return out == 'ok'
    
    def attach(self, tip_length: int|float) -> bool:
        """
        Attach the tip to the pipette tool.
        """
        logger.debug("Attaching tip")
        self.device.flags.tip_on = True
        self.device.flags.tip_on = self.device.isTipOn()
        if self.device.flags.tip_on:
            self.tip_length = tip_length
        return self.device.flags.tip_on
    
    def eject(self) -> bool:
        """
        Eject the tip from the pipette tool.
        """
        logger.debug("Ejecting tip")
        out = self.device.eject()
        success = (out == 'ok')
        if success:
            self.device.flags.tip_on = False
            self.tip_length = 0
        return success
        
    def home(self) -> bool:
        """
        Home the pipette tool.
        """
        logger.debug("Homing")
        out = self.device.home()
        return out == 'ok'
        
    def setSpeed(self, speed: int|float, as_default:bool = True) -> bool:
        """
        Set the speed of the pipette tool.

        Args:
            speed (float): The speed to set the pipette tool to.
        """
        assert abs(speed) in self.device.preset_speeds, f"Speed must be one of {self.device.preset_speeds}"
        logger.debug(f"Setting speed to {speed} uL/s")
        speed_code = self.device.info.preset_speeds.index(abs(speed))+1
        out = self.device.setInSpeedCode(speed_code) if speed > 0 else self.device.setOutSpeedCode(speed_code)
        if as_default:
            if speed > 0:
                self.speed_in = speed
            else:
                self.speed_out = speed
        return out == 'ok'
    
    def isTipOn(self) -> bool:
        """
        Check if the tip is on the pipette tool.

        Returns:
            bool: True if the tip is on the pipette tool, False otherwise.
        """
        return self.device.isTipOn()
    