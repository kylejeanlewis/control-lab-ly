# %% -*- coding: utf-8 -*-
"""
Adapted from @jaycecheng sartorius serial

Created: Tue 2022/12/08 11:11:00
@author: Chang Jie

Notes / actionables:
-
"""
# Standard library imports
import numpy as np
from threading import Thread
import time

# Third party imports
import serial # pip install pyserial

# Local application imports
from ..liquid_utils import LiquidHandler
from .sartorius_lib import ErrorCode, ModelInfo, StatusCode
from .sartorius_lib import ERRORS, MODELS, STATUSES, STATUS_QUERIES, QUERIES
print(f"Import: OK <{__name__}>")

DEFAULT_STEPS = {
    'air_gap': 10,
    'pullback': 5
}
READ_TIMEOUT_S = 0.3
STEP_RESOLUTION = 10
STEP_RESOLUTION_ABS = 2
TIME_RESOLUTION = 1.03
TIP_THRESHOLD = 276
WETTING_CYCLES = 1

# z = 250 (w/o tip)
# z = 330 (w/ tip)
class Sartorius(LiquidHandler):
    def __init__(self, port:str, channel=1, offset=(0,0,0), **kwargs):
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
        
        self.device = None
        self.home_position = 0
        self.limits = (0,0)
        self.implement_offset = (0,0,-250)
        self.tip_length = 0
        
        self._flags = {
            'busy': False,
            'connected': False,
            'get_feedback': False,
            'occupied': False,
            'pause_feedback':False,
            'tip_on': False
        }
        self._levels = 0
        self._position = 0
        self._resolution = 0
        self._speed_in = 3      # Default speed is setting 3
        self._speed_out = 3     # Default speed is setting 3
        self._speed_codes = None
        self._status_code = ''
        self._threads = {}
        
        self._air_gap_steps = DEFAULT_STEPS['air_gap']
        self._pullback_steps = DEFAULT_STEPS['pullback']
        
        self.verbose = False
        self.port = ''
        self._baudrate = None
        self._timeout = None
        self._connect(port)
        return
    
    @property
    def levels(self):
        response = self._query('DN')
        try:
            self._levels = int(response)
            return self._levels
        except ValueError:
            pass
        return response
    
    @property
    def position(self):
        response = self._query('DP')
        try:
            self._position = int(response)
            return self._position
        except ValueError:
            pass
        return response
    
    @property
    def resolution(self):
        return self._resolution
    
    @property
    def speed(self):
        speed = {
            'in': self._speed_codes[self._speed_in],
            'out': self._speed_codes[self._speed_out]
        }
        return speed
    @speed.setter
    def speed(self, value):
        """
        Set the intake or outflow speeds

        Args:
            value (iterable):
                speed_code (int): Preset speed code
                direction (str): 'in' or 'out'

        Raises:
            Exception: Select a valid speed code
            Exception: Select a valid direction
        """
        speed, direction = value
        speed_code = [x for x,val in enumerate(np.array(self._speed_codes)-speed) if val >= 0][0]
        print(f'Speed Code: {speed_code}')
        if not (0 < speed_code < len(self._speed_codes)):
            raise Exception(f'Please select a valid speed code from 1 to {len(self._speed_codes)-1}')
        if direction == 'in':
            self._speed_in = speed_code
            self._query(f'SI{speed_code}')
            self._query('DI')
        elif direction == 'out':
            self._speed_out = speed_code
            self._query(f'SO{speed_code}')
            self._query('DO')
        else:
            raise Exception("Please select either 'in' or 'out' for direction parameter")
        return
    
    @property
    def status(self):
        return StatusCode(self._status_code).name
    @status.setter
    def status(self, status_code:str):
        if status_code not in STATUSES:
            raise Exception(f"Please input a valid status code from: {', '.join(STATUSES)}")
        self._status_code = status_code
        return
    
    def __cycles__(self):
        """
        Retrieve total cycle lifetime

        Returns:
            int: number of lifetime cycles
        """
        response = self._query('DX')
        try:
            cycles = int(response)
            print(f'Total cycles: {cycles}')
            return cycles
        except ValueError:
            pass
        return response
    
    def __delete__(self):
        self._shutdown()
        return
    
    def __model__(self):
        """
        Retreive the model of the device

        Returns:
            str: model name
        """
        response = self._query('DM')
        print(f'Model: {response}')
        return response
    
    def __resolution__(self):
        """
        Retrieve the resolution of the device

        Returns:
            int: volume resolution of device
        """
        response = self._query('DR')
        try:
            res = int(response)
            print(f'{res/1000} uL / step')
            return res
        except ValueError:
            pass
        return response
    
    def __version__(self):
        """
        Retrieve the version of the device

        Returns:
            str: device version
        """
        return self._query('DV')

    def _calculate_speed_parameters(self, volume:int, speed:int):
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
        for standard in self._speed_codes:
            if not standard or standard < speed:
                continue
            time_interval_limit = int(volume*(1/speed - 1/standard)/TIME_RESOLUTION)
            if not step_interval_limit or not time_interval_limit:
                continue
            intervals = max(min(step_interval_limit, time_interval_limit), 1)
            each_steps = volume/self.resolution/intervals
            each_delay = volume*(1/speed - 1/standard)/intervals
            area = 0.5 * (volume**2) * (1/self.resolution) * (1/intervals) * (1/speed - 1/standard)
            outcomes[area] = {'delay': each_delay, 'intervals': intervals, 'standard': standard, 'step_size': int(each_steps)}
        if len(outcomes) == 0:
            print("No feasible speed parameters.")
            return {}
        print(f'Best parameters: {outcomes[min(outcomes)]}')
        return outcomes[min(outcomes)]
    
    def _connect(self, port:str, baudrate=9600, timeout=1):
        """
        Connect to machine control unit

        Args:
            port (str): com port address
            baudrate (int): baudrate. Defaults to 9600.
            timeout (int, optional): timeout in seconds. Defaults to None.
            
        Returns:
            serial.Serial: serial connection to machine control unit if connection is successful, else None
        """
        self.port = port
        self._baudrate = baudrate
        self._timeout = timeout
        device = None
        try:
            device = serial.Serial(port, self._baudrate, timeout=self._timeout)
            self.device = device
            print(f"Connection opened to {port}")
            self.setFlag('connected', True)
            
            self.getInfo()
            self.reset()
            self.toggleFeedbackLoop(on=False)
        except Exception as e:
            print(f"Could not connect to {port}")
            if self.verbose:
                print(e)
        return self.device
    
    def _is_expected_reply(self, message_code:str, response:str):
        """
        Check whether the response is an expected reply

        Args:
            message_code (str): two-character message code
            response (str): response string from device

        Returns:
            bool: whether the response is an expected reply
        """
        if response in ERRORS:
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
        while self._flags['get_feedback']:
            if self._flags['pause_feedback']:
                continue
            self.getStatus()
            self.getLiquidLevel()
        print('Stop listening...')
        return
    
    def _query(self, string:str, timeout_s=READ_TIMEOUT_S, resume_feedback=False):
        """
        Send query and wait for response

        Args:
            string (str): message string
            timeout_s (int, optional): duration to wait before timeout. Defaults to READ_TIMEOUT_S.

        Returns:
            str: message readout
        """
        message_code = string[:2]
        if message_code not in STATUS_QUERIES:
            if self._flags['get_feedback'] and not self._flags['pause_feedback']:
                self.setFlag('pause_feedback', True)
                time.sleep(timeout_s)
            self.getStatus()
            while self.isBusy():
                self.getStatus()
        
        start_time = time.time()
        message_code = self._write(string)
        response = ''
        while not self._is_expected_reply(message_code, response):
            if time.time() - start_time > timeout_s:
                break
            response = self._read()
        # print(time.time() - start_time)
        if message_code in QUERIES:
            response = response[2:]
        if message_code not in STATUS_QUERIES and resume_feedback:
            self.setFlag('pause_feedback', False)
        return response

    def _read(self):
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
            if response in ERRORS:
                print(ErrorCode[response].value)
                return response
            elif response == 'ok':
                return response
        except Exception as e:
            if self.verbose:
                print(e)
        return response
    
    def _set_channel(self, new_channel:int):
        """
        Set channel id of device

        Args:
            new_channel (int): new channel id

        Raises:
            Exception: Address should be between 1~9
        """
        if not (0 < new_channel < 10):
            raise Exception('Please select a valid rLine address from 1 to 9')
        response = self._query(f'*A{new_channel}')
        if response == 'ok':
            self.channel = new_channel
        return
    
    def _shutdown(self):
        """
        Close serial connection and shutdown
        """
        self.toggleFeedbackLoop(on=False)
        # self.zero()
        self.device.close()
        self._flags = {
            'busy': False,
            'connected': False,
            'get_feedback': False,
            'occupied': False,
            'pause_feedback':False,
            'tip_on': False
        }
        return
    
    def _write(self, string:str):
        """
        Sends message to device

        Args:
            string (str): <message code><value>

        Returns:
            str: two-character message code
        """
        message_code = string[:2]
        fstring = f'{self.channel}{string}º\r' # message template: <PRE><ADR><CODE><DATA><LRC><POST>
        bstring = bytearray.fromhex(fstring.encode('utf-8').hex())
        try:
            # Typical timeout wait is 400ms
            self.device.write(bstring)
        except Exception as e:
            if self.verbose:
                print(e)
        return message_code
    
    def addAirGap(self, channel=None):
        """
        Create an air gap between two volumes of liquid in pipette
        
        Args:
            channel (int, optional): channel to add air gap. Defaults to None.

        Returns:
            str: device response
        """
        response = self._query(f'RI{self._air_gap_steps}')
        time.sleep(1)
        return response
        
    def aspirate(self, volume, speed=None, wait=0, reagent='', pause=False, channel=None):
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
        self.setFlag('pause_feedback', True)
        self.setFlag('occupied', True)
        volume = min(volume, self.capacity - self.volume)
        steps = int(volume / self.resolution)
        volume = steps * self.resolution
        speed_parameters = {}
        if speed is None:
            speed = self.speed['in']
        elif speed in self._speed_codes:
            self.speed = speed,'in'
        elif speed not in self._speed_codes:
            print(volume)
            print(speed)
            speed_parameters = self._calculate_speed_parameters(volume=volume, speed=speed)
            print(speed_parameters)
            standard = speed_parameters.get('standard')
            if standard == None:
                print('Speed not feasible.')
                return
            self.speed = standard,'in'
        
        if volume == 0:
            return ''
        print(f'Aspirate {volume} uL')
        start_aspirate = time.time()
        if speed not in self._speed_codes:
            delay = speed_parameters.get('delay', TIME_RESOLUTION)
            step_size = speed_parameters.get('step_size', STEP_RESOLUTION)
            intervals = speed_parameters.get('intervals', STEP_RESOLUTION)
            for i in range(intervals):
                start_time = time.time()
                step = step_size if (i+1 != intervals) else steps
                move_time = step*self.resolution / standard
                response = self._query(f'RI{step}', resume_feedback=False)
                if response != 'ok':
                    print("Aspirate failed")
                    return response
                steps -= step
                duration = time.time() - start_time
                if duration < (delay+move_time):
                    time.sleep(delay+move_time-duration)
        else:
            response = self._query(f'RI{steps}')
            move_time = steps*self.resolution / speed
            time.sleep(move_time)
            if response != 'ok':
                return response
        print(f'Aspirate time: {time.time()-start_aspirate}s')
        
        # Update values
        self.volume += volume
        if len(reagent) and len(self.reagent) == 0:
            self.reagent = reagent
        
        time.sleep(wait)
        self.setFlag('occupied', False)
        self.setFlag('pause_feedback', False)
        if pause:
            input("Press 'Enter' to proceed.")
        return response
    
    def blowout(self, home=True, channel=None):
        """
        Blowout last remaining drop in pipette

        Args:
            home (bool, optional): whether to return plunger to home position. Defaults to True.
            channel (int, optional): channel to blowout. Defaults to None.

        Returns:
            str: device response
        """
        string = f'RB{self.home_position}' if home else f'RB'
        response = self._query(string)
        time.sleep(1)
        return response
    
    def connect(self):
        """
        Reconnect to device using existing port and baudrate
        
        Returns:
            serial.Serial: serial connection to machine control unit if connection is successful, else None
        """
        return self._connect(self.port, self._baudrate, self._timeout)
    
    def dispense(self, volume, speed=None, wait=0, force_dispense=False, pause=False, channel=None):
        """
        Dispense desired volume of reagent from channel

        Args:
            volume (int, or float): volume to be dispensed
            speed (int, optional): speed to dispense. Defaults to None.
            wait (int, optional): wait time between steps in seconds. Defaults to 0.
            force_dispense (bool, optional): whether to continue dispensing even if insufficient volume in channel. Defaults to False.
            pause (bool, optional): whether to pause for intervention / operator input. Defaults to False.
            channel (int, optional): channel to dispense. Defaults to None.

        Raises:
            Exception: Required dispense volume is greater than volume in tip

        Returns:
            str: device response
        """
        self.setFlag('pause_feedback', True)
        self.setFlag('occupied', True)
        if force_dispense:
            volume = min(volume, self.volume)
        elif volume > self.volume:
            raise Exception('Required dispense volume is greater than volume in tip')
        steps = int(volume / self.resolution)
        volume = steps * self.resolution
        speed_parameters = {}
        if speed is None:
            speed = self.speed['out']
        elif speed in self._speed_codes:
            self.speed = speed,'out'
        elif speed not in self._speed_codes:
            print(volume)
            print(speed)
            speed_parameters = self._calculate_speed_parameters(volume=volume, speed=speed)
            print(speed_parameters)
            standard = speed_parameters.get('standard')
            if standard == None:
                print('Speed not feasible.')
                return
            self.speed = standard,'out'
        
        if volume == 0:
            return ''
        print(f'Dispense {volume} uL')
        start_dispense = time.time()
        if speed not in self._speed_codes:
            delay = speed_parameters.get('delay', TIME_RESOLUTION)
            step_size = speed_parameters.get('step_size', STEP_RESOLUTION)
            intervals = speed_parameters.get('intervals', STEP_RESOLUTION)
            for i in range(intervals):
                start_time = time.time()
                step = step_size if (i+1 != intervals) else steps
                move_time = step*self.resolution / standard
                response = self._query(f'RO{step}', resume_feedback=False)
                if response != 'ok':
                    print("Dispense failed")
                    return response
                steps -= step
                duration = time.time() - start_time
                if duration < (delay+move_time):
                    time.sleep(delay+move_time-duration)
        else:
            response = self._query(f'RO{steps}')
            move_time = steps*self.resolution / speed
            time.sleep(move_time)
            if response != 'ok':
                return response
        print(f'Dispense time: {time.time()-start_dispense}s')
        
        # Update values
        self.volume = max(self.volume - volume, 0)
        
        time.sleep(wait)
        if self.volume == 0:
            self.blowout(home=True)
        self.setFlag('occupied', False)
        self.setFlag('pause_feedback', False)
        if pause:
            input("Press 'Enter' to proceed.")
        return response
    
    def eject(self, home=True, channel=None):
        """
        Eject pipette tip

        Args:
            home (bool, optional): whether to return plunger to home position. Defaults to True.
            channel (int, optional): channel to eject. Defaults to None.

        Returns:
            str: device response
        """
        self.reagent = ''
        string = f'RE{self.home_position}' if home else f'RE'
        response = self._query(string)
        time.sleep(1)
        return response
    
    def getErrors(self, channel=None):
        """
        Get errors from device
        
        Args:
            channel (int, optional): channel to get errors. Defaults to None.

        Returns:
            str: device response
        """
        return self._query('DE')
    
    def getInfo(self):
        """
        Get model info

        Raises:
            Exception: Select a valid model name
        """
        model = self.__model__().split('-')[0]
        if model not in MODELS:
            print(f'Received: {model}')
            raise Exception(f"Please select a valid model from: {', '.join(MODELS)}")
        info = ModelInfo[model].value
        print(info)
        
        self.limits = (info['tip_eject_position'], info['max_position'])
        self.capacity = info['capacity']
        self.home_position = info['home_position']
        self._resolution = info['resolution']
        self._speed_codes = info['speed_codes']
        return
    
    def getLiquidLevel(self, channel=None):
        """
        Get the liquid level by measuring capacitance
        
        Args:
            channel (int, optional): channel to get liquid level. Defaults to None.
        
        Returns:
            str: device response
        """
        response = self._query('DN')
        try:
            self._levels = int(response)
        except ValueError:
            pass
        return response
      
    def getStatus(self, channel=None):
        """
        Get the device status
        
        Args:
            channel (int, optional): channel to get status. Defaults to None.

        Returns:
            str: device response
        """
        response = self._query('DS')
        try:
            response = int(response)
        except ValueError as e:
            if self.verbose:
                print(e)
            return response
        if response in ['4','6','8']:
            self.setFlag('busy', True)
            if self.verbose:
                print(StatusCode(response).name)
        elif response in ['0']:
            self.setFlag('busy', False)
        self.status = response
        return response
    
    def home(self, channel=None):
        """
        Return plunger to home position
        
        Args:
            channel (int, optional): channel to home. Defaults to None.

        Returns:
            str: device response
        """
        response = self._query(f'RP{self.home_position}')
        time.sleep(1)
        return response
    
    def isBusy(self):
        """
        Checks whether the pipette is busy
        
        Returns:
            bool: whether the pipette is busy
        """
        return self._flags['busy']
    
    def isConnected(self):
        """
        Check whether pipette is connected

        Returns:
            bool: whether pipette is connected
        """
        return self._flags['connected']
    
    def isFeasible(self, position:int):
        """
        Checks if specified position is a feasible position for plunger to access

        Args:
            position (int): plunger position

        Returns:
            bool: whether plunger position is feasible
        """
        if (self.limits[0] < position < self.limits[1]):
            return True
        print(f"Range limits reached! {self.limits}")
        return False
    
    def isTipOn(self):
        """
        Checks whether tip is on
        
        Returns:
            bool: whether the tip in on
        """
        self.getLiquidLevel()
        print(f'Tip capacitance: {self._levels}')
        # tip_on = (self._levels > TIP_THRESHOLD)
        # self.setFlag('tip_on', tip_on)
        tip_on = self._flags.get('tip_on')
        return tip_on
    
    def move(self, axis:str, value:int, channel=None):
        """
        Move plunger either up or down

        Args:
            axis (str): desired direction of plunger (up / down)
            value (int): number of steps to move plunger by
            channel (int, optional): channel to move. Defaults to None.
        Raises:
            Exception: Value has to be non-negative
            Exception: Axis direction either 'up' or 'down'

        Returns:
            str: device response
        """
        if value < 0:
            raise Exception("Please input non-negative value")
        if axis.lower() in ['up','u']:
            return self.moveBy(value)
        elif axis.lower() in ['down','d']:
            return self.moveBy(-value)
        else:
            raise Exception("Please select either 'up' or 'down'")
    
    def moveBy(self, steps:int, channel=None):
        """
        Move plunger by specified number of steps

        Args:
            steps (int): number of steps to move plunger by (<0: move down/dispense; >0 move up/aspirate)
            channel (int, optional): channel to move by. Defaults to None.

        Returns:
            str: device response
        """
        response = ''
        if steps > 0:
            response = self._query(f'RI{steps}')
        elif steps < 0:
            response = self._query(f'RO{-steps}')
        return response
    
    def moveTo(self, position:int, channel=None):
        """
        Move plunger to specified position

        Args:
            position (int): desired plunger position
            channel (int, optional): channel to move to. Defaults to None.

        Returns:
            str: device response
        """
        return self._query(f'RP{position}')
    
    def pullback(self, channel=None):
        """
        Pullback liquid from tip
        
        Args:
            channel (int, optional): channel to pullback. Defaults to None.

        Returns:
            str: device response
        """
        response = self._query(f'RI{self._pullback_steps}')
        time.sleep(1)
        return response
    
    def reset(self, channel=None):
        """
        Zeros and go back to home position
        
        Args:
            channel (int, optional): channel to reset. Defaults to None.

        Returns:
            str: device response
        """
        self.zero()
        return self.home()

    def setFlag(self, name:str, value:bool):
        """
        Set a flag truth value

        Args:
            name (str): label
            value (bool): flag value
        """
        self._flags[name] = value
        return
    
    def toggleFeedbackLoop(self, on:bool, channel=None):
        """
        Toggle between start and stopping feedback loop
        
        Args:
            channel (int, optional): channel to toggle feedback loop. Defaults to None.

        Args:
            on (bool): whether to listen to feedback
        """
        self.setFlag('get_feedback', on)
        if on:
            thread = Thread(target=self._loop_feedback)
            thread.start()
            self._threads['feedback_loop'] = thread
        else:
            if 'feedback_loop' in self._threads:
                self._threads['feedback_loop'].join()
        return

    def zero(self, channel=None):
        """
        Zero the plunger position
        
        Args:
            channel (int, optional): channel to zero. Defaults to None.

        Returns:
            str: device response
        """
        self.eject()
        response = self._query('RZ')
        time.sleep(2)
        return response
