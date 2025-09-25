# -*- coding: utf-8 -*-
""" 
This module contains the SartoriusDevice class.

Attributes:
    READ_FORMAT (str): command template for reading
    WRITE_FORMAT (str): command template for writing
    Data (NamedTuple): data type for communication
    IntData (NamedTuple): data type for communication
    STEP_RESOLUTION (int): minimum number of steps to have tolerable errors in volume
    RESPONSE_TIME (float): delay between sending a command and receiving a response, in seconds
    
## Classes:
    `SartoriusDevice`: Sartorius pipette device class
    
## Functions:
    `interpolate_speed`: Calculates the best parameters for volume and speed
    
<i>Documentation last updated: 2025-02-22</i>
"""
# Standard library imports
from __future__ import annotations
from datetime import datetime
import logging
import numpy as np
import time
from types import SimpleNamespace
from typing import NamedTuple, Any

# Local application imports
from ......core.device import SerialDevice, AnyDevice
from . import sartorius_lib as lib

# Configure logging
from controllably import CustomLevelFilter
logger = logging.getLogger(__name__)
CustomLevelFilter().setModuleLevel(__name__, logging.INFO)

# READ_FORMAT = "{channel:1}{data}�\r"      # command template: <PRE><ADR><CODE><DATA><LRC><POST>
READ_FORMAT = "{channel:1}{data}\r"      # command template: <PRE><ADR><CODE><DATA><LRC><POST>
WRITE_FORMAT = '{channel}{data}º\r'       # command template: <PRE><ADR><CODE><DATA><LRC><POST> # Typical timeout wait is 400ms
Data = NamedTuple("Data", [("data", str), ("channel", int)])
IntData = NamedTuple("IntData", [("data", int), ("channel", int)])

STEP_RESOLUTION = 10
"""Minimum number of steps to have tolerable errors in volume"""
RESPONSE_TIME = 1.03
"""Delay between sending a command and receiving a response, in seconds"""

