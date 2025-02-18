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
from datetime import datetime
import logging
import numpy as np
import time
from types import SimpleNamespace
from typing import NamedTuple, Any

# Local application imports
from .....core.device import SerialDevice
from . import sartorius_lib as lib

_logger = logging.getLogger("controllably.Transfer")
_logger.debug(f"Import: OK <{__name__}>")

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
logger.addHandler(handler)

READ_FORMAT = "{channel:1}{data}�\r"      # command template: <PRE><ADR><CODE><DATA><LRC><POST>
WRITE_FORMAT = '{channel}{data}º\r'       # command template: <PRE><ADR><CODE><DATA><LRC><POST> # Typical timeout wait is 400ms
Data = NamedTuple("Data", [("data", str), ("channel", int)])
IntData = NamedTuple("IntData", [("data", int), ("channel", int)])

STEP_RESOLUTION = 10
"""Minimum number of steps to have tolerable errors in volume"""
RESPONSE_TIME = 1.03
"""Delay between sending a command and receiving a response, in seconds"""

class SartoriusDevice(SerialDevice):
    """
    Sartorius object

    ### Constructor
    Args:
        `port` (str): COM port address
        `channel` (int, optional): channel id. Defaults to 1.
        `offset` (tuple[float], optional): x,y,z offset of tip. Defaults to (0,0,0).
        `response_time` (float, optional): delay between sending a command and receiving a response, in seconds. Defaults to 1.03.
        `tip_inset_mm` (float, optional): length of pipette that is inserted into the pipette tip. Defaults to 12.
        `tip_capacitance` (int, optional): threshold above which a conductive pipette tip is considered to be attached. Defaults to 276.
    
    ### Attributes
    - `channel` (int): channel id
    - `limits` (tuple[int]): lower and upper step limits
    - `model_info` (SartoriusPipetteModel): Sartorius model info
    - `offset` (tuple[float]): x,y,z offset of tip
    - `position` (int): position of plunger
    - `response_time` (float): delay between sending a command and receiving a response, in seconds
    - `speed_code` (Speed): codes for aspirate and dispense speeds
    - `speed_presets` (PresetSpeeds): preset speeds available
    - `tip_inset_mm` (float): length of pipette that is inserted into the pipette tip
    - `tip_length` (float): length of pipette tip
    - `tip_capacitance` (int): threshold above which a conductive pipette tip is considered to be attached
    
    ### Properties
    - `capacitance` (int): capacitance as measured at the end of the pipette
    - `home_position` (int): home position of pipette
    - `port` (str): COM port address
    - `resolution` (float): volume resolution of pipette (i.e. uL per step)
    - `status` (str): pipette status
    
    ### Methods
    - `addAirGap`: create an air gap between two volumes of liquid in pipette
    - `aspirate`: aspirate desired volume of reagent into pipette
    - `blowout`: blowout liquid from tip
    - `dispense`: dispense desired volume of reagent
    - `eject`: eject the pipette tip
    - `empty`: empty the pipette
    - `getCapacitance`: get the capacitance as measured at the end of the pipette
    - `getErrors`: get errors from the device
    - `getInfo`: get details of the Sartorius pipette model
    - `getPosition`: get the current position of the pipette
    - `getStatus`: get the status of the pipette
    - `home`: return plunger to home position
    - `isFeasible`: checks and returns whether the plunger position is feasible
    - `isTipOn`: checks and returns whether a pipette tip is attached
    - `move`: move the plunger either up or down by a specified number of steps
    - `moveBy`: move the plunger by a specified number of steps
    - `moveTo`: move the plunger to a specified position
    - `pullback`: pullback liquid from tip
    - `reset`: reset the pipette
    - `setSpeed`: set the speed of the plunger
    - `shutdown`: shutdown procedure for tool
    - `toggleFeedbackLoop`: start or stop feedback loop
    - `zero`: zero the plunger position
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
        Instantiate the class

        Args:
            port (str): COM port address
            channel (int, optional): channel id. Defaults to 1.
            offset (tuple[float], optional): x,y,z offset of tip. Defaults to (0,0,0).
            response_time (float, optional): delay between sending a command and receiving a response, in seconds. Defaults to 1.03.
            tip_inset_mm (float, optional): length of pipette that is inserted into the pipette tip. Defaults to 12.
            tip_capacitance (int, optional): threshold above which a conductive pipette tip is considered to be attached. Defaults to 276.
        """
        super().__init__(
            port=port, baudrate=baudrate, timeout=timeout,
            init_timeout=init_timeout, simulation=simulation, verbose=verbose, 
            data_type=data_type, read_format=read_format, write_format=write_format, **kwargs
        )
        
        self._logger = logger.getChild(f"{self.__class__.__name__}_{id(self)}")
        self._logger.addHandler(logging.StreamHandler())
        self.verbose = verbose
        
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
        logger.warning("Any attached pipette tip may drop during initialisation.")
        self.connect()
        return
    
    # Properties
    
    @property
    def capacity(self) -> int:
        return self.info.capacity
    
    @property
    def home_position(self) -> int:
        return self.info.home_position
    
    @property
    def max_position(self) -> int:
        return self.info.max_position
    
    @property
    def tip_eject_position(self) -> int:
        return self.info.tip_eject_position
    
    @property
    def limits(self) -> tuple[int]:
        return (self.info.tip_eject_position, self.info.max_position)
    
    @property
    def preset_speeds(self) -> np.ndarray[int|float]:
        return np.array(self.info.preset_speeds)
    
    # General methods
    def connect(self):
        super().connect()
        if self.flags.simulation:
            self.position = self.home_position
        if self.checkDeviceConnection():
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
        format_out = format_out or self.read_format
        if self.flags.simulation:
            field_types = data_type.__annotations__
            data_defaults = data_type._field_defaults
            defaults = [data_defaults.get(f, ('' if t==str else t(0))) for f,t in field_types.items()]
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
                self.clear()
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
            data_out = self.processOutput(format_out.format(**data_dict).strip(), format=format_out, data_type=data_type)
            data_out = data_out if timestamp else data_out[0]
            
            all_output.append((data_out, now) if timestamp else data_out)
            self._repeat_query = True
        return all_output if multi_out else all_output[0]
    
    # Status query methods
    def getCapacitance(self) -> int:
        out: IntData = self.query('DN', data_type=IntData)
        self.capacitance = out.data
        return out.data
    
    def getErrors(self) -> str:
        out: Data = self.query('DE')
        return out.data
    
    def getPosition(self) -> int:
        out: IntData = self.query('DP', data_type=IntData)
        if self.flags.simulation:
            return self.position
        self.position = out.data
        return out.data
    
    def getStatus(self) -> int:
        out: IntData = self.query('DS', data_type=IntData)
        if self.flags.simulation:
            return self.status
        self.status = out.data
        status_name = lib.StatusCode(self.status).name
        if self.status in [4,6,8]:
            self.flags.busy = True
            logger.debug(status_name)
        elif self.status == 0:
            self.flags.busy = False
        return out.data
    
    def isTipOn(self) -> bool:
        if self.flags.conductive_tips:
            self.flags.tip_on = (self.getCapacitance() > self.tip_capacitance)
            logger.info(f'Tip capacitance: {self.capacitance}')
        return self.flags.tip_on
    
    # Getter methods
    def getInfo(self, *, model: str|None = None) -> lib.ModelInfo:
        if not self.is_connected:
            return
        self.model = self.getModel()
        self.version = self.getVersion()
        self.volume_resolution = self.getVolumeResolution() or 1
        self.speed_code_in = self.getInSpeedCode()
        self.speed_code_out = self.getOutSpeedCode()
        
        model_name = model or self.model
        model_info = lib.Model[model_name.split('-')[0]].value
        self.info = model_info
        if self.volume_resolution != model_info.resolution:
            logger.warning(f"Resolution mismatch: {self.volume_resolution=} | {model_info.resolution=}")
            # logger.warning("Check library values.")
            self.volume_resolution = model_info.resolution
        return model_info
    
    def getModel(self) -> str:
        out: Data = self.query('DM')
        model_name = out.data.split('-')[0]
        if model_name not in lib.Model._member_names_:
            logger.warning(f'Received: {model_name}')
            logger.warning("Defaulting to: BRL0")
            logger.warning(f"Valid models are: {', '.join(lib.Model._member_names_)}")
        return out.data
    
    def getVolumeResolution(self) -> float:
        out: IntData = self.query('DR', data_type=IntData)
        return out.data / 1000
    
    def getInSpeedCode(self) -> int:
        out: IntData = self.query('DI', data_type=IntData)
        return out.data
    
    def getOutSpeedCode(self) -> int:
        out: IntData = self.query('DO', data_type=IntData)
        return out.data
    
    def getVersion(self) -> str:
        out: Data = self.query('DV')
        return out.data
    
    def getLifetimeCycles(self) -> int:
        out: IntData = self.query('DX', data_type=IntData)
        return out.data
    
    # Setter methods
    def setInSpeedCode(self, value:int) -> str:
        out: Data = self.query(f'SI{value}')
        if out.data == 'ok':
            self.speed_code_in = value
        return out.data
    
    def setOutSpeedCode(self, value:int) -> str:
        out: Data = self.query(f'SO{value}')
        if out.data == 'ok':
            self.speed_code_out = value
        return out.data
    
    def setChannelID(self, channel:int) -> str:
        assert 1 <= channel <= 9, "Channel ID must be between 1 and 9!"
        out: Data = self.query(f'*A{channel}')
        if out.data == 'ok':
            self.channel = channel
        return out.data
    
    # Action methods
    def aspirate(self, steps:int) -> str:
        steps = round(steps)
        assert steps >= 0, "Ensure non-negative steps!"
        # out: Data = self.query(f'RI{steps}', data_type=Data)
        # self.position += steps
        return self.moveBy(steps)
    
    def blowout(self, home:bool = True, *, position: int|None = None) -> str:
        position = self.home_position if position is None else position
        position = round(position)
        data = f'RB{position}' if home else 'RB'
        out: Data = self.query(data)
        time.sleep(1)
        if home:
            self.position = position
        return out.data
    
    def dispense(self, steps:int) -> str:
        steps = round(steps)
        assert steps >= 0, "Ensure non-negative steps!"
        # out: Data =  self.query(f'RO{steps}', data_type=Data)
        # self.position -= steps
        return self.moveBy(-steps)
    
    def eject(self, home:bool = True, *, position: int|None = None) -> str:
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
        return self.moveTo(self.home_position)
    
    def move(self, steps:int) -> str:
        return self.moveBy(steps)
    
    def moveBy(self, steps:int) -> str:
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
        self.eject()
        out: Data = self.query('RZ')
        self.position = 0
        time.sleep(2)
        return out.data
    
    def reset(self) -> str:
        self.zero()
        return self.home()


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
