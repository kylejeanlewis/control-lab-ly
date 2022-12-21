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
from .. import LiquidHandler
from .sartorius_lib import ErrorCode, ModelInfo, StatusCode, ERRS
print(f"Import: OK <{__name__}>")

READ_TIMEOUT_S = 1
STATUS_QUERIES = ['DS','DE','DP','DN']
STATIC_QUERIES = ['Dv','DM','DX','DI','DO','DR']
QUERIES = STATUS_QUERIES + STATIC_QUERIES
WETTING_CYCLES = 1

# z = 250 (w/o tip)
# z = 330 (w/ tip)
class SartoriusDevice(object):
    def __init__(self, port, channel=1, offset=(0,0,0)):
        self.capacity = 0
        self.channel = channel
        self.offset = offset
        self.reagent = ''
        self.volume = 0
        
        self.bounds = (0,0)
        self.home_position = 0
        self.mcu = None
        
        self._baudrate = 9600
        self._flags = {
            'busy': False,
            'connected': False,
            'get_feedback': False,
            'pause_feedback':False
        }
        self._levels = 0
        self._port = ''
        self._position = 0
        self._resolution = 0
        self._speed_in = 0
        self._speed_out = 0
        self._speed_codes = None
        self._status = 0
        self._threads = {}
        self._timeout = 1
        
        self.verbose = True
        self._connect(port)
        return
    
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
    def speed(self):
        speed = {
            'in': self._speed_codes[self._speed_in],
            'out': self._speed_codes[self._speed_out]
        }
        return speed
    
    @speed.setter
    def speed(self, speed_code, direction):
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
    
    def __cycles__(self):
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
        response = self._query('DM')
        print(f'Model: {response}')
        return response
    
    def __resolution__(self):
        response = self._query('DR')
        try:
            res = int(response)
            print(f'{res}nL')
            return res
        except ValueError:
            pass
        return response
    
    def __version__(self):
        return self._query('DV')
    
    def _connect(self, port):
        """
        Establish serial connection to cnc controller.
        - port: serial port of cnc Arduino
        - baudrate: 
        - timeout:
        """
        self._port = port
        mcu = None
        try:
            mcu = serial.Serial(port, self._baudrate, timeout=self._timeout)
            self.mcu = mcu
            print(f"Connection opened to {port}")
            self._flags['connected'] = True
            self._get_info()
            self._zero()
            self.startFeedbackLoop()
        except Exception as e:
            if self.verbose:
                print(e)
        return
    
    def _get_info(self):
        model = self.__model__().split('-')[0]
        models = [m for m in dir(ModelInfo) if not m.startswith('__') or not m.endswith('__')]
        if model not in models:
            print(f'Received: {model}')
            raise Exception(f"Please select a valid model from: {', '.join(models)}")
        info = getattr(ModelInfo, model).value
        
        self.bounds = (info['tip_eject_position'], info['max_position'])
        self.capacity = info['capacity']
        self.home_position = info['home_position']
        self._resolution = info['resolution']
        self._speed_codes = info['speed_codes']
        return
    
    def _is_expected_reply(self, message_code:str, response:str):
        if response in ERRS:
            return True
        if message_code not in QUERIES and response == 'ok':
            return True
        if message_code in QUERIES and response[:2] == message_code.lower():
            reply_code, data = response[:2], response[2:]
            # print(f'[{reply_code}] {data}')
            return True
        return False
    
    def _query(self, string, timeout_s=READ_TIMEOUT_S):
        message_code = string[:2]
        if message_code not in STATUS_QUERIES:
            self._flags['pause_feedback'] = True
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
            self._flags['pause_feedback'] = False
        return response

    def _read(self):
        response = ''
        try:
            response = self.mcu.readline()
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
        if not (0 < new_channel < 10):
            raise Exception('Please select a valid rLine address from 1 to 9')
        response = self._query(f'*A{new_channel}')
        if response == 'ok':
            self.channel = new_channel
        return
    
    def _shutdown(self):
        self.stopFeedbackLoop()
        self._zero()
        self.mcu.close()
        self._flags = {
            'busy': False,
            'connected': False,
            'get_feedback': False,
            'pause_feedback':False
        }
        return
    
    def _write(self, string:str):
        # Typical timeout wait is 400ms
        message_code = string[:2]
        fstring = f'{self.channel}{string}º\r'
        bstring = bytearray.fromhex(fstring.encode('utf-8').hex())
        try:
            self.mcu.write(bstring)
        except Exception as e:
            if self.verbose:
                print(e)
        return message_code
    
    def _zero(self):
        self._query('RZ')
        time.sleep(2)
        return
    
    def airgap(self, steps=10):
        return self._query(f'RI{steps}')
        
    def aspirate(self, reagent, vol, speed=0, wait=1, pause=False):
        steps = int(vol / self._resolution)
        vol = steps * self._resolution
        if speed:
            self.speed = (speed, 'in')
        
        if self._query(f'RI{steps}') != 'ok':
            return
        self.reagent = reagent
        self.volume += vol
        print(f'Aspirate {vol} uL')
        
        time.sleep(wait)
        if pause:
            input("Press 'Enter' to proceed.")
        return
    
    def blowout(self, home=True):
        string = f'RB{self.home_position}' if home else f'RB'
        return self._query(string)
    
    def connect(self):
        return self._connect(self._port)
    
    def close(self):
        return self._shutdown()
    
    def cycle(self, reagent, vol, speed=0, wait=1):
        self.aspirate(reagent, vol, speed=speed, wait=wait)
        self.dispense(vol, speed=speed, wait=wait, force_dispense=True)
        return
    
    def dispense(self, vol, speed=0, wait=1, pause=False, force_dispense=False):
        if force_dispense:
            vol = min(vol, self.volume)
        elif vol > self.volume:
            raise Exception('Required dispense volume is greater than volume in tip')
        
        steps = int(vol / self._resolution)
        vol = steps * self._resolution
        if speed:
            self.speed = (speed, 'out')
        
        if self._query(f'RO{steps}') != 'ok':
            return
        self.volume -= vol
        print(f'Dispense {vol} uL')
        
        time.sleep(wait)
        if self.volume == 0:
            self.blowout(True)
        if pause:
            input("Press 'Enter' to proceed.")
        return
    
    def eject(self, home=True):
        self.reagent = ''
        string = f'RE{self.home_position}' if home else f'RE'
        return self._query(string)
    
    def empty(self, wait=1, pause=False):
        return self.dispense(self.capacity, wait=wait, pause=pause, force_dispense=True)
    
    def feedbackLoop(self):
        print('Listening...')
        while self._flags['get_feedback']:
            if self._flags['pause_feedback']:
                continue
            self.getStatus()
            self.getLiquidLevel()
        print('Stop listening...')
        return
    
    def fill(self, reagent, prewet=True, wait=1, pause=False):
        vol = self.capacity - self.volume
        if prewet:
            for c in range(WETTING_CYCLES):
                if c == 0:
                    self.cycle(reagent, vol=vol, wait=2)
                else:
                    self.cycle(reagent, vol=200)
        self.aspirate(reagent, vol, wait=wait, pause=pause)
        return
    
    def getErrors(self):
        return self._query('DE')
    
    def getLiquidLevel(self):
        try:
            self._levels = int(self._query('DN'))
        except ValueError:
            pass
        return
      
    def getStatus(self):
        response = self._query('DS')
        if response in ['4','6','8']:
            self._flags['busy'] = True
            # print(StatusCode(response).name)
        elif response in ['0']:
            self._flags['busy'] = False
        self._status = response
        return response
    
    def home(self):
        return self._query(f'RP{self.home_position}')
    
    def isBusy(self):
        return self._flags['busy']
    
    def isConnected(self):
        return self._flags['connected']
    
    def isFeasible(self, position):
        if (self.bounds[0] < position < self.bounds[1]):
            return True
        print(f"Range limits reached! {self.bounds}")
        return False
    
    def moveBy(self, steps):
        if steps > 0:
            self._query(f'RI{steps}')
        elif steps < 0:
            self._query(f'RO{-steps}')
        return
    
    def moveTo(self, position):
        return self._query(f'RP{position}')
    
    def pullback(self, steps=5):
        return self._query(f'RI{steps}')
    
    def reset(self):
        return self._zero()
    
    def rinse(self, reagent, rinse_cycles=3):
        for _ in range(rinse_cycles):
            self.cycle(reagent, vol=self.capacity)
        return
    
    def startFeedbackLoop(self):
        self._flags['get_feedback'] = True
        t = Thread(target=self.feedbackLoop)
        t.start()
        self._threads['feedback_loop'] = t
        return
     
    def stopFeedbackLoop(self):
        self._flags['get_feedback'] = False
        self._threads['feedback_loop'].join()
        return


