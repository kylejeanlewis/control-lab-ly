# %% -*- coding: utf-8 -*-
"""
Adapted from @jaycecheng sartorius serial

Created: Tue 2022/12/08 11:11:00
@author: Chang Jie

Notes / actionables:
-
"""
# Standard library imports
from threading import Thread
import time

# Third party imports
import serial # pip install pyserial

# Local application imports
from ..liquid_utils import LiquidHandler
from .sartorius_lib import ErrorCode, ModelInfo, StatusCode, ERRS, STATUS_QUERIES, QUERIES
print(f"Import: OK <{__name__}>")

DEFAULT_STEPS = {
    'air_gap': 10,
    'pullback': 5
}
READ_TIMEOUT_S = 1
WETTING_CYCLES = 1

# z = 250 (w/o tip)
# z = 330 (w/ tip)
class Sartorius(LiquidHandler):
    def __init__(self, port:str, channel=1, offset=(0,0,0), **kwargs):
        super().__init__(**kwargs)
        self.channel = channel
        self.offset = offset
        
        self.device = None
        self.home_position = 0
        self.limits = (0,0)
        # self.pipette_tip_length = 0
        
        self._flags = {
            'busy': False,
            'connected': False,
            'get_feedback': False,
            'pause_feedback':False
        }
        self._levels = 0
        self._position = 0
        self._resolution = 0
        self._speed_in = 0
        self._speed_out = 0
        self._speed_codes = None
        self._status_code = ''
        self._threads = {}
        
        self._air_gap_steps = DEFAULT_STEPS['air_gap']
        self._pullback_steps = DEFAULT_STEPS['pullback']
        
        self.verbose = True
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
    def speed(self, speed_code:int, direction:str):
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
        status_codes = [s.value for s in StatusCode]
        if status_code not in status_codes:
            raise Exception(f"Please input a valid status code from: {', '.join(status_codes)}")
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
            print(f'{res}nL')
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
            self.zero()
            self.toggleFeedbackLoop(on=True)
        except Exception as e:
            if self.verbose:
                print(f"Could not connect to {port}")
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
        if response in ERRS:
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
    
    def _query(self, string:str, timeout_s=READ_TIMEOUT_S):
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
            self.setFlag('pause_feedback', True)
            time.sleep(timeout_s)
        if self.isBusy():
            time.sleep(timeout_s)
        
        message_code = self._write(string)
        _start_time = time.time()
        response = ''
        while not self._is_expected_reply(message_code, response):
            if time.time() - _start_time > timeout_s:
                break
            response = self._read()
        if message_code in QUERIES:
            response = response[2:]
        if message_code not in STATUS_QUERIES:
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
            response = response[2:-2].decode('utf-8')
            if response in ERRS:
                print(getattr(ErrorCode, response).value)
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
        self.zero()
        self.device.close()
        self._flags = {
            'busy': False,
            'connected': False,
            'get_feedback': False,
            'pause_feedback':False
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
    
    def addAirGap(self):
        """
        Create an air gap between two volumes of liquid in pipette

        Returns:
            str: device response
        """
        return self._query(f'RI{self._air_gap_steps}')
        
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
        if speed is None:
            speed = self.speed['in']
        self.setFlag('busy', True)
        volume = min(volume, self.capacity - self.volume)
        steps = int(volume / self.resolution)
        volume = steps * self.resolution
        
        if volume == 0:
            return ''
        print(f'Aspirate {volume} uL')
        response = self._query(f'RI{steps}')
        if response != 'ok':
            return response
        
        # Update values
        self.volume += volume
        if len(reagent) and len(self.reagent) == 0:
            self.reagent = reagent
        
        time.sleep(wait)
        self.setFlag('busy', False)
        if pause:
            input("Press 'Enter' to proceed.")
        return response
    
    def blowout(self, home=True):
        """
        Blowout last remaining drop in pipette

        Args:
            home (bool, optional): whether to return plunger to home position. Defaults to True.

        Returns:
            str: device response
        """
        string = f'RB{self.home_position}' if home else f'RB'
        return self._query(string)

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
        if speed is None:
            speed = self.speed['out']
        self.setFlag('busy', True)
        if force_dispense:
            volume = min(volume, self.volume)
        elif volume > self.volume:
            raise Exception('Required dispense volume is greater than volume in tip')
        steps = int(volume / self.resolution)
        volume = steps * self.resolution
        
        if volume == 0:
            return ''
        print(f'Dispense {volume} uL')
        response = self._query(f'RO{steps}')
        if response != 'ok':
            return response
        
        # Update values
        self.volume = max(self.volume - volume, 0)
        
        time.sleep(wait)
        if self.volume == 0:
            self.blowout(home=True)
        self.setFlag('busy', False)
        if pause:
            input("Press 'Enter' to proceed.")
        return response
    
    def eject(self, home=True):
        """
        Eject pipette tip

        Args:
            home (bool, optional): whether to return plunger to home position. Defaults to True.

        Returns:
            str: device response
        """
        self.reagent = ''
        string = f'RE{self.home_position}' if home else f'RE'
        return self._query(string)
    
    def getErrors(self):
        """
        Get errors from device

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
        models = [m for m in dir(ModelInfo) if not m.startswith('__') or not m.endswith('__')]
        if model not in models:
            print(f'Received: {model}')
            raise Exception(f"Please select a valid model from: {', '.join(models)}")
        info = getattr(ModelInfo, model).value
        print(info)
        
        self.limits = (info['tip_eject_position'], info['max_position'])
        self.capacity = info['capacity']
        self.home_position = info['home_position']
        self._resolution = info['resolution']
        self._speed_codes = info['speed_codes']
        return
    
    def getLiquidLevel(self):
        """
        Get the liquid level by measuring capacitance
        
        Returns:
            str: device response
        """
        response = self._query('DN')
        try:
            self._levels = int(response)
        except ValueError:
            pass
        return response
      
    def getStatus(self):
        """
        Get the device status

        Returns:
            str: device response
        """
        response = self._query('DS')
        if response in ['4','6','8']:
            self.setFlag('busy', True)
            if self.verbose:
                print(StatusCode(response).name)
        elif response in ['0']:
            self.setFlag('busy', False)
        self.status = response
        return response
    
    def home(self):
        """
        Return plunger to home position

        Returns:
            str: device response
        """
        return self._query(f'RP{self.home_position}')
    
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
    
    def move(self, axis:str, value:int):
        """
        Move plunger either up or down

        Args:
            axis (str): desired direction of plunger (up / down)
            value (int): number of steps to move plunger by

        Raises:
            Exception: Value has to be non-negative
            Exception: Axis direction either 'up' or 'down'

        Returns:
            str: device response
        """
        if value < 0:
            raise Exception("Please input non-negative value")
        if axis in ['up','u','U']:
            return self.moveBy(value)
        elif axis in ['down','d','D']:
            return self.moveBy(-value)
        else:
            raise Exception("Please select either 'up' or 'down'")
    
    def moveBy(self, steps:int):
        """
        Move plunger by specified number of steps

        Args:
            steps (int): number of steps to move plunger by (<0: move down/dispense; >0 move up/aspirate)

        Returns:
            str: device response
        """
        response = ''
        if steps > 0:
            response = self._query(f'RI{steps}')
        elif steps < 0:
            response = self._query(f'RO{-steps}')
        return response
    
    def moveTo(self, position:int):
        """
        Move plunger to specified position

        Args:
            position (int): desired plunger position

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
        return self._query(f'RI{self._pullback_steps}')
    
    def reset(self):
        """
        Alias for zero

        Returns:
            str: device response
        """
        return self.zero()

    def setFlag(self, name:str, value:bool):
        """
        Set a flag truth value

        Args:
            name (str): label
            value (bool): flag value
        """
        self._flags[name] = value
        return
    
    def toggleFeedbackLoop(self, on:bool):
        """
        Toggle between start and stopping feedback loop

        Args:
            on (bool): whether to listen to feedback
        """
        self.setFlag('get_feedback', on)
        if on:
            thread = Thread(target=self._loop_feedback)
            thread.start()
            self._threads['feedback_loop'] = thread
        else:
            self._threads['feedback_loop'].join()
        return

    def zero(self):
        """
        Zero the plunger position

        Returns:
            str: device response
        """
        response = self._query('RZ')
        time.sleep(2)
        return response
