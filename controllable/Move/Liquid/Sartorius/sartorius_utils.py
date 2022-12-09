# %% -*- coding: utf-8 -*-
"""
Adapted from @jaycecheng sartorius serial

Created: Tue 2022/12/08 11:11:00
@author: Chang Jie

Notes / actionables:
-
"""
# Standard library imports

# Third party imports
import serial # pip install pyserial

# Local application imports
from .. import LiquidHandler
from .sartorius_lib import ErrorCodes, SpeedCodes
print(f"Import: OK <{__name__}>")

DEFAULT_SPEED = 3000
PRIMING_TIME = 2
WETTING_CYCLES = 1

class Sartorius(LiquidHandler):
    def __init__(self, port):
        self.capacity = 0
        self.reagent = ''
        self.volume = 0
        
        self._address = 1
        self._flags = {
            'busy': False,
            'connected': False
        }
        self._speed_in = 0
        self._speed_out = 0
        self._speed_codes = None
        
        self._connect(port)
        self._get_speed_codes()
        return
    
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
        except Exception as e:
            if self.verbose:
                print(e)
        self.mcu = mcu
        return
    
    def _get_speed_codes(self):
        model = self.__model__()
        models = [m for m in dir(SpeedCodes) if not m.startswith('__') or not m.endswith('__')]
        if f'rLine_{model}' not in models:
            raise Exception(f"Please select a valid model from: {', '.join(models)}")
        self._speed_codes = getattr(SpeedCodes, model).value
        return
    
    def _query(self, string):
        self._write(string)
        return self._read()
    
    def _read(self):
        response = self.mcu.readline()
        response = response[1:-5]
        data = response[2:]
        errs = [e for e in dir(ErrorCodes)if not e.startswith('__') or not e.endswith('__')]
        if response in errs:
            print(getattr(SpeedCodes, response).value)
        else:
            print(response)
        return data
    
    def _set_address(self, new_address):
        if not 0 < new_address < 10:
            raise Exception('Please select a valid rLine address from 1 to 9')
        self.mcu.write(f'*A{new_address}')
        return
    
    def _write(self, string):
        fstring = f'{self._address}{string}º\r'
        bstring = bytearray.fromhex(fstring.encode('utf-8').hex())
        self.mcu.write(bstring)
        return
    
    def airgap(self):
        return
        
    def aspirate(self, reagent, vol, speed=DEFAULT_SPEED, wait=1, pause=False):
        steps = 5
        self._query(f'RI{steps}')
        return
    
    def blowout(self, position=None):
        self._query(f'RB')
        return
    
    def cycle(self, reagent, vol, speed=DEFAULT_SPEED, wait=1):
        self.aspirate(reagent, vol, speed=speed, wait=wait)
        self.dispense(vol, speed=speed, wait=wait, force_dispense=True)
        return
    
    def detectLevel(self):
        return self.getLiquidLevel()
    
    def dispense(self, vol, speed=DEFAULT_SPEED, wait=1, pause=False, force_dispense=False):
        steps = 5
        self._query(f'RI{steps}')
        return
    
    def eject(self, position=None):
        self._query(f'RE')
        return
    
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
        return self._query('DN')
    
    def getPosition(self):
        return self._query('DP')
      
    def getStatus(self):
        return self._query('DS')
    
    def isBusy(self):
        return self._flags['busy']
    
    def isConnected(self):
        return self._flags['connected']
    
    def listen(self):
        return
    
    def moveTo(self, position):
        self._query(f'RP{position}')
        return
    
    def prime(self):
        return
    
    def pullback(self):
        return
    
    def reset(self):
        return
    
    def residual(self):
        return
    
    def rinse(self, reagent, rinse_cycles=3):
        for _ in range(rinse_cycles):
            self.cycle(reagent, vol=self.capacity)
        return
    
    def update(self, field, value):
        return
    
    def zero(self):
        # 'RZ'
        return