class SartoriusDevice(SerialDevice):
    """ 
    Sartorius pipette device class
    
    ### Constructor:
        `port` (str, optional): COM port address. Defaults to None.
        `baudrate` (int, optional): baudrate of the device. Defaults to 9600.
        `timeout` (int, optional): timeout for communication. Defaults to 2.
        `channel` (int, optional): channel id. Defaults to 1.
        `step_resolution` (int, optional): minimum number of steps to have tolerable errors in volume. Defaults to STEP_RESOLUTION.
        `response_time` (float, optional): delay between sending a command and receiving a response, in seconds. Defaults to RESPONSE_TIME.
        `tip_inset_mm` (int, optional): length of pipette that is inserted into the pipette tip. Defaults to 12.
        `tip_capacitance` (int, optional): threshold above which a conductive pipette tip is considered to be attached. Defaults to 276.
        `init_timeout` (int, optional): timeout for initialization. Defaults to 2.
        `data_type` (NamedTuple, optional): data type for communication. Defaults to Data.
        `read_format` (str, optional): read format for communication. Defaults to READ_FORMAT.
        `write_format` (str, optional): write format for communication. Defaults to WRITE_FORMAT.
        `simulation` (bool, optional): simulation mode. Defaults to False.
        `verbose` (bool, optional): verbose mode. Defaults to False.
        
    ### Attributes and properties:
        `info` (lib.ModelInfo): Sartorius model info
        `model` (str): model of the pipette
        `version` (str): version of the pipette
        `total_cycles` (int): total number of cycles of the pipette
        `volume_resolution` (float): volume resolution of the pipette
        `step_resolution` (int): minimum number of steps to have tolerable errors in volume
        `capacitance` (int): capacitance as measured at the end of the pipette
        `position` (int): current position of the pipette
        `speed_code_in` (int): speed code for aspirating
        `speed_code_out` (int): speed code for dispensing
        `status` (int): status of the pipette
        `channel` (int): channel id
        `response_time` (float): delay between sending a command and receiving a response, in seconds
        `tip_capacitance` (int): threshold above which a conductive pipette tip is considered to be attached
        `tip_inset_mm` (int): length of pipette that is inserted into the pipette tip
        `tip_length` (int): length of the pipette tip
        `capacity` (int): Capacity of the pipette
        `home_position` (int): Home position of the pipette
        `max_position` (int): Maximum position of the pipette
        `tip_eject_position` (int): Tip eject position of the pipette
        `limits` (tuple[int]): Lower and upper step limits of the pipette
        `preset_speeds` (np.ndarray[int|float]): Preset speeds available for the pipette
    
    ### Methods:
        `connect`: Connect to the device
        `query`: Query the device
        `getCapacitance`: Get the capacitance as measured at the end of the pipette
        `getErrors`: Get errors from the device
        `getPosition`: Get the current position of the pipette
        `getStatus`: Get the status of the pipette
        `isTipOn`: Check and return whether a pipette tip is attached
        `getInfo`: Get details of the Sartorius pipette model
        `getModel`: Get the model of the pipette
        `getVolumeResolution`: Get the volume resolution of the pipette
        `getInSpeedCode`: Get the speed code for aspirating
        `getOutSpeedCode`: Get the speed code for dispensing
        `getVersion`: Get the version of the pipette
        `getLifetimeCycles`: Get the total number of cycles of the pipette
        `setInSpeedCode`: Set the speed code for aspirating
        `setOutSpeedCode`: Set the speed code for dispensing
        `setChannelID`: Set the channel ID
        `aspirate`: Aspirate desired volume of reagent into pipette
        `blowout`: Blowout liquid from tip
        `dispense`: Dispense desired volume of reagent
        `eject`: Eject the pipette tip
        `home`: Return plunger to home position
        `move`: Move the plunger either up or down by a specified number of steps
        `moveBy`: Move the plunger by a specified number of steps
        `moveTo`: Move the plunger to a specified position
        `zero`: Zero the plunger position
        `reset`: Reset the pipette
    """
    
    _default_flags: SimpleNamespace = SimpleNamespace(
        verbose=False, connected=False, simulation=False,
        busy=False, conductive_tips=False, tip_on=False
    )
    implement_offset = (0,0,-250)
    def __init__(self, 
        port: str|None = None, 
        baudrate: int = 9600,
        timeout: int = 2,
        *,
        channel: int = 1, 
        step_resolution: int = STEP_RESOLUTION,
        response_time: float = RESPONSE_TIME,
        tip_inset_mm: int = 12,
        tip_capacitance: int = 276,
        init_timeout:int = 2, 
        data_type: NamedTuple = Data,
        read_format: str = READ_FORMAT,
        write_format: str = WRITE_FORMAT,
        simulation: bool = False, 
        verbose: bool = False,
        **kwargs
    ):
        """
        Initialize the Sartorius pipette device
        
        Args:
            port (str, optional): COM port address. Defaults to None.
            baudrate (int, optional): baudrate of the device. Defaults to 9600.
            timeout (int, optional): timeout for communication. Defaults to 2.
            channel (int, optional): channel id. Defaults to 1.
            step_resolution (int, optional): minimum number of steps to have tolerable errors in volume. Defaults to STEP_RESOLUTION.
            response_time (float, optional): delay between sending a command and receiving a response, in seconds. Defaults to RESPONSE_TIME.
            tip_inset_mm (int, optional): length of pipette that is inserted into the pipette tip. Defaults to 12.
            tip_capacitance (int, optional): threshold above which a conductive pipette tip is considered to be attached. Defaults to 276.
            init_timeout (int, optional): timeout for initialization. Defaults to 2.
            data_type (NamedTuple, optional): data type for communication. Defaults to Data.
            read_format (str, optional): read format for communication. Defaults to READ_FORMAT.
            write_format (str, optional): write format for communication. Defaults to WRITE_FORMAT.
            simulation (bool, optional): simulation mode. Defaults to False.
            verbose (bool, optional): verbose mode. Defaults to False.
        """
        super().__init__(
            port=port, baudrate=baudrate, timeout=timeout,
            init_timeout=init_timeout, simulation=simulation, verbose=verbose, 
            data_type=data_type, read_format=read_format, write_format=write_format, **kwargs
        )
        
        self.info = lib.Model.BRL0.value
        self.model = 'BRL0'
        self.version = ''
        self.total_cycles = 0
        self.volume_resolution = 1
        self.step_resolution = step_resolution
        
        self.capacitance = 0
        self.position = 0
        self.speed_code_in = 3
        self.speed_code_out = 3
        self.status = 0
        
        self.channel = channel
        self.response_time = response_time
        self.tip_capacitance = tip_capacitance
        self.tip_inset_mm = tip_inset_mm
        self.tip_length = 0
        
        self._repeat_query = True
        self._logger.warning("Any attached pipette tip may drop during initialisation.")
        self.connect()
        return
    
    # Properties
    @property
    def capacity(self) -> int:
        """Capacity of the pipette"""
        return self.info.capacity
    
    @property
    def home_position(self) -> int:
        """Home position of the pipette"""
        return self.info.home_position
    
    @property
    def max_position(self) -> int:
        """Maximum position of the pipette"""
        return self.info.max_position
    
    @property
    def tip_eject_position(self) -> int:
        """Tip eject position of the pipette"""
        return self.info.tip_eject_position
    
    @property
    def limits(self) -> tuple[int]:
        """Lower and upper step limits of the pipette"""
        return (self.info.tip_eject_position, self.info.max_position)
    
    @property
    def preset_speeds(self) -> np.ndarray[int|float]:
        """Preset speeds available for the pipette"""
        return np.array(self.info.preset_speeds)
    
    # General methods
    def connect(self):
        super().connect()
        if self.flags.simulation:
            self.position = self.home_position
        if self.is_connected:
            self.getInfo()
            self.reset()
        return
    
    def query(self,
        data: Any, 
        multi_out: bool = False, 
        *, 
        timeout: int|float = 0.3, 
        format_in: str|None = None, 
        format_out: str|None = None, 
        data_type: NamedTuple|None = None, 
        timestamp: bool = False
    ):
        data_type: NamedTuple = data_type or self.data_type
        format_in = format_in or self.write_format
        format_out = format_out or self.read_format
        if self.flags.simulation:
            field_types = data_type.__annotations__
            data_defaults = data_type._field_defaults
            defaults = [data_defaults.get(f, ('' if t is str else t(0))) for f,t in field_types.items()]
            data_out = data_type(*defaults)
            response = (data_out, datetime.now()) if timestamp else data_out
            return [response] if multi_out else response
        
        responses = super().query(
            data, multi_out, timeout=timeout, 
            format_in=format_in, timestamp=timestamp,
            channel=self.channel
        )
        if multi_out and not len(responses):
            return None
        responses = responses if multi_out else [responses]
        
        all_output = []
        for response in responses:
            if timestamp:
                out,now = response
            else:
                out = response
            if out is None:
                all_output.append(response)
                continue
            out: Data = out
            
            # Check channel
            if out.channel != self.channel:
                self._logger.warning(f"Channel mismatch: self={self.channel} | response={out.channel}")
                continue
            # Check error code
            if out.data[:2] == 'er':
                error_code = out.data
                error_details = lib.ErrorCode[error_code].value
                self._logger.error(f"{self.model}-{self.channel} received an error from command: {error_code}")
                self._logger.error(error_details)
                self.clearDeviceBuffer()
                if error_code != 'er4' or not self._repeat_query:
                    self._repeat_query = True
                    raise RuntimeError(error_details)
                else:   # repeat query once if drive was previously busy
                    time.sleep(timeout)
                    self.query(
                        data, multi_out, timeout=timeout, 
                        format_in=format_in, format_out=format_out, 
                        data_type=data_type, timestamp=timestamp
                    )
                    self._repeat_query = False
            # Check command code
            elif data.startswith('D') and (data[:2] != out.data[:2].upper()):
                self._logger.warning(f"Command mismatch: sent={data[:2]} | response={out.data[:2]}")
                continue
            
            data_dict = out._asdict()
            if out.data != 'ok':
                data_dict.update(dict(data=out.data[2:]))
            data_out = self.processOutput(format_out.format(**data_dict).strip(), format_out=format_out, data_type=data_type)
            data_out = data_out if timestamp else data_out[0]
            
            all_output.append((data_out, now) if timestamp else data_out)
            self._repeat_query = True
        return all_output if multi_out else all_output[0]
    
    # Status query methods
    def getCapacitance(self) -> int:
        """ 
        Get the capacitance as measured at the end of the pipette
        
        Returns:
            int: capacitance as measured at the end of the pipette
        """
        out: IntData = self.query('DN', data_type=IntData)
        self.capacitance = out.data
        return out.data
    
    def getErrors(self) -> str:
        """
        Get errors from the device
        
        Returns:
            str: errors from the device
        """
        out: Data = self.query('DE')
        return out.data
    
    def getPosition(self) -> int:
        """
        Get the current position of the pipette
        
        Returns:
            int: current position of the pipette
        """
        out: IntData = self.query('DP', data_type=IntData)
        if self.flags.simulation:
            return self.position
        self.position = out.data
        return out.data
    
    def getStatus(self) -> int:
        """
        Get the status of the pipette
        
        Returns:
            int: status of the pipette
        """
        out: IntData = self.query('DS', data_type=IntData)
        if self.flags.simulation:
            return self.status
        self.status = out.data
        status_name = lib.StatusCode(self.status).name
        if self.status in [4,6,8]:
            self.flags.busy = True
            self._logger.debug(status_name)
        elif self.status == 0:
            self.flags.busy = False
        return out.data
    
    def isTipOn(self) -> bool:
        """
        Check and return whether a pipette tip is attached
        
        Returns:
            bool: whether a pipette tip is attached
        """
        if self.flags.conductive_tips:
            self.flags.tip_on = (self.getCapacitance() > self.tip_capacitance)
            self._logger.info(f'Tip capacitance: {self.capacitance}')
        return self.flags.tip_on
    
    # Getter methods
    def getInfo(self, *, model: str|None = None) -> lib.ModelInfo:
        """
        Get details of the Sartorius pipette model
        
        Args:
            model (str, optional): model name. Defaults to None.
            
        Returns:
            lib.ModelInfo: Sartorius model info
        """
        if not self.is_connected:
            return
        self.model = self.getModel()
        self.version = self.getVersion()
        self.volume_resolution = self.getVolumeResolution() or 1
        self.speed_code_in = self.getInSpeedCode()
        self.speed_code_out = self.getOutSpeedCode()
        
        model_name = model or self.model
        self.model = model_name.split('-')[0]
        model_info = lib.Model[model_name.split('-')[0]].value
        self.info = model_info
        if self.volume_resolution != model_info.resolution:
            self._logger.warning(f"Resolution mismatch: {self.volume_resolution=} | {model_info.resolution=}")
            self._logger.warning(f"Using library value... ({model_info.resolution})")
            self.volume_resolution = model_info.resolution
        return model_info
    
    def getModel(self) -> str:
        """
        Get the model of the pipette
        
        Returns:
            str: model of the pipette
        """
        out: Data = self.query('DM')
        model_name = out.data.split('-')[0]
        if model_name not in lib.Model._member_names_:
            self._logger.warning(f'Received: {model_name}')
            self._logger.warning("Defaulting to: BRL0")
            self._logger.warning(f"Valid models are: {', '.join(lib.Model._member_names_)}")
            return 'BRL0'
        return out.data
    
    def getVolumeResolution(self) -> float:
        """
        Get the volume resolution of the pipette
        
        Returns:
            float: volume resolution of the pipette
        """
        out: IntData = self.query('DR', data_type=IntData)
        return out.data / 1000
    
    def getInSpeedCode(self) -> int:
        """
        Get the speed code for aspirating
        
        Returns:
            int: speed code for aspirating
        """
        out: IntData = self.query('DI', data_type=IntData)
        return out.data
    
    def getOutSpeedCode(self) -> int:
        """
        Get the speed code for dispensing
        
        Returns:
            int: speed code for dispensing
        """
        out: IntData = self.query('DO', data_type=IntData)
        return out.data
    
    def getVersion(self) -> str:
        """
        Get the version of the pipette
        
        Returns:
            str: version of the pipette
        """
        out: Data = self.query('DV')
        return out.data
    
    def getLifetimeCycles(self) -> int:
        """
        Get the total number of cycles of the pipette
        
        Returns:
            int: total number of cycles of the pipette
        """
        out: IntData = self.query('DX', data_type=IntData)
        return out.data
    
    # Setter methods
    def setInSpeedCode(self, value:int) -> str:
        """
        Set the speed code for aspirating
        
        Args:
            value (int): speed code
            
        Returns:
            str: response from the device
        """
        out: Data = self.query(f'SI{value}')
        if out.data == 'ok':
            self.speed_code_in = value
        return out.data
    
    def setOutSpeedCode(self, value:int) -> str:
        """
        Set the speed code for dispensing
        
        Args:
            value (int): speed code
            
        Returns:
            str: response from the device
        """
        out: Data = self.query(f'SO{value}')
        if out.data == 'ok':
            self.speed_code_out = value
        return out.data
    
    def setChannelID(self, channel:int) -> str:
        """
        Set the channel ID
        
        Args:
            channel (int): channel ID
            
        Returns:
            str: response from the device
        """
        assert 1 <= channel <= 9, "Channel ID must be between 1 and 9!"
        out: Data = self.query(f'*A{channel}')
        if out.data == 'ok':
            self.channel = channel
        return out.data
    
    # Action methods
    def aspirate(self, steps:int) -> str:
        """
        Aspirate desired volume of reagent into pipette
        
        Args:
            steps (int): number of steps to aspirate
            
        Returns:
            str: response from the device
        """
        steps = round(steps)
        assert steps >= 0, "Ensure non-negative steps!"
        # out: Data = self.query(f'RI{steps}', data_type=Data)
        # self.position += steps
        return self.moveBy(steps)
    
    def blowout(self, home:bool = True, *, position: int|None = None) -> str:
        """
        Blowout liquid from tip
        
        Args:
            home (bool, optional): return to home position. Defaults to True.
            position (int|None, optional): position to move to. Defaults to None.
            
        Returns:
            str: response from the device
        """
        position = self.home_position if position is None else position
        position = round(position)
        data = f'RB{position}' if home else 'RB'
        out: Data = self.query(data)
        time.sleep(1)
        if home:
            self.position = position
        return out.data
    
    def dispense(self, steps:int) -> str:
        """
        Dispense desired volume of reagent
        
        Args:
            steps (int): number of steps to dispense
            
        Returns:
            str: response from the device
        """
        steps = round(steps)
        assert steps >= 0, "Ensure non-negative steps!"
        # out: Data =  self.query(f'RO{steps}', data_type=Data)
        # self.position -= steps
        return self.moveBy(-steps)
    
    def eject(self, home:bool = True, *, position: int|None = None) -> str:
        """
        Eject the pipette tip
        
        Args:
            home (bool, optional): return to home position. Defaults to True.
            position (int|None, optional): position to move to. Defaults to None.
            
        Returns:
            str: response from the device
        """
        position = self.home_position if position is None else position
        position = round(position)
        data = f'RE{position}' if home else 'RE'
        out: Data = self.query(data)
        time.sleep(1)
        if home:
            self.position = position
        self.flags.tip_on = False
        return out.data
    
    def home(self) -> str:
        """
        Return plunger to home position
        
        Returns:
            str: response from the device
        """
        return self.zero()
    
    def move(self, steps:int) -> str:
        """
        Move the plunger either up or down by a specified number of steps
        
        Args:
            steps (int): number of steps to move
            
        Returns:
            str: response from the device
        """
        return self.moveBy(steps)
    
    def moveBy(self, steps:int) -> str:
        """
        Move the plunger by a specified number of steps
        
        Args:
            steps (int): number of steps to move
            
        Returns:
            str: response from the device
        """
        steps = round(steps)
        assert (min(self.limits) <= (self.position+steps) <= max(self.limits)), f"Range limits reached! ({self.position+steps})"
        data = f'RI{steps}' if steps >= 0 else f'RO{abs(steps)}'
        out: Data = self.query(data)
        while self.flags.busy:
            self.getStatus()
            time.sleep(0.3)
        self.position += steps
        # self.getPosition()
        return out.data
    
    def moveTo(self, position:int) -> str:
        """
        Move the plunger to a specified position
        
        Args:
            position (int): position to move to
            
        Returns:
            str: response from the device
        """
        position = round(position)
        assert (min(self.limits) <= position <= max(self.limits)), f"Range limits reached! ({position})"
        out: Data = self.query(f'RP{position}')
        while self.flags.busy:
            self.getStatus()
            time.sleep(0.3)
        self.position = position
        # self.getPosition()
        return out.data
    
    def zero(self) -> str:
        """
        Zero the plunger position
        
        Returns:
            str: response from the device
        """
        # self.query('RZ')
        # time.sleep(2)
        # self.eject(home=False)
        # # time.sleep(1)
        out: Data = self.query('RZ')
        self.position = 0
        time.sleep(2)
        self.eject()
        return out.data
    
    def reset(self) -> str:
        """
        Reset the pipette
        
        Returns:
            str: response from the device
        """
        self.zero()
        return


