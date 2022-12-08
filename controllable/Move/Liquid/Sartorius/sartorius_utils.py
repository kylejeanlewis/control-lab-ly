# %% -*- coding: utf-8 -*-
"""
Adapted from @jaycecheng sartorius serial

Created: Tue 2022/12/08 11:11:00
@author: Chang Jie

Notes / actionables:
-
"""
# Standard library imports
import time

# Third party imports
import serial # pip install pyserial

# Local application imports
from .. import LiquidHandler
print(f"Import: OK <{__name__}>")

DEFAULT_SPEED = 3000
PRIMING_TIME = 2
WETTING_CYCLES = 1

class Sartorius(LiquidHandler):
    def __init__(self):
        self.attr = {
            'busy': False,
            'connected': False,
            'capacity': 0,
            'reagent': '',
            'volume' : 0
        }
        return
        
    def aspirate(self, reagent, vol, speed=DEFAULT_SPEED, wait=1, pause=False):
        return
    
    def changeTip(self, tip_capacity):
        self.attr['capacity'] = tip_capacity
        return
    
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
        except Exception as e:
            if self.verbose:
                print(e)
        self.mcu = mcu
        return
    
    def cycle(self, reagent, vol, speed=DEFAULT_SPEED, wait=1):
        self.aspirate(reagent, vol, speed=speed, wait=wait)
        self.dispense(vol, speed=speed, wait=wait, force_dispense=True)
        return
    
    def dispense(self, vol, speed=DEFAULT_SPEED, wait=1, pause=False, force_dispense=False):
        return
    
    def empty(self, wait=1, pause=False):
        self.dispense(self.attr['capacity'], wait=wait, pause=pause, force_dispense=True)
        return
    
    def fill(self, reagent, prewet=True, wait=1, pause=False):
        vol = self.attr['capacity'] - self.attr['volume']

        if prewet:
            for c in range(WETTING_CYCLES):
                if c == 0:
                    self.cycle(reagent, vol=vol*1.1, wait=2)
                else:
                    self.cycle(reagent, vol=200)

        self.aspirate(reagent, vol, wait=wait, pause=pause)
        return
    
    def isBusy(self):
        return self.attr['busy']
    
    def isConnected(self):
        return self.attr['connected']
    
    def listen(self):
        return
    
    def prime(self):
        return
    
    def rinse(self, reagent, rinse_cycles=3):
        for _ in range(rinse_cycles):
            self.cycle(reagent, vol=self.attr['capacity'])
        return
    
    def update(self, field, value):
        return