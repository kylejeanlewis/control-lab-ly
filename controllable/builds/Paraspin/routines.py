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
from ...misc import HELPER
from ... import Make
from ... import Move
from ... import Transfer
from ..build_utils import Setup
print(f"Import: OK <{__name__}>")

CNC_SPEED = 250

class SpinbotSetup(Setup):
    def __init__(self, config, ignore_connections=False, **kwargs):
        super().__init__(**kwargs)
        self.mover = None
        self.liquid = None
        self.maker = None
        
        self.positions = {}
        self._config = config
        self._flags = {
            'at_rest': False
        }
        self._connect(ignore_connections=ignore_connections)
        pass
    
    def _connect(self, diagnostic=True, ignore_connections=False):
        mover_class = self._get_class(Move, self._config['mover']['class'])
        liquid_class = self._get_class(Transfer, self._config['liquid']['class'])
        maker_class = self._get_class(Make, self._config['maker']['class'])
        
        self.mover = mover_class(**self._config['mover']['settings'])
        self.liquid = liquid_class(**self._config['liquid']['settings'])
        self.maker = maker_class(**self._config['maker']['settings'])
        
        if 'labelled_positions' in self._config.keys():
            # names, coords = zip(*self._config['labelled_positions'].items())
            self.labelPositions(self._config['labelled_positions'])

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
        
        # Test tools
        self.maker._diagnostic()
        self.mover._diagnostic()
        self.rest()
        self.liquid._diagnostic()
        print('Ready!')
        return

    def align(self, coordinates, offset=(0,0,0)):
        coordinates = np.array(coordinates) - np.array(offset)
        if not self.mover.isFeasible(coordinates, transform=True, tool_offset=True):
            print(f"Infeasible toolspace coordinates! {coordinates}")
        self.mover.safeMoveTo(coordinates, descent_speed_fraction=0.2)
        self._flags['at_rest'] = False
        
        # Time the wait
        # distance = np.linalg.norm(coordinates - np.array(self.mover.coordinates))
        # t_align = distance / CNC_SPEED + 2
        # time.sleep(t_align)
        return
    
    def aspirateAt(self, coordinates, volume, speed=None, channel=None, **kwargs):
        if not self.liquid.isTipOn(): # or not self.liquid.tip_length:
            print("There is no tip attached.")
            return
        offset = self.liquid.channels[channel].offset if 'channels' in dir(self.liquid) else self.liquid.offset
        self.align(coordinates=coordinates, offset=offset)
        self.liquid.aspirate(volume=volume, speed=speed, channel=channel)
        return
    
    def attachTip(self, coordinates, tip_length=80, channel=None):
        if 'eject' not in dir(self.liquid):
            print("'attachTip' method not available.")
            return
        if self.liquid.isTipOn():# or self.liquid.tip_length:
            print("Please eject current tip before attaching new tip.")
            return
        self.mover.safeMoveTo(coordinates, descent_speed_fraction=0.2)
        self.mover.move('z', -20, speed_fraction=0.01)
        time.sleep(3)
        self.liquid.tip_length = tip_length
        self.mover.implement_offset = tuple(np.array(self.mover.implement_offset) + np.array([0,0,-tip_length]))
        self.mover.move('z', 20+tip_length, speed_fraction=0.2)
        time.sleep(1)
        return
    
    def checkTip(self):
        return
    
    def coat(self, maker_chn, liquid_chn, vol, maker_kwargs, rest=True, new_thread=True):
        if vol:
            self.align(self.maker.channels[maker_chn].position, self.liquid.channels[liquid_chn].offset)
            while self.maker.channels[maker_chn]._flags['busy']:
                time.sleep(0.5)
            self.maker.channels[maker_chn]._flags['busy'] = True
            self.liquid.dispense(volume=vol, channel=liquid_chn)

        # Start new thread from here
        self.maker.channels[maker_chn].etc = time.time() + 1 + sum([v for k,v in maker_kwargs.items() if 'time' in k])
        if new_thread:
            thread = Thread(target=self.maker.channels[maker_chn].execute, name=f'maker_{self.maker.channels[maker_chn].order}', kwargs=maker_kwargs)
            thread.start()
            if rest:
                self.rest()
                self.liquid.pullback()
            return thread
        else:
            if rest:
                self.rest()
                self.liquid.pullback([liquid_chn])
            self.maker.channels[maker_chn].execute(maker_kwargs)
        return
    
    def dispenseAt(self, coordinates, volume, speed=None, channel=None, **kwargs):
        if not self.liquid.isTipOn(): # or not self.liquid.tip_length:
            print("There is no tip attached.")
            return
        offset = self.liquid.channels[channel].offset if 'channels' in dir(self.liquid) else self.liquid.offset
        self.align(coordinates=coordinates, offset=offset)
        self.liquid.dispense(volume=volume, speed=speed, channel=channel)
        return
    
    def ejectTip(self, coordinates, channel=None):
        if 'eject' not in dir(self.liquid):
            print("'ejectTip' method not available.")
            return
        if not self.liquid.isTipOn(): # or not self.liquid.tip_length:
            print("There is currently no tip to eject.")
            return
        self.mover.safeMoveTo(coordinates, descent_speed_fraction=0.2)
        time.sleep(1)
        self.liquid.eject()
        tip_length = self.liquid.tip_length
        self.mover.implement_offset = tuple(np.array(self.mover.implement_offset) - np.array([0,0,-tip_length]))
        self.liquid.tip_length = 0
        return
    
    def isBusy(self):
        return any([self.liquid.isBusy(), self.maker.isBusy()])
    
    def labelPositions(self, names_coords={}, overwrite=False):
        for name,coordinates in names_coords.items():
            if name not in self.positions.keys() or overwrite:
                self.positions[name] = coordinates
            else:
                print(f"The position '{name}' has already been defined at: {self.positions[name]}")
        return
    
    def reset(self):
        # Empty liquids
        self.rest()
        return
    
    def rest(self):
        if self._flags['at_rest']:
            return
        rest_coordinates = self.positions.get('rest', self.mover._transform_out((self.mover.home_coordinates)))
        self.mover.safeMoveTo(rest_coordinates)
        self._flags['at_rest'] = True
        return
    