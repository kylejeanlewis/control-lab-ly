# %% -*- coding: utf-8 -*-
"""
Adapted from @jaycecheng sartorius serial

Created: Tue 2022/12/08 11:11:00
@author: Chang Jie

Notes / actionables:
-
"""
# Standard library imports
from __future__ import annotations
import numpy as np
from threading import Thread
import time
from typing import Optional, Union

# Third party imports
import serial # pip install pyserial

# Local application imports
from ..liquid_utils import LiquidHandler, Speed
from .sartorius_lib import ErrorCode, ModelInfo, StatusCode, SpeedParameters, Model
from .sartorius_lib import STATUS_QUERIES, QUERIES
print(f"Import: OK <{__name__}>")

STEP_RESOLUTION = 10

class Sartorius(LiquidHandler):
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
        response_time: float = 1.03,        # Empirical: minimum drive response time [s]
        tip_threshold: int = 276,           # Empirical: capacitance value above which tip is attached
        **kwargs
    ):
        """
        Sartorius object

        Args:
            port (str): com port address
            channel (int, optional): device channel. Defaults to 1.
            offset (tuple, optional): x,y,z offset of tip. Defaults to (0,0,0).
        """
        super().__init__(**kwargs)
        self.channel = channel
        self.offset = offset
        self.response_time = response_time
        self.tip_threshold = tip_threshold
        
        self.model_info: Model = None
        self.limits = (0,0)
        self.position = 0
        self.speed_code = Speed(3,3)
        self.speed_presets = None
        self.tip_length = 0
        
        self._capacitance = 0
        self._status_code = ''
        self._threads = {}
        
        print("Any attached pipette tip may drop during initialisation.")
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
    
    def __cycles__(self) -> Union[int, str]:
        """
        Retrieve total cycle lifetime

        Returns:
            int: number of lifetime cycles
        """
        response = self._query('DX')
        try:
            cycles = int(response)
        except ValueError:
            return response
        print(f'Total cycles: {cycles}')
        return cycles
    
    def __model__(self) -> str:
        """
        Retreive the model of the device

        Returns:
            str: model name
        """
        response = self._query('DM')
        print(f'Model: {response}')
        return response
    
    def __resolution__(self) -> Union[int, str]:
        """
        Retrieve the resolution of the device

        Returns:
            int: volume resolution of device in nL
        """
        response = self._query('DR')
        try:
            resolution = int(response)
        except ValueError:
            return response
        print(f'{resolution/1000} uL / step')
        return resolution
    
    def __version__(self) -> str:
        """
        Retrieve the version of the device

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
        Aspirate desired volume of reagent into channel

        Args:
            volume (int, or float): volume to be aspirated
            speed (int, optional): speed to aspirate. Defaults to None.
            wait (int, optional): wait time between steps in seconds. Defaults to 0.
            reagent (str, optional): name of reagent. Defaults to ''.
            pause (bool, optional): whether to pause for intervention / operator input. Defaults to False.
            channel (int, optional): channel to aspirate. Defaults to None.
            
        Returns:
            str: device response
        """ 
        self.setFlag(pause_feedback=True, occupied=True)
        volume = min(volume, self.capacity - self.volume)
        steps = int(volume / self.resolution)
        volume = steps * self.resolution
        if volume == 0:
            return ''
        print(f'Aspirating {volume} uL...')
        start_aspirate = time.time()
        speed = self.speed.up if speed is None else speed
        
        if speed in self.speed_presets:
            if speed != self.speed.up:
                self.setSpeed(speed=speed, up=True)
                self.speed.up = speed
            start_aspirate = time.time()
            response = self._query(f'RI{steps}')
            move_time = steps*self.resolution / speed
            time.sleep(move_time)
            # if response != 'ok':
            #     return response
            
        elif speed not in self.speed_presets:
            print(f"Target: {volume} uL at {speed} uL/s...")
            speed_parameters = self._calculate_speed_parameters(volume=volume, speed=speed)
            print(speed_parameters)
            preset = speed_parameters.preset
            if preset is None:
                raise RuntimeError('Target speed not possible.')
            self.setSpeed(speed=preset, up=True)
            self.speed.up = speed
            start_aspirate = time.time()
            
            steps_left = steps
            delay = speed_parameters.delay
            step_size = speed_parameters.step_size
            intervals = speed_parameters.intervals
            for i in range(intervals):
                start_time = time.time()
                step = step_size if (i+1 != intervals) else steps_left
                move_time = step*self.resolution / preset
                response = self._query(f'RI{step}', resume_feedback=False)
                # if response != 'ok':
                #     print("Aspiration failed")
                #     return response
                steps_left -= step
                duration = time.time() - start_time
                if duration < (delay+move_time):
                    time.sleep(delay+move_time-duration)
        
        # Update values
        print(f'Aspiration time: {time.time()-start_aspirate}s')
        time.sleep(wait)
        self.setFlag(occupied=False, pause_feedback=False)
        self.volume += volume
        self.position += steps
        if reagent is not None:
            self.reagent = reagent
        if pause:
            input("Press 'Enter' to proceed.")
        return response
    
    def blowout(self, home:bool = True, **kwargs) -> str:
        """
        Blowout last remaining drop in pipette

        Args:
            home (bool, optional): whether to return plunger to home position. Defaults to True.
            channel (int, optional): channel to blowout. Defaults to None.

        Returns:
            str: device response
        """
        message = f'RB{self.home_position}' if home else 'RB'
        response = self._query(message)
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
        Dispense desired volume of reagent from channel

        Args:
            volume (int, or float): volume to be dispensed
            speed (int, optional): speed to dispense. Defaults to None.
            wait (int, optional): wait time between steps in seconds. Defaults to 0.
            force_dispense (bool, optional): whether to continue dispensing even if insufficient volume in channel. Defaults to False.
            pause (bool, optional): whether to pause for intervention / operator input. Defaults to False.
            blowout (bool, optional): whether to perform blowout when volume reaches zero. Defaults to True.
            blowout_home (bool, optional): whether to home the plunger after blowout. Defaults to True.
            channel (int, optional): channel to dispense. Defaults to None.

        Raises:
            Exception: Required dispense volume is greater than volume in tip

        Returns:
            str: device response
        """
        self.setFlag(pause_feedback=True, occupied=True)
        if force_dispense:
            volume = min(volume, self.volume)
        elif volume > self.volume:
            raise Exception('Required dispense volume is greater than volume in tip')
        steps = int(volume / self.resolution)
        volume = steps * self.resolution
        if volume == 0:
            return ''
        print(f'Dispensing {volume} uL...')
        start_dispense = time.time()
        speed = self.speed.down if speed is None else speed

        if speed in self.speed_presets:
            if speed != self.speed.down:
                self.setSpeed(speed=speed, up=False)
                self.speed.down = speed
            start_dispense = time.time()
            response = self._query(f'RO{steps}')
            move_time = steps*self.resolution / speed
            time.sleep(move_time)
            # if response != 'ok':
            #     return response
            
        elif speed not in self.speed_presets:
            print(f"Target: {volume} uL at {speed} uL/s...")
            speed_parameters = self._calculate_speed_parameters(volume=volume, speed=speed)
            print(speed_parameters)
            preset = speed_parameters.preset
            if preset is None:
                raise RuntimeError('Target speed not possible.')
            self.setSpeed(speed=preset, up=False)
            self.speed.down = speed
            start_dispense = time.time()
        
            steps_left = steps
            delay = speed_parameters.delay
            step_size = speed_parameters.step_size
            intervals = speed_parameters.intervals
            for i in range(intervals):
                start_time = time.time()
                step = step_size if (i+1 != intervals) else steps_left
                move_time = step*self.resolution / preset
                response = self._query(f'RO{step}', resume_feedback=False)
                # if response != 'ok':
                #     print("Dispense failed")
                #     return response
                steps_left -= step
                duration = time.time() - start_time
                if duration < (delay+move_time):
                    time.sleep(delay+move_time-duration)

        # Update values
        print(f'Dispense time: {time.time()-start_dispense}s')
        time.sleep(wait)
        self.setFlag(occupied=False, pause_feedback=False)
        self.volume = max(self.volume - volume, 0)
        self.position -= steps
        if self.volume == 0 and blowout:
            self.blowout(home=blowout_home)
        if pause:
            input("Press 'Enter' to proceed.")
        return response
    
    def eject(self, home:bool = True) -> str:
        """
        Eject pipette tip

        Args:
            home (bool, optional): whether to return plunger to home position. Defaults to True.
            channel (int, optional): channel to eject. Defaults to None.

        Returns:
            str: device response
        """
        self.reagent = ''
        message = f'RE{self.home_position}' if home else 'RE'
        response = self._query(message)
        self.position = self.home_position if home else 0
        time.sleep(1)
        return response
    
    def empty(self, **kwargs):
        return self.home()
    
    def getCapacitance(self) -> Union[int, str]:
        """
        Get the liquid level by measuring capacitance
        
        Args:
            channel (int, optional): channel to get liquid level. Defaults to None.
        
        Returns:
            str: device response
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
        Get errors from device
        
        Args:
            channel (int, optional): channel to get errors. Defaults to None.

        Returns:
            str: device response
        """
        return self._query('DE')
    
    def getInfo(self, model: Optional[str] = None):
        """
        Get model info

        Raises:
            Exception: Select a valid model name
        """
        model = self.__model__().split('-')[0] if model is None else model
        if model not in ModelInfo._member_names_:
            print(f'Received: {model}')
            model = 'BRL0'
            print(f"Defaulting to: {'BRL0'}")
            print(f"Valid models are: {', '.join(ModelInfo._member_names_)}")
        info: Model = ModelInfo[model].value
        print(info)
        self.model_info = info
        self.capacity = info.capacity
        self.limits = (info.tip_eject_position, info.max_position)
        self.speed_presets = info.preset_speeds
        self.speed.up = self.speed_presets[self.speed_code.up]
        self.speed.down = self.speed_presets[self.speed_code.down]
        return
    
    def getPosition(self, **kwargs) -> int:
        response = self._query('DP')
        try:
            position = int(response)
        except ValueError:
            return response
        self.position = position
        return self.position
      
    def getStatus(self, **kwargs) -> str:
        """
        Get the device status
        
        Args:
            channel (int, optional): channel to get status. Defaults to None.

        Returns:
            str: device response
        """
        response = self._query('DS')
        try:
            status = int(response)
        except ValueError:
            return response
        if response not in [_status.value for _status in StatusCode]:
            return response
        
        self._status_code = status
        if status in [4,6,8]:
            self.setFlag(busy=True)
            if self.verbose:
                print(StatusCode(status).name)
        elif status == 0:
            self.setFlag(busy=False)
        return StatusCode(self._status_code).name
    
    def home(self) -> str:
        """
        Return plunger to home position
        
        Args:
            channel (int, optional): channel to home. Defaults to None.

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
        Checks if specified position is a feasible position for plunger to access

        Args:
            position (int): plunger position

        Returns:
            bool: whether plunger position is feasible
        """
        if (self.limits[0] <= position <= self.limits[1]):
            return True
        print(f"Range limits reached! {self.limits}")
        return False
    
    def isTipOn(self) -> bool:
        """
        Checks whether tip is on
        
        Returns:
            bool: whether the tip in on
        """
        self.getCapacitance()
        print(f'Tip capacitance: {self.capacitance}')
        if self.flags['conductive_tips']:
            tip_on = (self.capacitance > self.tip_threshold)
            self.setFlag(tip_on=tip_on)
        tip_on = self.flags['tip_on']
        return tip_on
    
    def move(self, direction:str, steps:int, **kwargs) -> str:
        """
        Move plunger either up or down

        Args:
            direction (str): desired direction of plunger (up / down)
            value (int): number of steps to move plunger by
            channel (int, optional): channel to move. Defaults to None.
        Raises:
            Exception: Value has to be non-negative
            Exception: Axis direction either 'up' or 'down'

        Returns:
            str: device response
        """
        steps = abs(steps)
        if direction.lower() in ['up','u']:
            steps *= 1
        elif direction.lower() in ['down','d']:
            steps *= -1
        else:
            raise Exception("Please select either 'up' or 'down'")
        return self.moveBy(steps)
    
    def moveBy(self, steps:int, **kwargs) -> str:
        """
        Move plunger by specified number of steps

        Args:
            steps (int): number of steps to move plunger by (<0: move down/dispense; >0 move up/aspirate)
            channel (int, optional): channel to move by. Defaults to None.

        Returns:
            str: device response
        """
        message = f'RI{steps}' if steps > 0 else f'RO{-steps}'
        self.position += steps
        return self._query(message)
    
    def moveTo(self, position:int, **kwargs) -> str:
        """
        Move plunger to specified position

        Args:
            position (int): desired plunger position
            channel (int, optional): channel to move to. Defaults to None.

        Returns:
            str: device response
        """
        self.position = position
        return self._query(f'RP{position}')
    
    def pullback(self, steps:int = 5, **kwargs) -> str:
        """
        Pullback liquid from tip
        
        Args:
            steps (int, optional): number of steps to pullback. Defaults to DEFAULT_PULLBACK.
            channel (int, optional): channel to pullback. Defaults to None.

        Returns:
            str: device response
        """
        response = self._query(f'RI{steps}')
        self.position += steps
        time.sleep(1)
        return response
    
    def reset(self) -> str:
        """
        Zeros and go back to home position
        
        Args:
            channel (int, optional): channel to reset. Defaults to None.

        Returns:
            str: device response
        """
        self.zero()
        return self.home()
    
    def setSpeed(self, speed:int, up:bool, **kwargs) -> str:
        speed_code = 1 + [x for x,val in enumerate(np.array(self.speed_presets)-speed) if val >= 0][0]
        print(f'Speed {speed_code}: {self.speed_presets[speed_code-1]} uL/s')
        direction = 'I' if up else 'O'
        self._query(f'S{direction}{speed_code}')
        if up:
            self.speed_code.up = speed_code
            # self.speed.up = speed
        else:
            self.speed_code.down = speed_code
            # self.speed.down = speed
        return self._query(f'D{direction}')
    
    def shutdown(self):
        """
        Close serial connection and shutdown
        """
        self.toggleFeedbackLoop(on=False)
        return super().shutdown()
    
    def toggleFeedbackLoop(self, on:bool):
        """
        Toggle between start and stopping feedback loop
        
        Args:
            channel (int, optional): channel to toggle feedback loop. Defaults to None.

        Args:
            on (bool): whether to listen to feedback
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
        
        Args:
            channel (int, optional): channel to zero. Defaults to None.

        Returns:
            str: device response
        """
        self.eject()
        response = self._query('RZ')
        self.position = 0
        time.sleep(2)
        return response

    # Protected method(s)
    def _calculate_speed_parameters(self, volume:int, speed:int) -> SpeedParameters:
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
            if not step_interval_limit or not time_interval_limit:
                continue
            intervals = max(min(step_interval_limit, time_interval_limit), 1)
            each_steps = volume/self.resolution/intervals
            each_delay = volume*(1/speed - 1/preset)/intervals
            area = 0.5 * (volume**2) * (1/self.resolution) * (1/intervals) * (1/speed - 1/preset)
            outcomes[area] = SpeedParameters(preset, intervals, int(each_steps), each_delay)
        if len(outcomes) == 0:
            print("No feasible speed parameters.")
            return SpeedParameters(None, STEP_RESOLUTION, STEP_RESOLUTION, self.response_time)
        print(f'Best parameters: {outcomes[min(outcomes)]}')
        return outcomes[min(outcomes)]
    
    def _connect(self, port:str, baudrate:int = 9600, timeout:int = 1):
        """
        Connect to machine control unit

        Args:
            `port` (str): com port address
            `baudrate` (int, optional): baudrate. Defaults to 9600.
            `timeout` (int, optional): timeout in seconds. Defaults to 1.
            
        Returns:
            `serial.Serial`: serial connection to machine control unit if connection is successful, else `None`
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
            print(f"Could not connect to {port}")
            if self.verbose:
                print(e)
        else:
            time.sleep(2)   # Wait for grbl to initialize
            device.flushInput()
            print(f"Connection opened to {port}")
            self.setFlag(connected=True)
        self.getInfo()
        self.reset()
        self.device = device
        return
    
    def _is_expected_reply(self, response:str, message_code:str, **kwargs) -> bool:
        """
        Check whether the response is an expected reply

        Args:
            message_code (str): two-character message code
            response (str): response string from device

        Returns:
            bool: whether the response is an expected reply
        """
        if response in ErrorCode._member_names_:
            return True
        if message_code not in QUERIES and response == 'ok':
            return True
        if message_code in QUERIES and response[:2] == message_code.lower():
            reply_code, data = response[:2], response[2:]
            if self.verbose:
                print(f'[{reply_code}] {data}')
            return True
        return False

    def _loop_feedback(self):
        """
        Feedback loop to constantly check status and liquid level
        """
        print('Listening...')
        while self.flags['get_feedback']:
            if self.flags['pause_feedback']:
                continue
            self.getStatus()
            self.getCapacitance()
        print('Stop listening...')
        return
    
    def _query(self, 
        message: str, 
        timeout_s: float = 0.3, 
        resume_feedback: bool = False
    ) -> str:
        """
        Send query and wait for response

        Args:
            message (str): message string
            timeout_s (int, optional): duration to wait before timeout. Defaults to 0.3.

        Returns:
            str: message readout
        """
        message_code = message[:2]
        if message_code not in STATUS_QUERIES:
            if self.flags['get_feedback'] and not self.flags['pause_feedback']:
                self.setFlag(pause_feedback=True)
                time.sleep(timeout_s)
            self.getStatus()
            while self.isBusy():
                self.getStatus()
        
        start_time = time.time()
        self._write(message)
        response = ''
        while not self._is_expected_reply(response, message_code):
            if time.time() - start_time > timeout_s:
                break
            response = self._read()
        # print(time.time() - start_time)
        if message_code in QUERIES:
            response = response[2:]
        if message_code not in STATUS_QUERIES:
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
            response = response[2:-2].decode('utf-8')
        except AttributeError:
            pass
        except Exception as e:
            if self.verbose:
                print(e)
        if response in ErrorCode._member_names_:
            print(ErrorCode[response].value)
        return response
    
    def _set_channel_id(self, new_channel_id:int):
        """
        Set channel id of device

        Args:
            new_channel (int): new channel id

        Raises:
            Exception: Address should be between 1~9
        """
        if not (0 < new_channel_id < 10):
            raise Exception('Please select a valid rLine address from 1 to 9')
        response = self._query(f'*A{new_channel_id}')
        if response == 'ok':
            self.channel = new_channel_id
        return
    
    def _write(self, message:str) -> bool:
        """
        Sends message to device

        Args:
            message (str): <message code><value>

        Returns:
            str: two-character message code
        """
        if self.verbose:
            print(message)
        fstring = f'{self.channel}{message}º\r' # message template: <PRE><ADR><CODE><DATA><LRC><POST>
        # bstring = bytearray.fromhex(fstring.encode('utf-8').hex())
        try:
            # Typical timeout wait is 400ms
            self.device.write(fstring.encode('utf-8'))
        except AttributeError:
            pass
        except Exception as e:
            if self.verbose:
                print(e)
            return False
        return True
    