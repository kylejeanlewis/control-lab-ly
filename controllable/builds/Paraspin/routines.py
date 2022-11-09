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
        
        self._config = config
        self._connect(ignore_connections=ignore_connections)
        pass
    
    def _checkInputs(self, **kwargs):
        keys = list(kwargs.keys())
        if any(len(kwargs[key]) != len(kwargs[keys[0]]) for key in keys):
            raise Exception(f"Ensure the lengths of these inputs are the same: {', '.join(keys)}")
        return
    
    def _checkPositions(self, wait=2, pause=False):
        for maker_chn in self.maker.channels.values():
            for liquid_chn in self.liquid.channels.values():
                self.align(liquid_chn.offset, maker_chn.position)
                time.sleep(wait)
                if pause:
                    input("Press 'Enter to proceed.")
        return
    
    def _connect(self, diagnostic=True, ignore_connections=False):
        self.mover = mover_class(**self._config['mover_settings'])
        self.liquid = liquid_class(**self._config['liquid_settings'])
        self.maker = maker_class(**self._config['maker_settings'])

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
            thread = threading.Thread(target=m.execute, name=f'maker_diag_{c}')
            thread.start()

        # Test self.mover
        self.home()
        self._checkPositions()
        self.rest()
        
        # Test liquid
        self.primeAll()
        return

    def align(self, offset, position):
        coord = np.array(position) - np.array(offset)
        if not self.mover.isFeasible(coord):
            raise Exception("Selected position is not feasible.")
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
        self.maker.channels[maker_chn].etc = time.time() + 1 + sum([v for k,v in maker_kwargs.items() if 'time' in k])
        if new_thread:
            thread = threading.Thread(target=self.maker.channels[maker_chn].execute, name=f'maker_{self.maker.channels[maker_chn].order}', kwargs=maker_kwargs)
            thread.start()
            if rest:
                self.rest()
                self.liquid.primeAll()
            return thread
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
            if not pause:
                # log_now(f'CNC align: syringe {syringe.order} with spill station...')
                self.align(self.liquid.channels[channel].offset, self.positions['spill'])
            self.liquid.empty(channel, wait, pause)
        return
    
    def fillLiquids(self, channels=[], reagents=[], vols=[], wait=0, pause=False):
        if len(channels) == 0:
            channels = list(self.liquid.channels.keys())
        self._checkInputs(channels=channels, reagents=reagents, vols=vols)
        
        self.align(0, self.positions['fill'])
        for channel,reagent,vol in zip(channels, reagents, vols):
            self.liquid.prime(channel)
            if vol == 0 or self.liquid.channels[channel].volume == self.liquid.channels[channel].capacity:
                continue
            if not pause:
                # log_now(f'CNC align: syringe {syringe.order} with fill station...')
                self.align(self.liquid.channels[channel].offset, self.positions['fill'])
            self.liquid.aspirate(channel, reagent, vol, wait=wait, pause=pause)
            self.liquid.prime(channel)
        return
    
    def home(self):
        return self.mover.home()
    
    def labelPosition(self, name, coord, overwrite=False):
        if name not in self.positions.keys() or overwrite:
            self.positions[name] = coord
        else:
            raise Exception(f"The position '{name}' has already been defined at: {self.positions[name]}")
        return
    
    def labelPositions(self, names, coords, overwrite=False):
        self._checkInputs(names=names, coords=coords)
        for name,coord in zip(names, coords):
            self.labelPosition(name, coord, overwrite)
        return
    
    def primeAll(self, channels=[]):
        return self.liquid.primeAll(channels)
    
    def rest(self, home=True):
        # log_now(f'CNC align: move to rest position...')
        if home:
            self.mover.home()
        else:
            try:
                self.mover.moveTo(self.positions['rest'])
            except KeyError:
                raise Exception('Rest position not yet labelled.')
        return
    
    def rinseAll(self, channels=[], rinse_cycles=3):
        self.emptyLiquids(channels)
        self.liquid.rinseAll(channels, rinse_cycles)
        return

    def reset(self, home=True, wait=0, pause=False):
        self.emptyLiquids(wait=wait, pause=pause)
        self.rest(home)
        return
    