class Sartorius(LiquidHandler):
    def __init__(self, ports=[], channels=[], offsets=[], **kwargs):
        super().__init__(**kwargs)
        properties = list(zip(ports, channels, offsets))
        self.channels = {chn: SartoriusDevice(port, chn, off) for port,chn,off in properties}
        return
    
    def aspirate(self, channel, reagent, vol, speed=0, wait=1, pause=False):
        return self.channels[channel].aspirate(reagent, vol, speed, wait, pause)
    
    def cycle(self, channel, reagent, vol, speed=0, wait=1):
        return self.channels[channel].cycle(reagent, vol, speed, wait)
    
    def dispense(self, channel, vol, speed=0, wait=1, pause=False, force_dispense=False):
        return self.channels[channel].dispense(vol, speed, wait, pause, force_dispense)
    
    def empty(self, channel, wait=1, pause=False):
        return self.channels[channel].empty(wait, pause)
    
    def fill(self, channel, reagent, prewet=True, wait=1, pause=False):
        return self.channels[channel].fill(reagent, prewet, wait, pause)
    
    def isConnected(self):
        connects = [pipette.isConnected() for pipette in self.channels.values()]
        if all(connects):
            return True
        return False
    
    def pullback(self, channel):
        return self.channels[channel].pullback()
    
    def rinse(self, channel, reagent, rinse_cycles=3):
        return self.channels[channel].rinse(reagent, rinse_cycles)