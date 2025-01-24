# -*- coding: utf-8 -*-
"""
This module holds the base class for liquid handler tools.

Classes:
    LiquidHandler (ABC)
    Speed (dataclass)
"""
# Standard library imports
from __future__ import annotations
from copy import deepcopy
import logging
import time
from types import SimpleNamespace

# Local application imports
from ...core import factory
from ...core.device import Device, StreamingDevice

_logger = logging.getLogger("controllably.Transfer")
_logger.debug(f"Import: OK <{__name__}>")

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
logger.addHandler(handler)

def interpolate_speed(
    volume:int, 
    speed:int, 
    *,
    speed_presets: tuple[int|float],
    volume_resolution: float,
    step_resolution: int,
    time_resolution: float
) -> dict[str, int|float]|None:
    """
    Calculates the best parameters for volume and speed

    Args:
        volume (int): volume to be transferred
        speed (int): speed at which liquid is transferred

    Returns:
        dict: dictionary of best parameters
    """
    total_steps = volume/volume_resolution
    if total_steps < step_resolution:
        # target volume is smaller than the resolution of the pipette
        logger.error("Volume is too small.")
        return
    
    if speed in speed_presets:
        # speed is a preset, no interpolation needed
        return dict(preset_speed=speed, n_intervals=1, step_size=total_steps, delay=0)
    
    interpolation_deviations = {}
    for preset in speed_presets:
        if preset < speed:
            # preset is slower than target speed, it will never hit target speed
            continue
        total_delay = volume*(1/speed - 1/preset)
        if total_delay < time_resolution:
            # required delay is shorter than the communication delay
            continue
        n_intervals = int(max(1,min(total_steps/step_resolution, total_delay/time_resolution)))
        # if n_intervals == 1 and speed != preset:
        #     # only one interval is needed, but the speed is not the same as the preset
        #     # this means no interpolation is done, only the preset is used with a suitable delay
        #     continue
        steps_per_interval = int(total_steps/n_intervals)
        delay_per_interval = total_delay/n_intervals
        area = 0.5 * (volume**2) * (1/volume_resolution) * (1/n_intervals) * (1/speed - 1/preset)
        interpolation_deviations[area] = dict(
            preset_speed=preset, n_intervals=n_intervals, 
            step_size=steps_per_interval, delay=delay_per_interval
        )
    if len(interpolation_deviations) == 0:
        logger.error("No feasible speed parameters.")
        return
    best_parameters = interpolation_deviations[min(interpolation_deviations)]
    logger.info(f'Best parameters: {best_parameters}')
    return best_parameters


def execute_action_at_speed(parameters):
    ...


