# %% -*- coding: utf-8 -*-
"""
Created: Tue 2022/11/01 17:13:35
@author: Chang Jie

Notes / actionables:
-
"""
# Local application imports
from .. import Mover
print(f"Import: OK <{__name__}>")

class LiquidHandler(Mover):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.channels = {}
        return
    
    def _getValues(self, channels, field):
        if len(channels) == 0:
            channels = list(self.channels.keys())
        return [(key, getattr(self.channels[key], field)) for key in channels]

    def aspirate(self, *args, **kwargs):
        '''
        Adjust the valve and aspirate reagent
        - vol: volume
        - speed: speed of pump rotation

        Returns: None
        '''
        return

    def cycle(self, channel, reagent, vol, speed=0, wait=1):
        self.aspirate(channel, reagent, vol, speed=speed, wait=wait)
        self.dispense(channel, vol, speed=speed, wait=wait, force_dispense=True)
        return

    def dispense(self, *args, **kwargs):
        '''
        Adjust the valve and dispense reagent
        - vol: volume
        - speed: speed of pump rotation
        - force_dispense: continue with dispense even if insufficient volume in syringe

        Returns: None
        '''
        return

    def empty(self, *args, **kwargs):
        '''
        Adjust the valve and empty syringe

        Returns: None
        '''
        return
    
    def emptyAll(self, channels=[], wait=1, pause=False):
        if len(channels) == 0:
            channels = list(self.channels.keys())
        for channel in channels:
            self.empty(channel, wait, pause)
        return

    def fill(self, *args, **kwargs):
        '''
        Adjust the valve and fill syringe with reagent
        - reagent: reagent to be filled in syringe
        - vol: volume

        Returns: None
        '''
        return
    
    def fillAll(self, channels=[], reagents=[], prewet=True, wait=1, pause=False):
        if len(channels) == 0:
            channels = list(self.channels.keys())
        self._checkInputs(channels=channels, reagents=reagents)
        for channel,reagent in zip(channels, reagents):
            self.fill(channel, reagent, prewet, wait, pause)
        return
    
    def getReagents(self, channels=[]):
        return self._getValues(channels, 'reagent')
    
    def getVolumes(self, channels=[]):
        return self._getValues(channels, 'volume')

    def pullback(self, *args, **kwargs):
        return
    
    def pullbackAll(self, channels=[]):
        if len(channels) == 0:
            channels = list(self.channels.keys())
        for channel in channels:
            self.pullback(channel)
        return
    
    def rinse(self, *args, **kwargs):
        return
    
    def rinseAll(self, channels=[], reagents=[], rinse_cycles=3):
        if len(channels) == 0:
            channels = list(self.channels.keys())
        for channel,reagent in zip(channels, reagents):
            self.rinse(channel, reagent, rinse_cycles)
        return
