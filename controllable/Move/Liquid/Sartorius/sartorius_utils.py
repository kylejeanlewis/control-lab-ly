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
from .sartorius_lib import ErrorCodes, ModelInfo
print(f"Import: OK <{__name__}>")

PRIMING_TIME = 2
WETTING_CYCLES = 1

class Sartorius(LiquidHandler):
    def __init__(self, port):
        super().__init__()
        self.capacity = 0
        self.reagent = ''
        self.volume = 0
        
        self.bounds = (0,0)
        self.home_position = 0
        
        self._address = 1
        self._flags = {
            'busy': False,
            'connected': False,
            'running': False
        }
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
        return self._query('DX')
    
    def __delete__(self):
        self._shutdown()
        return
    
    def __model__(self):
        return self._query('DM')
    
    def __resolution__(self):
        return self._query('DR')
    
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
            print(f"Connection opened to {port}")
            self._flags['connected'] = True
            self._flags['running'] = True
            t = Thread(target=self.listening)
            t.start()
            self._threads['listen_loop'] = t
        except Exception as e:
            if self.verbose:
                print(e)
        self.mcu = mcu
        
        self._get_info()
        self._zero()
        return
    
    def _get_info(self):
        model_id = self.__model__()
        model = f'rLine_{model_id}'
        models = [m for m in dir(ModelInfo) if not m.startswith('__') or not m.endswith('__')]
        if model not in models:
            raise Exception(f"Please select a valid model from: {', '.join(models)}")
        info = getattr(ModelInfo, model).value
        
        self.bounds = (info['tip_eject_position'], info['max_position'])
        self.capacity = int(model_id)
        self.home_position = info['home_position']
        self._resolution = info['resolution']
        self._speed_codes = info['speed_codes']
        return
    
    def _query(self, string):
        self._write(string)
        return self._read()
    
    def _read(self):
        response = ''
        try:
            response = self.mcu.readline()
            response = response[1:-5]
            errs = [e for e in dir(ErrorCodes)if not e.startswith('__') or not e.endswith('__')]
            if response in errs:
                print(getattr(ErrorCodes, response).value)
                return response
            elif response == 'ok':
                return response
            print(response)
            response = response[2:]
        except Exception as e:
            if self.verbose:
                print(e)
        return 
    
    def _set_address(self, new_address):
        if not 0 < new_address < 10:
            raise Exception('Please select a valid rLine address from 1 to 9')
        response = self._query(f'*A{new_address}')
        if response == 'ok':
            self._address = new_address
        return
    
    def _shutdown(self):
        self._flags['running'] = False
        self._threads['listen_loop'].join()
        self.mcu.close()
        return
    
    def _write(self, string):
        try:
            fstring = f'{self._address}{string}º\r'
            bstring = bytearray.fromhex(fstring.encode('utf-8').hex())
            self.mcu.write(bstring)
        except Exception as e:
            if self.verbose:
                print(e)
        return
    
    def _zero(self):
        return self._query('RZ')
    
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
            input("Press 'Enter to proceed.")
        return
    
    def blowout(self, home):
        self._query(f'RB')
        return
    
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
            # log_now(f'Syringe {self.order}: Current volume too low for required dispense', save=log)
            pass
        
        steps = int(vol / self._resolution)
        vol = steps * self._resolution
        if speed:
            self.speed = (speed, 'out')
        
        self._query(f'RI{steps}')
        self.volume -= vol
        print(f'Dispense {vol} uL')
        
        time.sleep(wait)
        if pause:
            input("Press 'Enter to proceed.")
        return
    
    def eject(self):
        return self._query(f'RE')
    
    def empty(self, wait=1, pause=False):
        self.dispense(self.capacity, wait=wait, pause=pause, force_dispense=True)
        return
    
    def fill(self, reagent, prewet=True, wait=1, pause=False):
        vol = self.capacity - self.volume

        if prewet:
            for c in range(WETTING_CYCLES):
                if c == 0:
                    self.cycle(reagent, vol=vol*1.1, wait=2)
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
        return self._query('DS')
    
    def home(self):
        return self._query(f'RP{self.home_position}')
    
    def isBusy(self):
        return self._flags['busy']
    
    def isConnected(self):
        return self._flags['connected']
    
    def listening(self):
        while self._flags['running']:
            self.getStatus()
            self.getLiquidLevel()
        print('Stop listening...')
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
    