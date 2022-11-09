# %% -*- coding: utf-8 -*-
"""
Adapted from @jaycecheng spinutils

Created: Tue 2022/11/01 17:13:35
@author: Chang Jie

Notes / actionables:
-
"""
# Standard library imports
import os
import pandas as pd
import pkgutil
import time
import yaml

# Third party imports

# Local application imports
from .routines import Setup
print(f"Import: OK <{__name__}>")

CONFIG_FILE = 'config.yaml'

class Program(object):
    def __init__(self, ignore_connections=False, recover_state_from_file=''):
        self._config = self._readPlans(CONFIG_FILE)
        self.setup = Setup(self._config, ignore_connections)
        self.window = None
        self.flags = {
            'force_stop': False
        }
        
        self.reagents_df = None
        self.recipe_df = None
        
        self._all_steps = {}
        self._executed = []
        self._state_filename = recover_state_from_file
        self._threads = []
        
        if len(recover_state_from_file):
            self._readState()
        return
    
    # Main methods
    def _assignSteps(self):
        self._all_steps = {}
        for key in self.setup.maker.channels.keys():
            steps = []
            for _, row in self.recipe_df.iterrows():
                if key not in row['channels']:
                    # continue
                    liquid_chn = self.reagents_df[self.reagents_df['reagent']==row['reagent']]['channel'][0]
                    maker_kwargs = dict(
                        soak_time=row['soak_time'],
                        spin_speed=row['spin_speed'],
                        spin_time=row['spin_time']
                    )
                    kwargs = dict(
                        maker_chn=key,
                        liquid_chn=liquid_chn,
                        vol=row['volume'],
                        maker_kwargs=maker_kwargs
                    )
                    steps.append(kwargs)
            self._all_steps[key] = steps
        return
    
    def _isOverrun(self, start_time, timeout):
        if timeout!=None and time.time() - start_time > timeout:
            # log_now(f'Exceeded runtime of {timeout}s', True)
            return True
        return False
    
    def _getRequiredVolumes(self):
        df = self.recipe_df.copy()
        df['required_volume'] = [len(row['channels'])*row['volume'] for _,row in df.iterrows()]
        df = df.groupby('reagent')['required_volume'].sum().reset_index()
        return df
    
    def _readPlans(self, config_file):
        yml = pkgutil.get_data(__name__, config_file).decode('utf-8')
        config = yaml.full_load(yml)
        return config
    
    def _readState(self, filename=''):
        if len(filename) == 0:
            filename = self._state_filename
        with open(filename, 'r', encoding='utf-8') as f:
            state = yaml.full_load(f)
            
        # Mover states
        for key,value in state['mover']['positions'].items():
            if key == 'current':
                pass
                # self.setup.mover.coordinates = (value['x'],value['y'],value['z'])
            else:
                self.setup.positions[key] = (value['x'],value['y'],value['z'])
            
        # Liquid states
        for channel,values in state['liquid']['channels'].items():
            for field,value in values.items():
                self.setup.liquid.update(channel, field, value)
        return state

    def loadRecipe(self, reagents_file='', recipe_file='', reagents_df=None, recipe_df=None): # read recipe
        if type(reagents_df) == type(None):
            if len(reagents_file) == 0:
                raise Exception('Please input either filename or DataFrame for reagents.')
            columns = ['channel', 'reagent', 'volume']
            reagents_df = pd.read_csv(reagents_file)
            if set(reagents_df.columns) != set(columns):
                raise Exception(f"Ensure only these headers are present: {', '.join(columns)}")
        self.reagents_df = reagents_df
        
        if type(recipe_df) == type(None):
            if len(recipe_file) == 0:
                raise Exception('Please input either filename or DataFrame for recipe.')
            columns = ['channels', 'reagent', 'volume', 'soak_time', 'spin_speed', 'spin_time']
            recipe_df = pd.read_csv(recipe_file)
            if set(recipe_df.columns) != set(columns):
                raise Exception(f"Ensure only these headers are present: {', '.join(columns)}")
        channels = recipe_df['channels'].str.split(' ')
        channels = [[int(c) for c in row] for row in channels]
        recipe_df['channels'] = channels
        self.recipe_df = recipe_df
        
        self._assignSteps()
        return
    
    def loadScheduler(self):
        return
    
    def prepareSetup(self, fill_sequence=[], manual_fill=False):
        df = self.reagents_df.copy()
        required_volumes_df = self._getRequiredVolumes()
        current_volumes_df = pd.DataFrame(self.setup.liquid.getVolumes(), columns=['channel','current_volume'])
        df = df.merge(required_volumes_df, on='reagent', how='left')
        df = df.merge(current_volumes_df, on='channel', how='left')
        fill_volumes = [ max(0, max(row['volume'],row['required_volume']) - row['current_volume']) for _,row in df.iterrows()]
        df['fill_volume'] = fill_volumes
        
        df.set_index('channel', inplace=True)
        if len(fill_sequence):
            if set(fill_sequence) != set(df.index):
                raise Exception(f"Ensure fill sequence only contains these channels: {', '.join([str(i) for i in df.index])}")
            df.reindex(fill_sequence)
        kwargs = dict(
            channels=df.index.to_list(),
            reagents=df['reagent'].to_list(),
            vols=df['fill_volume'].to_list()
        )
        print(kwargs)
        
        self.setup.fillLiquids(pause=manual_fill, **kwargs)
        return
    
    def queue(self, maker_chn, rest=True, new_thread=True): #give instructions
        kwargs = self._all_steps[maker_chn].pop(0)
        thread = self.setup.coat(rest=rest, new_thread=new_thread, **kwargs)
        self._threads.append(thread)
        self._executed.append(kwargs)
        return
    
    def reset(self, hardware_only=True):
        self.setup.reset(home=False, pause=True)
        if not hardware_only:
            self.reagents_df = None
            self.recipe_df = None
            self._all_steps = {}
            self._executed = []
            self._threads = []
        return

    def runExperiment(self, timeout=None):
        start_time = time.time()
        while not all([(len(steps)==0 for steps in self._all_steps.values())]):
            time.sleep(0.05)
            if self._isOverrun(start_time, timeout) or self.flags['force_stop']:
                break
            # run scheduler and queue actions
            pass
        return
    
    def saveState(self, filename=''):
        if len(filename) == 0:
            folder = __name__.split('builds.')[1].replace('.', '/')
            if not os.path.exists(folder):
                os.makedirs(folder)
            filename = f"{folder}/state.yaml"
        
        axes = ('x','y','z')
        states = {
            'mover': {
                'positions': {
                    name: {axis: value for axis,value in zip(axes,coord)} for name,coord in self.setup.positions.items()
                }
            },
            'liquid': {
                'channels': {
                    c.channel: dict(reagent=c.reagent,volume=c.volume) for c in self.setup.liquid.channels.values()
                }
            }
        }
        states['mover']['positions']['current'] = {axis: float(value) for axis,value in zip(axes,self.setup.mover.coordinates)}
        
        with open(filename, 'w', encoding='utf-8') as f:
            yaml.dump(states, f, indent=2)
            self._state_filename = filename
        return
    
    def start(self, timeout=None):
        try:
            self.runExperiment(timeout)
        finally:
            self.reset()
            print('Stopping threads...')
            for thread in self._threads:
                thread.join(timeout=2)
        return
    
    # Component methods
    def getReagents(self, channels=[]):
        return self.setup.liquid.getReagents(channels=channels)
    def getVolumes(self, channels=[]):
        return self.setup.liquid.getVolumes(channels=channels)
    def labelPosition(self, name, coord, overwrite=False):
        return self.setup.labelPosition(name, coord, overwrite)
    def labelPositions(self, names, coords, overwrite=False):
        return self.setup.labelPositions(names, coords, overwrite)

    # GUI methods
    def _gui_build_window(self):
        return
    def _gui_disable_interface(self):
        return
    def _gui_loop(self):
        return
    