class LiquidHandler:
    """
    LiquidHandler is an abstract base class for liquid handler tools.

    ### Attributes
    - `name` (str): name of the liquid handler tool
    - `model` (Model): model of the liquid handler tool
    - `speed` (Speed): speed of the liquid handler tool

    ### Methods
    - `transfer(volume: int, speed: int)`: abstract method for transferring liquid
    - `home()`: abstract method for moving the liquid handler to home position
    - `eject_tip()`: abstract method for ejecting the tip from the liquid handler
    - `aspirate(volume: int)`: abstract method for aspirating liquid
    - `dispense(volume: int)`: abstract method for dispensing liquid
    - `set_speed(speed: int)`: abstract method for setting the speed of the liquid handler
    """
    
    _default_flags: SimpleNamespace[str,bool] = SimpleNamespace(busy=False, verbose=False)
    def __init__(self, *, verbose:bool = False, **kwargs):
        """
        Instantiate the class

        Args:
            verbose (bool, optional): verbosity of class. Defaults to False.
        """
        self.device: Device|StreamingDevice = kwargs.get('device', factory.create_from_config(kwargs))
        self.flags: SimpleNamespace = deepcopy(self._default_flags)
        
        self._logger = logger.getChild(f"{self.__class__.__name__}_{id(self)}")
        self._logger.addHandler(logging.StreamHandler())
        self.verbose = verbose
        
        # Category specific attributes
        self.speed_in = 0
        self.speed_out = 0
        self.capacity = 0
        self.volume = 0
        self.reagent = ''
        
        self.channel = 0
        self.offset = (0,0,0)
        
        self.volume_resolution = 0
        return
    
    def __del__(self):
        self.shutdown()
        return
    
    @property
    def connection_details(self) -> dict:
        """Connection details for the device"""
        return self.device.connection_details
    
    @property
    def is_busy(self) -> bool:
        """Whether the device is busy"""
        return self.flags.busy
    
    @property
    def is_connected(self) -> bool:
        """Whether the device is connected"""
        return self.device.is_connected
    
    @property
    def verbose(self) -> bool:
        """Verbosity of class"""
        return self.flags.verbose
    @verbose.setter
    def verbose(self, value:bool):
        assert isinstance(value,bool), "Ensure assigned verbosity is boolean"
        self.flags.verbose = value
        level = logging.DEBUG if value else logging.INFO
        for handler in self._logger.handlers:
            if not isinstance(handler, logging.StreamHandler):
                continue
            handler.setLevel(level)
        return
    
    def connect(self):
        """Connect to the device"""
        self.device.connect()
        return
    
    def disconnect(self):
        """Disconnect from the device"""
        self.device.disconnect()
        return
    
    def resetFlags(self):
        """Reset all flags to class attribute `_default_flags`"""
        self.flags = deepcopy(self._default_flags)
        return
    
    def shutdown(self):
        """Shutdown procedure for tool"""
        self.disconnect()
        self.resetFlags()
        return
    
    # Liquid handling methods
    def aspirate(self, 
        volume: float, 
        speed: float|None = None, 
        reagent: str|None = None,
        *,
        pullback: bool = False,
        delay: int = 0, 
        pause: bool = False, 
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
        if volume > (self.capacity - self.volume):
            volume = self.capacity - self.volume
            self._logger.warning("Volume exceeds capacity. Aspirating up to capacity.")
        if volume < self.volume_resolution:
            self._logger.warning("Volume is too small. Ensure volume is greater than resolution.")
            return False
        volume = round(volume/self.volume_resolution)*self.volume_resolution
        speed = speed or self.speed_in
        
        # Replace with actual aspirate implementation
        ...
        
        # Update values
        time.sleep(delay)
        self.volume = min(self.volume + volume, self.capacity)
        if pullback and self.volume < self.capacity:
            self.pullback(**kwargs)
        if pause:
            input("Press 'Enter' to proceed.")
        raise NotImplementedError
    
    def blowout(self, **kwargs) -> bool:
        """
        Blowout liquid from tip

        Args:
            channel (Optional[Union[int, tuple[int]], optional): channel id. Defaults to None.
            
        Returns:
            bool: whether the action is successful
        """
        self._logger.warning("Blowout not implemented.")
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
        if volume > self.volume and not ignore:
            volume = self.volume
            self._logger.warning("Volume exceeds available volume. Dispensing up to available volume.")
        if volume < self.volume_resolution and not ignore:
            self._logger.warning("Volume is too small. Ensure volume is greater than resolution.")
            return False
        volume = round(volume/self.volume_resolution)*self.volume_resolution
        speed = speed or self.speed_out
        
        # Replace with actual dispense implementation
        ...
        
        # Update values
        time.sleep(delay)
        self.volume = max(self.volume - volume, 0)
        if blowout and self.volume == 0:
            self.blowout(**kwargs)
        if pause:
            input("Press 'Enter' to proceed.")
        raise NotImplementedError

    def pullback(self, **kwargs) -> bool:
        """
        Pullback liquid from tip

        Args:
            channel (Optional[Union[int, tuple[int]]], optional): channel id. Defaults to None.
            
        Returns:
            bool: whether the action is successful
        """
        self._logger.warning("Pullback not implemented.")
        return True
    
    def cycle(self, 
        volume: float, 
        speed: float|None = None, 
        reagent: str|None = None,
        cycles: int = 1,
        *,
        delay: int = 0,
        **kwargs
    ) -> bool:
        """
        Cycle between aspirate and dispense

        Args:
            volume (float): target volume
            speed (float|None, optional): speed to aspirate and dispense at. Defaults to None.
            delay (int, optional): time delay after each action. Defaults to 0.
            cycles (int, optional): number of cycles. Defaults to 1.
            reagent (str|None, optional): name of reagent. Defaults to None.
            channel (Optional[Union[int, tuple[int]]], optional): channel id. Defaults to None.

        Returns:
            bool: whether the action is successful
        """
        assert cycles > 0, "Ensure cycles is a positive integer"
        success = []
        for _ in range(int(cycles)):
            ret1 = self.aspirate(volume, speed, reagent, delay=delay, pause=False, **kwargs)
            ret2 = self.dispense(volume, speed, delay=delay, pause=False, ignore=True, **kwargs)
            success.extend([ret1,ret2])
        return all(success)
    
    def empty(self, 
        speed: float|None = None, 
        *,
        blowout: bool = False,
        delay: int = 0, 
        pause: bool = False, 
        **kwargs
    ) -> bool:
        """
        Empty the channel

        Args:
            speed (float|None, optional): speed to empty. Defaults to None.
            delay (int, optional): delay time between steps in seconds. Defaults to 0.
            pause (bool, optional): whether to pause for user intervention. Defaults to False.
            channel (Optional[Union[int, tuple[int]]], optional): channel id. Defaults to None.
            
        Returns:
            bool: whether the action is successful
        """
        return self.dispense(self.capacity, speed, blowout=blowout, delay=delay, pause=pause, ignore=True, **kwargs)
    
    def fill(self, 
        speed: float|None = None, 
        reagent: str|None = None,
        *,
        pullback: bool = False,
        cycles: int = 0,
        delay: int = 0, 
        pause: bool = False, 
        **kwargs
    ) -> bool:
        """
        Fill the channel

        Args:
            speed (float|None, optional): speed to aspirate and dispense at. Defaults to None.
            delay (int, optional): time delay after each action. Defaults to 0.
            pause (bool, optional): whether to pause for user intervention. Defaults to False.
            cycles (int, optional): number of cycles before filling. Defaults to 0.
            reagent (str|None, optional): name of reagent. Defaults to None.
            channel (Optional[Union[int, tuple[int]]], optional): channel id. Defaults to None.
        
        Returns:
            bool: whether the action is successful
        """
        ret1 = self.rinse(speed, reagent, cycles, delay=delay, **kwargs) if cycles > 0 else True
        ret2 = self.aspirate(self.capacity, speed, reagent, pullback=pullback, delay=delay, pause=pause, **kwargs)
        return all([ret1,ret2])

    def rinse(self, 
        speed: float|None = None,
        reagent: str|None = None,
        cycles: int = 3,
        *,
        delay: int = 0, 
        **kwargs
    ) -> bool:
        """
        Rinse the channel with aspirate and dispense cycles
        
        Args:
            speed (float|None, optional): speed to aspirate and dispense at. Defaults to None.
            delay (int, optional): time delay after each action. Defaults to 0.
            cycles (int, optional): number of cycles. Defaults to 1.
            channel (Optional[Union[int, tuple[int]]], optional): channel id. Defaults to None.

        Returns:
            bool: whether the action is successful
        """
        return self.cycle(volume=self.capacity, speed=speed, reagent=reagent, cycles=cycles, delay=delay, **kwargs)
