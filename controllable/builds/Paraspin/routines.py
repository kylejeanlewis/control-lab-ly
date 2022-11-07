# %% -*- coding: utf-8 -*-
"""
Adapted from @jaycecheng spinutils

Created: Tue 2022/11/01 17:13:35
@author: Chang Jie

Notes / actionables:
-
"""
# Standard library imports
import numpy as np
import pandas as pd
import threading
import time

# Third party imports

# Local application imports
from ... import Make
from ... import Move
print(f"Import: OK <{__name__}>")

mover_class = Move.Cartesian.Primitiv
# mover_class = Move.Jointed.dobot.Dobot
liquid_class = Move.Liquid.SyringeAssembly
maker_class = Make.ThinFilm.SpinnerAssembly

CNC_SPEED = 250

class Setup(object):
    def __init__(self, config, ignore_connections=False):
        self.mover = None
        self.liquid = None
        self.maker = None
        self.flags = {
            'aligning': False
        }
        
        self.positions = {}
        self.rest_position = None
        
        self._config = config
        self._connect(ignore_connections=ignore_connections)
        pass
    
    def _connect(self, diagnostic=True, ignore_connections=False):
        mover_kwargs = {}
        liquid_kwargs = {}
        maker_kwargs = {}
        
        # self.mover = mover_class(**mover_kwargs)
        # self.liquid = liquid_class(**liquid_kwargs)
        # self.maker = maker_class(**maker_kwargs)
        
        self.mover = mover_class("COM8", [(-470,0,0), (0,0,0)], Z_safe=0, Z_updown=(0,0))
        self.liquid = liquid_class("COM4", [3000]*5, [3,4,5,6,7], [(x,0,0) for x in [-100,-75,-50,-25,0]])
        self.maker = maker_class(["COM16","COM15","COM14","COM13"], [0,1,2,3], [(x,0,0) for x in [-325,-250,-175,-100]])
        
        # self.mover = Move.Cartesian.Primitiv("COM8", [(-470,0,0), (0,0,0)], Z_safe=0, Z_updown=(0,0))
        # self.liquid = Move.Liquid.SyringeAssembly("COM4", [3000]*5, [3,4,5,6,7], offsets=[-100,-75,-50,-25,0])
        # self.maker
        
        if diagnostic:
            self._run_diagnostic(ignore_connections)
        return
    
    def _run_diagnostic(self, ignore_connections=False):
        connects = [self.mover.isConnected(), self.maker.isConnected(), self.liquid.isConnected()]
        if all(connects):
            print("Hardware / connection ok!")
        elif ignore_connections:
            print("Connection(s) not established. Ignoring...")
        else:
            print("Check hardware / connection!")
            return
        
        # Test self.maker
        for c,m in self.maker.channels.items():
            t = threading.Thread(target=m.execute, name=f'maker_diag_{c}')
            t.start()

        # Test self.mover
        self.home()
        self.rest()
        
        # Test liquid
        self.primeAll()
        return

    def align(self, offset, position):
        if not self.mover.isFeasible(position):
            raise Exception("Selected position is not feasible.")
        coord = np.array(position) - np.array(offset)
        self.mover.moveTo(coord)
        # self.at_home = False
        
        # Time the wait
        distance = np.linalg.norm(coord - np.array(self.mover.coordinates))
        t_align = distance / CNC_SPEED + 2
        time.sleep(t_align)
        # log_now(f'CNC align: in position')
        # self.aligning = 0
        return
    
    def coat(self, maker_chn, liquid_chn, vol, maker_kwargs, rest=True, new_thread=True):
        if vol:
            # log_now(f'CNC align: syringe {syringe.order} with spinner {spinner.order}...')
            self.align(self.liquid.channels[liquid_chn].offset, self.maker.channels[maker_chn].position)
            while self.maker.channels[maker_chn].flags['busy']:
                time.sleep(0.5)
                # return
            self.maker.channels[maker_chn].flags['busy'].busy = True
            self.liquid.dispense(liquid_chn, vol)

        # Start new thread from here
        self.maker.channels[maker_chn].etc = time.time() + 1 + sum([t for k,t in maker_kwargs.items() if 'time' in k])
        if new_thread:
            t = threading.Thread(target=self.maker.channels[maker_chn].execute, name=f'maker_{self.maker.channels[maker_chn].order}', kwargs=maker_kwargs)
            t.start()
            if rest:
                self.rest()
                self.liquid.primeAll()
            return t
        else:
            if rest:
                self.rest()
                self.liquid.prime(liquid_chn)
            self.maker.channels[maker_chn].execute(maker_kwargs)
        return
    
    def emptyLiquids(self, channels=[], wait=0, pause=False):
        if len(channels) == 0:
            channels = list(self.liquid.channels.keys())
        for channel in channels:
            # log_now(f'CNC align: syringe {syringe.order} with dump station...')
            self.align(self.liquid.channels[channel].offset, self.positions['dump'])
            self.liquid.empty(channel, wait, pause)
        return
    
    def fillLiquids(self, channels=[], reagents=[], vols=[], wait=0, pause=False):
        if len(channels) == 0:
            channels = list(self.liquid.channels.keys())
        if len(reagents) != len(channels):
            raise Exception("Please input the same number of channels and reagents.")
        if len(vols) != len(channels):
            raise Exception("Please input the same number of channels and volumes.")
        for channel,reagent,vol in zip(channels, reagents, vols):
            # log_now(f'CNC align: syringe {syringe.order} with dump station...')
            self.liquid.prime(channel)
            self.align(self.liquid.channels[channel].offset, self.positions['dump'])
            self.liquid.aspirate(channel, reagent, vol, wait=wait, pause=pause)
            self.liquid.prime(channel)
        return
    
    def home(self):
        return self.mover.home()
    
    def primeAll(self, channels=[]):
        return self.liquid.primeAll(channels)
    
    def rest(self, home=True):
        # log_now(f'CNC align: move to rest position...')
        if home:
            self.mover.home()
        else:
            self.mover.moveTo(self.rest_position)
        return
    
    def rinseAll(self, channels=[], rinse_cycles=3):
        self.emptyLiquids(channels)
        self.liquid.rinseAll(channels, rinse_cycles)
        return
    
    