def interpolate_speed(
    volume:int, 
    speed:int, 
    *,
    speed_presets: tuple[int|float],
    volume_resolution: float,               # uL per step
    step_resolution: int = STEP_RESOLUTION, # minimum number of steps
    time_resolution: float = RESPONSE_TIME  # minimum communication / time delay
) -> dict[str, int|float]|None:
    """
    Calculates the best parameters for volume and speed

    Args:
        volume (int): volume to be transferred
        speed (int): speed at which liquid is transferred
        speed_presets (tuple[int|float]): preset speeds available
        volume_resolution (float): volume resolution of pipette (i.e. uL per step)
        step_resolution (int, optional): minimum number of steps to have tolerable errors in volume. Defaults to STEP_RESOLUTION.
        time_resolution (float, optional): minimum communication / time delay. Defaults to RESPONSE_TIME.

    Returns:
        dict: dictionary of best parameters
    """
    total_steps = volume/volume_resolution
    if total_steps < step_resolution:
        # target volume is smaller than the resolution of the pipette
        logger.error("Volume is too small.")
        return dict(preset_speed=speed_presets[0], n_intervals=0, step_size=0, delay=0)
    
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
        return dict(preset_speed=speed_presets[0], n_intervals=0, step_size=0, delay=0)
    best_parameters = interpolation_deviations[min(interpolation_deviations)]
    logger.info(f'Best parameters: {best_parameters}')
    return best_parameters
