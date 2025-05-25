# -*- coding: utf-8 -*-
""" 
This module contains the Sartorius class.

## Classes:
    `Sartorius`: Sartorius pipette tool class
    
<i>Documentation last updated: 2025-02-22</i>
"""
# Standard library imports
from __future__ import annotations
import time

# Local application imports
from ...liquid import LiquidHandler
from .sartorius_api import SartoriusDevice, interpolate_speed

class Sartorius(LiquidHandler):
    """
    Sartorius pipette tool class
    
    ### Constructor:
        `port` (str): The port to connect to the pipette tool.
        `channel` (int): The channel to connect to. Defaults to 1.
        `verbose` (bool): Whether to print verbose output. Defaults to False.
        `simulation` (bool): Whether to simulate the pipette tool. Defaults to False.
        `tip_inset_mm` (int): The inset of the tip in mm. Defaults to 12.
        `tip_capacitance` (int): The capacitance of the tip. Defaults to 276.
        
    ### Attributes and properties:
        `tip_length` (int|float): The length of the tip attached to the pipette tool.
        `pullback_steps` (int): The number of steps to pull back the pipette tool.
        `speed_interpolation` (dict): The interpolation of speed values.
        `capacity` (float): The capacity of the pipette tool.
        `channel` (int): The channel of the pipette tool.
        `volume_resolution` (float): The volume resolution of the pipette tool.
        `tip_inset_mm` (float): The inset of the tip in mm.
        `device`: Device object
        `flags`: Flags for the class
        `speed_in`: Speed for aspiration
        `speed_out`: Speed for dispense
        `reagent`: Name of reagent
        `offset`: Offset for liquid handling
        `connection_details`: Connection details for the device
        `is_busy`: Whether the device is busy
        `is_connected`: Whether the device is connected
        `verbose`: Verbosity of class
        `volume`: Current volume of liquid in the channel
        
    ### Methods:
        `aspirate`: Aspirate desired volume of reagent
        `blowout`: Blowout liquid from tip
        `dispense`: Dispense desired volume of reagent
        `pullback`: Pullback liquid from tip
        `addAirGap`: Add an air gap to the pipette tool
        `attach`: Attach the tip to the pipette tool
        `eject`: Eject the tip from the pipette tool
        `home`: Home the pipette tool
        `setSpeed`: Set the speed of the pipette tool
        `isTipOn`: Check if the tip is on the pipette tool
        
        `connect`: Connect to the device
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
        *,
        channel: int = 1,
        verbose: bool = False,
        simulation: bool = False,
        tip_inset_mm: int = 12,
        tip_capacitance: int = 276,
        **kwargs
    ):
        """ 
        Initialize the Sartorius pipette tool.
        
        Args:
            port (str): The port to connect to the pipette tool.
            channel (int): The channel to connect to. Defaults to 1.
            verbose (bool): Whether to print verbose output. Defaults to False.
            simulation (bool): Whether to simulate the pipette tool. Defaults to False.
            tip_inset_mm (int): The inset of the tip in mm. Defaults to 12.
            tip_capacitance (int): The capacitance of the tip. Defaults to 276.
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
    def capacity(self) -> float:
        return self.device.capacity
    @capacity.setter
    def capacity(self, value: float):
        return
    
    @property
    def channel(self) -> int:
        return self.device.channel
    @channel.setter
    def channel(self, value: int):
        return
    
    @property
    def volume_resolution(self) -> float:
        return self.device.volume_resolution
    @volume_resolution.setter
    def volume_resolution(self, value: float):
        return
    
    @property
    def tip_inset_mm(self) -> float:
        """The inset of the tip in mm"""
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
        if (reagent and self.reagent) and reagent != self.reagent:
            self._logger.warning(f"Reagent {reagent} does not match current reagent {self.reagent}.")
            return False
        if not self.isTipOn():
            self._logger.warning("Ensure tip is attached.")
            raise RuntimeWarning("Ensure tip is attached.")
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
            self._logger.error("No feasible interpolation found.")
            raise ValueError("No feasible interpolation found.")
            return False
        if self.speed_in != parameters['preset_speed']:
            self.setSpeed(parameters['preset_speed'], as_default=False)
        
        remaining_steps = round(volume/self.volume_resolution)
        for i in range(parameters['n_intervals']):
            start_time = time.perf_counter()
            step = parameters['step_size'] if (i+1 != parameters['n_intervals']) else remaining_steps
            move_time = step*self.volume_resolution / parameters['preset_speed']
            out = self.device.aspirate(step)
            if not self.device.flags.simulation and out != 'ok':
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
        if not self.isTipOn():
            self._logger.warning("Ensure tip is attached.")
            raise RuntimeWarning("Ensure tip is attached.")
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
            self._logger.error("No feasible interpolation found.")
            raise ValueError("No feasible interpolation found.")
            return False
        if self.speed_out != parameters['preset_speed']:
            self.setSpeed(-1 * parameters['preset_speed'], as_default=False)
        
        remaining_steps = round(volume/self.volume_resolution)
        for i in range(parameters['n_intervals']):
            start_time = time.perf_counter()
            step = parameters['step_size'] if (i+1 != parameters['n_intervals']) else remaining_steps
            move_time = step*self.volume_resolution / parameters['preset_speed']
            out = self.device.dispense(step)
            if not self.device.flags.simulation and out != 'ok':
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
        Blowout liquid from tip
        
        Args:
            home (bool): whether to home the pipette tool after blowing out
            
        Returns:
            bool: whether the action is successful
        """
        self._logger.debug("Blowing out")
        out = self.device.blowout(home=home)
        return out == 'ok'
    
    def pullback(self, **kwargs) -> bool:
        out = self.device.move(self.pullback_steps)
        return out == 'ok'
    
    def addAirGap(self, steps: int = 10) -> bool:
        """ 
        Add an air gap to the pipette tool.
        
        Args:
            steps (int): The number of steps to move the pipette tool.
            
        Returns:
            bool: Whether the action is successful.
        """
        assert steps > 0, "Steps must be greater than 0"
        out = self.device.move(steps)
        return out == 'ok'
    
    def attach(self, tip_length: int|float) -> bool:
        """
        Attach the tip to the pipette tool.
        
        Args:
            tip_length (int|float): The length of the tip to attach.
            
        Returns:
            bool: Whether the action is successful.
        """
        self._logger.debug("Attaching tip")
        self.device.flags.tip_on = True
        self.device.flags.tip_on = self.device.isTipOn()
        if self.device.flags.tip_on:
            self.tip_length = tip_length
        return self.device.flags.tip_on
    
    def eject(self) -> bool:
        """
        Eject the tip from the pipette tool.
        
        Returns:
            bool: Whether the action is successful.
        """
        self._logger.debug("Ejecting tip")
        out = self.device.eject()
        success = (out == 'ok')
        if success:
            self.device.flags.tip_on = False
            self.tip_length = 0
        return success
        
    def home(self) -> bool:
        """
        Home the pipette tool.
        
        Returns:
            bool: Whether the action is successful.
        """
        self._logger.debug("Homing")
        out = self.device.home()
        return out == 'ok'
        
    def setSpeed(self, speed: int|float, as_default:bool = True) -> bool:
        """
        Set the speed of the pipette tool.

        Args:
            speed (float): The speed to set the pipette tool to.
            as_default (bool): Whether to set the speed as the default speed.
            
        Returns:
            bool: Whether the action is successful.
        """
        assert abs(speed) in self.device.preset_speeds, f"Speed must be one of {self.device.preset_speeds}"
        self._logger.debug(f"Setting speed to {speed} uL/s")
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
    