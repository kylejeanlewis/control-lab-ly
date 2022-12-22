# %% -*- coding: utf-8 -*-
"""
Created: Tue 2022/11/01 17:13:35
@author: Chang Jie

Notes / actionables:
-
"""
# Standard library imports
import numpy as np
from threading import Thread
import time

# Third party imports

# Local application imports
from ... import Make
from ... import Move
from ..build_utils import BaseSetup
print(f"Import: OK <{__name__}>")

CNC_SPEED = 250

class Setup(BaseSetup):
    def __init__(self, config, ignore_connections=False, **kwargs):
        # super().__init__(**kwargs)
        self.mover = None
        self.liquid = None
        self.maker = None
        self.positions = {}
        
        self._config = config
        self._flags = {
            'aligning': False,
            'at_rest': False
        }
        self._connect(ignore_connections=ignore_connections)
        pass
    
    def _check_positions(self, wait=2, pause=False):
        for maker_chn in self.maker.channels.values():
            for liquid_chn in self.liquid.channels.values():
                self.align(liquid_chn.offset, maker_chn.position)
                time.sleep(wait)
                if pause:
                    input("Press 'Enter' to proceed.")
        return
    
    def _connect(self, diagnostic=True, ignore_connections=False):
        mover_class = self._getClass(Move, self._config['mover']['class'])
        liquid_class = self._getClass(Move, self._config['liquid']['class'])
        maker_class = self._getClass(Make, self._config['maker']['class'])
        
        self.mover = mover_class(**self._config['mover']['settings'])
        self.liquid = liquid_class(**self._config['liquid']['settings'])
        self.maker = maker_class(**self._config['maker']['settings'])
        
        if 'labelled_positions' in self._config.keys():
            names, coords = zip(*self._config['labelled_positions'].items())
            self.labelPositions(names, coords)

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
            thread = Thread(target=m.execute, name=f'maker_diag_{c}')
            thread.start()
            time.sleep(1)

        # Test self.mover
        self.home()
        self._check_positions()
        self.rest()
        
        # Test liquid
        self.pullbackAll()
        print('Ready!')
        return

    def align(self, offset, position):
        coord = np.array(position) - np.array(offset)
        if not self.mover.isFeasible(coord, transform=True):
            raise Exception("Selected position is not feasible.")
        self.mover.moveTo(coord)
        self._flags['at_rest'] = False
        # self.at_home = False
        
        # Time the wait
        distance = np.linalg.norm(coord - np.array(self.mover.coordinates))
        t_align = distance / CNC_SPEED + 2
        time.sleep(t_align)
        # log_now(f'CNC align: in position')
        # self.aligning = 0
        return
    
    def attachTip(self, channel, pipette_tip_length=80):
        class_name = str(self.liquid.__class__)[8:-2].split('.')[-1]
        if class_name not in ['Sartorius']:
            return
        self.liquid.channels[channel].pipette_tip_length = pipette_tip_length
        z_safe = self.mover.home_position[2]
        self.mover.moveTo((*self.positions['tips'][:2], z_safe))
        self.mover.moveBy((0,0,self.positions['tips'][-1] - z_safe))
        
        self.mover.implement_offset = tuple(np.array(self.mover.implement_offset) + np.array([0,0,-pipette_tip_length]))
        self.mover.moveBy((0,0,pipette_tip_length))
        return
    
    def coat(self, maker_chn, liquid_chn, vol, maker_kwargs, rest=True, new_thread=True):
        if vol:
            # log_now(f'CNC align: syringe {syringe.order} with spinner {spinner.order}...')
            self.align(self.liquid.channels[liquid_chn].offset, self.maker.channels[maker_chn].position)
            while self.maker.channels[maker_chn]._flags['busy']:
                time.sleep(0.5)
                # return
            self.maker.channels[maker_chn]._flags['busy'] = True
            self.liquid.dispense(liquid_chn, vol)

        # Start new thread from here
        self.maker.channels[maker_chn].etc = time.time() + 1 + sum([v for k,v in maker_kwargs.items() if 'time' in k])
        if new_thread:
            thread = Thread(target=self.maker.channels[maker_chn].execute, name=f'maker_{self.maker.channels[maker_chn].order}', kwargs=maker_kwargs)
            thread.start()
            if rest:
                self.rest()
                self.liquid.pullbackAll()
            return thread
        else:
            if rest:
                self.rest()
                self.liquid.pullback(liquid_chn)
            self.maker.channels[maker_chn].execute(maker_kwargs)
        return
    
    def ejectTip(self, channel):
        class_name = str(self.liquid.__class__)[8:-2].split('.')[-1]
        if class_name not in ['Sartorius']:
            return
        pipette_tip_length = self.liquid.channels[channel].pipette_tip_length
        z_safe = self.mover.home_position[2]
        self.mover.moveTo((*self.positions['bins'][:2], z_safe))
        self.liquid.eject(channel)
        
        self.mover.implement_offset = tuple(np.array(self.mover.implement_offset) - np.array([0,0,-pipette_tip_length]))
        self.liquid.channels[channel].pipette_tip_length = 0
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
            self.liquid.pullback(channel)
            if vol == 0 or self.liquid.channels[channel].volume == self.liquid.channels[channel].capacity:
                continue
            if not pause:
                # log_now(f'CNC align: syringe {syringe.order} with fill station...')
                self.align(self.liquid.channels[channel].offset, self.positions['fill'])
            self.liquid.aspirate(channel, reagent, vol, wait=wait, pause=pause)
            self.liquid.pullback(channel)
        return
    
    def home(self):
        return self.mover.home()
    
    def isBusy(self):
        return any([self.liquid.isBusy(), self.maker.isBusy()])
    
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
    
    def pullbackAll(self, channels=[]):
        return self.liquid.pullbackAll(channels)
    
    def rest(self):
        # log_now(f'CNC align: move to rest position...')
        if self._flags['at_rest']:
            return
        try:
            self.mover.moveTo(self.positions['rest'])
        except KeyError:
            self.mover.home()
            raise Exception('Rest position not yet labelled.')
        self._flags['at_rest'] = True
        return
    
    def rinseAll(self, channels=[], reagents=[], rinse_cycles=3):
        self.emptyLiquids(channels)
        self.liquid.rinseAll(channels, reagents, rinse_cycles)
        return

    def reset(self, home=True, wait=0, pause=False):
        self.emptyLiquids(wait=wait, pause=pause)
        self.rest(home)
        return
    