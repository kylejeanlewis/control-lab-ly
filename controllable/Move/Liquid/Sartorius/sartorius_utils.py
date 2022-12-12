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
from .sartorius_lib import ErrorCode, ModelInfo, StatusCode
print(f"Import: OK <{__name__}>")

STATUS_QUERIES = ['DS','DE','DP','DN']
STATIC_QUERIES = ['Dv','DM','DX','DI','DO','DR']
WETTING_CYCLES = 1

class Sartorius(LiquidHandler):
    def __init__(self, port):
        super().__init__()
        self.capacity = 0
        self.reagent = ''
        self.volume = 0
        
        self.bounds = (0,0)
        self.home_position = 0
        self.mcu = None
        
        self._address = 1
        self._flags = {
            'busy': False,
            'connected': False,
            'feedback': False,
            'incoming':False,
            'listen': False
        }
        self._message_pool = {}
        self._resolution = 0
        self._speed_in = 0
        self._speed_out = 0
        self._speed_codes = None
        self._threads = {}
        
        self.verbose = True
        self._connect(port)
        return
    
    @property
    def position(self):
        return self.getPosition()
    
    @property
    def speed(self):
        speed = {
            'in': self._speed_codes[self._speed_in],
            'out': self._speed_codes[self._speed_out]
        }
        return speed
    
    @speed.setter
    def speed(self, speed_code, direction):
        if not 0 < speed_code < len(self._speed_codes):
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
        print(f'Total cycles: {response}')
        return int(response)
    
    def __delete__(self):
        self._shutdown()
        return
    
    def __model__(self):
        response = self._query('DM')
        print(response)
        return response
    
    def __resolution__(self):
        response = self._query('DR')
        print(f'{response}nL')
        return int(response)
    
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
        self._baudrate = 9600
        self._timeout = 1
        mcu = None
        try:
            mcu = serial.Serial(port, 9600, timeout=1)
            self.mcu = mcu
            print(f"Connection opened to {port}")
            self._get_info()
            self._zero()
            
            self._flags['connected'] = True
            self.startListening()
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
    
    def _query(self, string, timeout_s=0.4):
        _start_time = time.time()
        message_code = self._write(string)
        if message_code not in STATUS_QUERIES+STATIC_QUERIES:
            message_code = 'main'
        self._message_pool[message_code] = ''
        
        # Reading from message pool
        while len(self._message_pool[message_code])==0:
            if time.time() - _start_time > timeout_s:
                self._message_pool[message_code] = 'er4' # timeout error
                break
        response = self._message_pool.pop(message_code, '')
        if message_code not in STATUS_QUERIES:
            print(f'{response} [{string}]')
        return response

    def _read(self):
        response = ''
        try:
            response = self.mcu.readline()
            response = response[2:-2].decode('utf-8')
            errs = [e for e in dir(ErrorCode)if not e.startswith('__') or not e.endswith('__')]
            if response in errs:
                print(getattr(ErrorCode, response).value)
                for key in self._message_pool.keys():
                    self._message_pool[key] = response
                return response
            elif response == 'ok':
                self._message_pool['main'] = response
                return response
            # print(response)
            message_code = response[:2].upper()
            response = response[2:]
            self._message_pool[message_code] = response
        except Exception as e:
            if self.verbose:
                print(e)
        return response
    
    def _set_address(self, new_address:int):
        if not 0 < new_address < 10:
            raise Exception('Please select a valid rLine address from 1 to 9')
        response = self._query(f'*A{new_address}')
        if response == 'ok':
            self._address = new_address
        return
    
    def _shutdown(self):
        self.stopListening()
        self._zero()
        self.mcu.close()
        self._flags = {
            'busy': False,
            'connected': False,
            'feedback': False,
            'incoming':False,
            'listen': False
        }
        return
    
    def _write(self, string:str):
        # Typical timeout wait is 400ms
        message_code = string[:2]
        fstring = f'{self._address}{string}º\r'
        bstring = bytearray.fromhex(fstring.encode('utf-8').hex())
        try:
            if message_code not in STATUS_QUERIES:
                self._flags['incoming'] = True
            while self._flags['busy']:# and string not in STATUS_QUERIES:
                time.sleep(0.1)
            self.mcu.write(bstring)
            if message_code not in STATUS_QUERIES:
                self._flags['incoming'] = False
        except Exception as e:
            if self.verbose:
                print(e)
        return message_code
    
    def _zero(self):
        self._query('RZ')
        time.sleep(2)
        return
    
    def airgap(self):
        return self._query(f'RI{5}')
        
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
        string = f'RE{self.home_position}' if home else f'RE'
        return self._query(string)
    
    def empty(self, wait=1, pause=False):
        self.dispense(self.capacity, wait=wait, pause=pause, force_dispense=True)
        self.reagent = ''
        return
    
    def feedbackLoop(self):
        while self._flags['feedback']:
            if self._flags['incoming']:
                self._flags['busy'] = False
                continue
            self.getStatus()
            self.getLiquidLevel()
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
        return int(self._query('DN'))
    
    def getPosition(self):
        return int(self._query('DP'))
      
    def getStatus(self):
        response = int(self._query('DS'))
        if response in [4,6,8]:
            self._flags['busy'] = True
            print(StatusCode(int(response)).name)
        elif response in [0]:
            self._flags['busy'] = False
        return response
    
    def home(self):
        return self._query(f'RP{self.home_position}')
    
    def isBusy(self):
        return self._flags['busy']
    
    def isConnected(self):
        return self._flags['connected']
    
    def listening(self):
        print('Listening...')
        while self._flags['listen']:
            self._read()
        print('Stop listening...')
        return
    
    def moveBy(self, displacement):
        if displacement > 0:
            self._query(f'RI{displacement}')
        elif displacement < 0:
            self._query(f'RO{-displacement}')
        return
    
    def moveTo(self, position):
        return self._query(f'RP{position}')
    
    def pullback(self):
        return self._query(f'RI{5}')
    
    def reset(self):
        return self._zero()
    
    def rinse(self, reagent, rinse_cycles=3):
        for _ in range(rinse_cycles):
            self.cycle(reagent, vol=self.capacity)
        return
    
    def startFeedbackLoop(self):
        self._flags['feedback'] = True
        t = Thread(target=self.feedbackLoop)
        t.start()
        self._threads['feedback_loop'] = t
        return
    
    def startListening(self):
        self._flags['listen'] = True
        t = Thread(target=self.listening)
        t.start()
        self._threads['listen_loop'] = t
        return
    
    def stopFeedbackLoop(self):
        self._flags['feedback'] = False
        self._threads['feedback_loop'].join()
        return
    
    def stopListening(self):
        self._flags['listen'] = False
        self._threads['listen_loop'].join()
        return
    