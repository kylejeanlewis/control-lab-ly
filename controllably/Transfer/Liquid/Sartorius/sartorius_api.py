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
import numpy as np
from threading import Thread
import time
from typing import Optional, Union

# Third party imports
import serial # pip install pyserial

# Local application imports
from ..liquid import interpolate_speed
from ..liquid_utils import LiquidHandler, Speed
from . import sartorius_lib as lib

_logger = logging.getLogger("controllably.Transfer")
_logger.debug(f"Import: OK <{__name__}>")

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
logger.addHandler(handler)

QUERIES = lib.StatusQueryCode._member_names_ + lib.StaticQueryCode._member_names_
"""List of all query codes"""
STEP_RESOLUTION = 10
"""Minimum number of steps to have tolerable errors in volume"""

class Sartorius(LiquidHandler):
    """
    Sartorius object

    ### Constructor
    Args:
        `port` (str): COM port address
        `channel` (int, optional): channel id. Defaults to 1.
        `offset` (tuple[float], optional): x,y,z offset of tip. Defaults to (0,0,0).
        `response_time` (float, optional): delay between sending a command and receiving a response, in seconds. Defaults to 1.03.
        `tip_inset_mm` (float, optional): length of pipette that is inserted into the pipette tip. Defaults to 12.
        `tip_threshold` (int, optional): threshold above which a conductive pipette tip is considered to be attached. Defaults to 276.
    
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
    - `tip_threshold` (int): threshold above which a conductive pipette tip is considered to be attached
    
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
    
    _default_flags = {
        'busy': False,
        'conductive_tips': False,
        'connected': False,
        'get_feedback': False,
        'occupied': False,
        'pause_feedback':False,
        'tip_on': False
    }
    implement_offset = (0,0,-250)
    def __init__(self, 
        port:str, 
        channel: int = 1, 
        offset: tuple[float] = (0,0,0),
        response_time: float = 1.03,
        tip_inset_mm: int = 12,
        tip_threshold: int = 276,
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
            tip_threshold (int, optional): threshold above which a conductive pipette tip is considered to be attached. Defaults to 276.
        """
        super().__init__(**kwargs)
        self.channel = channel
        self.offset = offset
        self.response_time = response_time
        self.tip_threshold = tip_threshold
        self.tip_inset_mm = tip_inset_mm
        
        self.model_info: lib.ModelInfo = None
        self.limits = (0,0)
        self.position = 0
        self.speed_code = Speed(3,3)
        self.speed_presets = None
        self.tip_length = 0
        
        self._capacitance = 0
        self._status_code = ''
        self._threads = {}
        
        logger.warning("Any attached pipette tip may drop during initialisation.")
        self._connect(port)
        return
    
    # Properties
    @property
    def capacitance(self) -> int:
        return self._capacitance
        
    @property
    def home_position(self) -> int:
        return self.model_info.home_position
    
    @property
    def port(self) -> str:
        return self.connection_details.get('port', '')
    
    @property
    def resolution(self) -> float:
        return self.model_info.resolution
    
    @property
    def status(self) -> str:
        return self.getStatus()
    
    def getTotalCycles(self) -> Union[int, str]:
        """
        Retrieve total cycle lifetime

        Returns:
            Union[int, str]: number of lifetime cycles, or response string
        """
        response = self._query('DX')
        try:
            cycles = int(response)
        except ValueError:
            return response
        logger.info(f'Total cycles: {cycles}')
        return cycles
    
    def getModel(self) -> str:
        """
        Retrieve the model of the device

        Returns:
            str: model name
        """
        response = self._query('DM')
        logger.info(f'Model: {response}')
        return response
    
    def getVolumeResolution(self) -> Union[int, str]:
        """
        Retrieve the resolution of the device

        Returns:
            Union[int, str]: volume resolution of device in nL, or response string
        """
        response = self._query('DR')
        try:
            resolution = int(response)
        except ValueError:
            return response
        logger.info(f'{resolution/1000} uL / step')
        return resolution
    
    def getVersion(self) -> str:
        """
        Retrieve the software version on the device

        Returns:
            str: device version
        """
        return self._query('DV')

    def addAirGap(self, steps:int = 10) -> str:
        """
        Create an air gap between two volumes of liquid in pipette
        
        Args:
            steps (int, optional): number of steps for air gap. Defaults to DEFAULT_AIRGAP.
            channel (int, optional): channel to add air gap. Defaults to None.

        Returns:
            str: device response
        """
        response = self._query(f'RI{steps}')
        time.sleep(1)
        return response
        
    def aspirate(self, 
        volume: float, 
        speed: Optional[float] = None, 
        wait: int = 0, 
        pause: bool = False, 
        reagent: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Aspirate desired volume of reagent

        Args:
            volume (float): target volume
            speed (Optional[float], optional): speed to aspirate at. Defaults to None.
            wait (int, optional): time delay after aspirate. Defaults to 0.
            pause (bool, optional): whether to pause for user intervention. Defaults to False.
            reagent (Optional[str], optional): name of reagent. Defaults to None.
            
        Returns:
            str: device response
        """ 
        self.setFlag(pause_feedback=True, occupied=True)
        volume = min(volume, self.capacity - self.volume)
        steps = int(volume / self.resolution)
        volume = steps * self.resolution
        if volume == 0:
            return ''
        logger.info(f'Aspirating {volume} uL...')
        start_aspirate = time.perf_counter()
        speed = self.speed.up if speed is None else speed
        
        if speed in self.speed_presets:
            if speed != self.speed.up:
                self.setSpeed(speed=speed, up=True, default=False)
            start_aspirate = time.perf_counter()
            response = self._query(f'RI{steps}')
            move_time = steps*self.resolution / speed
            duration = time.perf_counter() - start_aspirate
            if duration < (move_time):
                time.sleep(move_time-duration)
            # if response != 'ok':
            #     return response
            
        elif speed not in self.speed_presets:
            logger.info(f"Target: {volume} uL at {speed} uL/s...")
            speed_parameters = self._calculate_speed_parameters(volume=volume, speed=speed)
            logger.debug(speed_parameters)
            preset = speed_parameters.preset
            if preset is None:
                # raise RuntimeError('Target speed not possible.')
                logger.error('Target speed not possible.')
                return
            self.setSpeed(speed=preset, up=True, default=False)
            
            steps_left = steps
            delay = speed_parameters.delay
            step_size = speed_parameters.step_size
            intervals = speed_parameters.intervals
            start_aspirate = time.perf_counter()
            for i in range(intervals):
                start_time = time.perf_counter()
                step = step_size if (i+1 != intervals) else steps_left
                move_time = step*self.resolution / preset
                response = self._query(f'RI{step}', resume_feedback=False, get_position=False)
                # if response != 'ok':
                #     logger.error("Aspiration failed")
                #     return response
                steps_left -= step
                duration = time.perf_counter() - start_time
                if duration < (delay+move_time):
                    time.sleep(delay+move_time-duration)
        
        # Update values
        logger.debug(f'Aspiration time: {time.perf_counter()-start_aspirate}s')
        time.sleep(wait)
        self.setFlag(occupied=False, pause_feedback=False)
        self.getPosition()
        self.volume += volume
        self.position += steps
        if reagent is not None:
            self.reagent = reagent
        if pause:
            input("Press 'Enter' to proceed.")
        return response
    
    def blowout(self, home:bool = True, **kwargs) -> str:
        """
        Blowout liquid from tip

        Args:
            home (bool, optional): whether to return plunger to home position. Defaults to True.

        Returns:
            str: device response
        """
        command = f'RB{self.home_position}' if home else 'RB'
        response = self._query(command)
        self.position = self.home_position
        time.sleep(1)
        return response
    
    def dispense(self, 
        volume: float, 
        speed: Optional[float] = None, 
        wait: int = 0, 
        pause: bool = False, 
        blowout: bool = False,
        blowout_home: bool = True,
        force_dispense: bool = False, 
        **kwargs
    ) -> str:
        """
        Dispense desired volume of reagent

        Args:
            volume (float): target volume
            speed (Optional[float], optional): speed to dispense at. Defaults to None.
            wait (int, optional): time delay after dispense. Defaults to 0.
            pause (bool, optional): whether to pause for user intervention. Defaults to False.
            blowout (bool, optional): whether perform blowout. Defaults to False.
            blowout_home (bool, optional): whether to return the plunger home after blowout. Defaults to True.
            force_dispense (bool, optional): whether to dispense reagent regardless. Defaults to False.

        Raises:
            ValueError: Required dispense volume is greater than volume in tip

        Returns:
            str: device response
        """
        self.setFlag(pause_feedback=True, occupied=True)
        if force_dispense:
            volume = min(volume, self.volume)
        elif volume > self.volume:
            raise ValueError('Required dispense volume is greater than volume in tip.')
        steps = int(volume / self.resolution)
        volume = steps * self.resolution
        if volume == 0:
            return ''
        logger.info(f'Dispensing {volume} uL...')
        start_dispense = time.perf_counter()
        speed = self.speed.down if speed is None else speed

        if speed in self.speed_presets:
            if speed != self.speed.down:
                self.setSpeed(speed=speed, up=False, default=False)
            start_dispense = time.perf_counter()
            response = self._query(f'RO{steps}')
            move_time = steps*self.resolution / speed
            duration = time.perf_counter() - start_dispense
            if duration < (move_time):
                time.sleep(move_time-duration)
            # if response != 'ok':
            #     return response
            
        elif speed not in self.speed_presets:
            logger.info(f"Target: {volume} uL at {speed} uL/s...")
            speed_parameters = self._calculate_speed_parameters(volume=volume, speed=speed)
            logger.debug(speed_parameters)
            preset = speed_parameters.preset
            if preset is None:
                # raise RuntimeError('Target speed not possible.')
                logger.error('Target speed not possible.')
                return
            self.setSpeed(speed=preset, up=False, default=False)
        
            steps_left = steps
            delay = speed_parameters.delay
            step_size = speed_parameters.step_size
            intervals = speed_parameters.intervals
            start_dispense = time.perf_counter()
            for i in range(intervals):
                start_time = time.perf_counter()
                step = step_size if (i+1 != intervals) else steps_left
                move_time = step*self.resolution / preset
                response = self._query(f'RO{step}', resume_feedback=False, get_position=False)
                # if response != 'ok':
                #     logger.error("Dispense failed")
                #     return response
                steps_left -= step
                duration = time.perf_counter() - start_time
                if duration < (delay+move_time):
                    time.sleep(delay+move_time-duration)

        # Update values
        logger.debug(f'Dispense time: {time.perf_counter()-start_dispense}s')
        time.sleep(wait)
        self.setFlag(occupied=False, pause_feedback=False)
        self.getPosition()
        self.volume = max(self.volume - volume, 0)
        self.position -= steps
        if self.volume == 0 and blowout:
            self.blowout(home=blowout_home)
        if pause:
            input("Press 'Enter' to proceed.")
        return response
    
    def eject(self, home:bool = True) -> str:
        """
        Eject the pipette tip

        Args:
            home (bool, optional): whether to return plunger to home position. Defaults to True.

        Returns:
            str: device response
        """
        self.reagent = ''
        command = f'RE{self.home_position}' if home else 'RE'
        response = self._query(command)
        self.position = self.home_position if home else 0
        time.sleep(1)
        if not self.flags['conductive_tips']:
            self.setFlag(tip_on=False)
        return response
    
    def getCapacitance(self) -> Union[int, str]:
        """
        Get the capacitance as measured at the end of the pipette
        
        Returns:
            Union[int, str]: capacitance value, or device response
        """
        response = self._query('DN')
        try:
            capacitance = int(response)
        except ValueError:
            return response
        self._capacitance = capacitance
        return capacitance
 
    def getErrors(self) -> str:
        """
        Get errors from the device

        Returns:
            str: device response
        """
        return self._query('DE')
    
    def getInfo(self, model: Optional[str] = None):
        """Get details of the Sartorius pipette model"""
        model = str(self.getModel()).split('-')[0] if model is None else model
        if model not in lib.Model._member_names_:
            logger.warning(f'Received: {model}')
            model = 'BRL0'
            logger.warning(f"Defaulting to: {'BRL0'}")
            logger.warning(f"Valid models are: {', '.join(lib.Model._member_names_)}")
        info: lib.ModelInfo = lib.Model[model].value
        logger.info(info)
        self.model_info = info
        self.capacity = info.capacity
        self.limits = (info.tip_eject_position, info.max_position)
        self.speed_presets = info.preset_speeds
        self.speed.up = self.speed_presets[self.speed_code.up-1]
        self.speed.down = self.speed_presets[self.speed_code.down-1]
        return
    
    def getPosition(self, **kwargs) -> int:
        """Get the current position of the pipette"""
        response = self._query('DP')
        try:
            position = int(response)
        except ValueError:
            return response
        self.position = position
        return self.position
      
    def getStatus(self, **kwargs) -> str:
        """
        Get the status of the pipette

        Returns:
            str: device response
        """
        response = self._query('DS')
        try:
            status = int(response)
        except ValueError:
            return response
        if response not in [_status.value for _status in lib.StatusCode]:
            return response
        
        self._status_code = status
        if status in [4,6,8]:
            self.setFlag(busy=True)
            logger.debug(lib.StatusCode(status).name)
        elif status == 0:
            self.setFlag(busy=False)
        return lib.StatusCode(self._status_code).name
    
    def home(self) -> str:
        """
        Return plunger to home position
        
        Returns:
            str: device response
        """
        response = self._query(f'RP{self.home_position}')
        self.volume = 0
        self.position = self.home_position
        time.sleep(1)
        return response
    
    def isFeasible(self, position:int) -> bool:
        """
        Checks and returns whether the plunger position is feasible

        Args:
            position (int): plunger position

        Returns:
            bool: whether plunger position is feasible
        """
        if (self.limits[0] <= position <= self.limits[1]):
            return True
        logger.error(f"Range limits reached! {self.limits}")
        return False
    
    def isTipOn(self) -> bool:
        """
        Checks and returns whether a pipette tip is attached
        
        Returns:
            bool: whether a pipette tip in attached
        """
        self.getCapacitance()
        logger.info(f'Tip capacitance: {self.capacitance}')
        if self.flags['conductive_tips']:
            tip_on = (self.capacitance > self.tip_threshold)
            self.setFlag(tip_on=tip_on)
        tip_on = self.flags['tip_on']
        return tip_on
    
    def move(self, steps:int, up:bool, **kwargs) -> str:
        """
        Move the plunger either up or down by a specified number of steps

        Args:
            steps (int): number of steps to move plunger by
            up (bool): whether to move the plunger up

        Returns:
            str: device response
        """
        steps = abs(steps) if up else -abs(steps)
        return self.moveBy(steps)
    
    def moveBy(self, steps:int, **kwargs) -> str:
        """
        Move the plunger by specified number of steps

        Args:
            steps (int): number of steps to move plunger by (<0: move down/dispense; >0 move up/aspirate)

        Returns:
            str: device response
        """
        command = f'RI{steps}' if steps > 0 else f'RO{-steps}'
        self.position += steps
        return self._query(command)
    
    def moveTo(self, position:int, **kwargs) -> str:
        """
        Move the plunger to a specified position

        Args:
            position (int): target plunger position

        Returns:
            str: device response
        """
        self.position = position
        return self._query(f'RP{position}')
    
    def pullback(self, steps:int = 5, **kwargs) -> str:
        """
        Pullback liquid from tip
        
        Args:
            steps (int, optional): number of steps to pullback. Defaults to 5.

        Returns:
            str: device response
        """
        response = self._query(f'RI{steps}')
        self.position += steps
        time.sleep(1)
        return response
    
    def reset(self) -> str:
        """
        Reset the pipette

        Returns:
            str: device response
        """
        self.zero()
        return self.home()
    
    def setSpeed(self, speed:int, up:bool, default:bool = False, **kwargs) -> str:
        """
        Set the speed of the plunger

        Args:
            speed (int): speed of plunger
            up (bool): direction of travel
            default (bool, optional): whether to set speed as a default. Defaults to False.

        Returns:
            str: device response
        """
        speed_code = 1 + [x for x,val in enumerate(np.array(self.speed_presets)-speed) if val >= 0][0]
        logger.info(f'Speed {speed_code}: {self.speed_presets[speed_code-1]} uL/s')
        direction = 'I' if up else 'O'
        self._query(f'S{direction}{speed_code}')
        if not default:
            return self._query(f'D{direction}')
        if up:
            self.speed_code.up = speed_code
            self.speed.up = self.speed_presets[speed_code-1]
        else:
            self.speed_code.down = speed_code
            self.speed.down = self.speed_presets[speed_code-1]
        return self._query(f'D{direction}')
    
    def shutdown(self):
        """Shutdown procedure for tool"""
        self.toggleFeedbackLoop(on=False)
        return super().shutdown()
    
    def toggleFeedbackLoop(self, on:bool):
        """
        Start or stop feedback loop
        
        Args:
            on (bool): whether to start feedback loop
        """
        self.setFlag(get_feedback=on)
        if on:
            if 'feedback_loop' in self._threads:
                self._threads['feedback_loop'].join()
            thread = Thread(target=self._loop_feedback)
            thread.start()
            self._threads['feedback_loop'] = thread
        else:
            if 'feedback_loop' in self._threads:
                self._threads['feedback_loop'].join()
        return

    def zero(self) -> str:
        """
        Zero the plunger position
        
        Returns:
            str: device response
        """
        self.eject()
        response = self._query('RZ')
        self.position = 0
        time.sleep(2)
        return response

    # Protected method(s)
    def _calculate_speed_parameters(self, volume:int, speed:int) -> lib.SpeedParameters:
        """
        Calculates the best parameters for volume and speed

        Args:
            volume (int): volume to be transferred
            speed (int): speed at which liquid is transferred

        Returns:
            dict: dictionary of best parameters
        """
        outcomes = {}
        step_interval_limit = int(volume/self.resolution/STEP_RESOLUTION)
        for preset in self.speed_presets:
            if preset < speed:
                # preset is slower than target speed, it will never hit target speed
                continue
            time_interval_limit = int(volume*(1/speed - 1/preset)/self.response_time)
            if not step_interval_limit:
                continue
            intervals = max(min(step_interval_limit, time_interval_limit), 1)
            if intervals == 1 and speed != preset:
                continue
            each_steps = volume/self.resolution/intervals
            each_delay = volume*(1/speed - 1/preset)/intervals
            area = 0.5 * (volume**2) * (1/self.resolution) * (1/intervals) * (1/speed - 1/preset)
            outcomes[area] = lib.SpeedParameters(preset, intervals, int(each_steps), each_delay)
        if len(outcomes) == 0:
            logger.error("No feasible speed parameters.")
            return lib.SpeedParameters(None, STEP_RESOLUTION, STEP_RESOLUTION, self.response_time)
        logger.info(f'Best parameters: {outcomes[min(outcomes)]}')
        return outcomes[min(outcomes)]
    
    def _connect(self, port:str, baudrate:int = 9600, timeout:int = 1):
        """
        Connection procedure for tool

        Args:
            port (str): COM port address
            baudrate (int, optional): baudrate. Defaults to 9600.
            timeout (int, optional): timeout in seconds. Defaults to 1.
        """
        self.connection_details = {
            'port': port,
            'baudrate': baudrate,
            'timeout': timeout
        }
        device = None
        try:
            device = serial.Serial(port, baudrate, timeout=timeout)
        except Exception as e:
            logger.error(f"Could not connect to {port}")
            # logger.exception(e)
        else:
            time.sleep(2)   # Wait for grbl to initialize
            device.reset_input_buffer()
            logger.info(f"Connection opened to {port}")
            self.setFlag(connected=True)
        self.device = device
        self.getInfo()
        self.reset()
        return
    
    def _is_expected_reply(self, response:str, command_code:str, **kwargs) -> bool:
        """
        Checks and returns whether the response is an expected reply

        Args:
            response (str): response string from device
            command_code (str): two-character command code

        Returns:
            bool: whether the response is an expected reply
        """
        if response in lib.ErrorCode._member_names_:
            return True
        if command_code not in QUERIES and response == 'ok':
            return True
        if command_code in QUERIES and response[:2] == command_code.lower():
            reply_code, data = response[:2], response[2:]
            logger.debug(f'[{reply_code}] {data}')
            return True
        return False

    def _loop_feedback(self):
        """Loop to constantly read from device"""
        print('Listening...')
        while self.flags['get_feedback']:
            if self.flags['pause_feedback']:
                continue
            self.getStatus()
            self.getCapacitance()
        print('Stop listening...')
        return
    
    def _query(self, 
        command: str, 
        timeout_s: float = 0.3, 
        resume_feedback: bool = False,
        get_position: bool = True
    ) -> str:
        """
        Write command to and read response from device

        Args:
            command (str): command string
            timeout_s (float, optional): duration to wait before timeout. Defaults to 0.3.
            resume_feedback (bool, optional): whether to resume reading from device. Defaults to False.
            get_position (bool, optional): whether to get the position of the plunger. Defaults to True.
        Returns:
            str: response string
        """
        command_code = command[:2]
        if command_code not in lib.StatusQueryCode._member_names_:
            if self.flags['get_feedback'] and not self.flags['pause_feedback']:
                self.setFlag(pause_feedback=True)
                time.sleep(timeout_s)
            # self.getStatus()
            # while self.isBusy():
            #     self.getStatus()
            if self.isBusy():
                time.sleep(timeout_s)
        
        start_time = time.perf_counter()
        self._write(command)
        response = ''
        while not self._is_expected_reply(response, command_code):
            if time.perf_counter() - start_time > timeout_s:
                break
            response = self._read()
        # logger.debug(time.perf_counter() - start_time)
        if command_code in QUERIES:
            response = response[2:]
        if command_code not in lib.StatusQueryCode._member_names_:
            if get_position:
                self.getPosition()
            if resume_feedback:
                self.setFlag(pause_feedback=False)
        return response

    def _read(self) -> str:
        """
        Read response from device

        Returns:
            str: response string
        """
        response = ''
        try:
            response = self.device.readline()
            if len(response) == 0:
                response = self.device.readline()
            response = response[2:-2].decode('utf-8','replace')
            logger.debug(repr(response))
        except AttributeError:
            pass
        except Exception as e:
            logger.exception(e)
        if response in lib.ErrorCode._member_names_:
            logger.error(lib.ErrorCode[response].value)
        return response
    
    def _set_channel_id(self, new_channel_id:int):
        """
        Set channel id of device

        Args:
            new_channel (int): new channel id

        Raises:
            ValueError: Please select a valid rLine address from 1 to 9
        """
        if not (0 < new_channel_id < 10):
            raise ValueError('Please select a valid rLine address from 1 to 9.')
        response = self._query(f'*A{new_channel_id}')
        if response == 'ok':
            self.channel = new_channel_id
        return
    
    def _write(self, command:str) -> bool:
        """
        Write command to device

        Args:
            command (str): <command code><value>

        Returns:
            bool: whether command was sent successfully
        """
        fstring = f'{self.channel}{command}º\r' # command template: <PRE><ADR><CODE><DATA><LRC><POST>
        # bstring = bytearray.fromhex(fstring.encode('utf-8').hex())
        logger.debug(repr(fstring))
        try:
            # Typical timeout wait is 400ms
            self.device.write(fstring.encode('utf-8'))
        except AttributeError:
            pass
        except Exception as e:
            logger.exception(e)
            return False
        return True
    