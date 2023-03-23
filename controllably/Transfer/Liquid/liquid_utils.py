# %% -*- coding: utf-8 -*-
"""
Created: Tue 2022/11/01 17:13:35
@author: Chang Jie

Notes / actionables:
- 
"""
# Standard library imports
from __future__ import annotations
from abc import ABC, abstractmethod
from collections import namedtuple
import numpy as np
from typing import Optional

# Local application imports
print(f"Import: OK <{__name__}>")

PRE_FILL_CYCLES = 1

Speed = namedtuple('Speed', ['up','down'])

class LiquidHandler(ABC):
    """
    Liquid handler class

    Args:
        **kwargs: catch-all for stray inputs
    """
    def __init__(self, verbose:bool = False, **kwargs):
        self.capacity = 0
        self.channel = 0
        self.reagent = ''
        self.speed = Speed(0,0)
        self.volume = 0
        
        self._offset = (0,0,0)
        self.flags = {}
        self.verbose = verbose
        return

    @abstractmethod
    def aspirate(self, volume, speed=None, wait=0, reagent='', pause=False, channel=None):
        """
        Aspirate desired volume of reagent into channel

        Args:
            volume (int, or float): volume to be aspirated
            speed (int, optional): speed to aspirate. Defaults to None.
            wait (int, optional): wait time between steps in seconds. Defaults to 0.
            reagent (str, optional): name of reagent. Defaults to ''.
            pause (bool, optional): whether to pause for intervention / operator input. Defaults to False.
            channel (int, optional): channel to aspirate. Defaults to None.
        """
    
    @abstractmethod
    def blowout(self, channel=None):
        """
        Blowout liquid from tip

        Args:
            channel (int, optional): channel to pullback. Defaults to None.
        """

    @abstractmethod
    def dispense(self, volume, speed=None, wait=0, force_dispense=False, pause=False, channel=None):
        """
        Dispense desired volume of reagent from channel

        Args:
            volume (int, or float): volume to be dispensed
            speed (int, optional): speed to dispense. Defaults to None.
            wait (int, optional): wait time between steps in seconds. Defaults to 0.
            force_dispense (bool, optional): whether to continue dispensing even if insufficient volume in channel. Defaults to False.
            pause (bool, optional): whether to pause for intervention / operator input. Defaults to False.
            channel (int, optional): channel to dispense. Defaults to None.
        """

    @abstractmethod
    def pullback(self, channel=None):
        """
        Pullback liquid from tip

        Args:
            channel (int, optional): channel to pullback. Defaults to None.
        """

    # Properties
    @property
    def offset(self) -> np.ndarray:
        return np.array(self._offset)
    @offset.setter
    def offset(self, value:tuple[float]):
        if len(value) != 3:
            raise Exception('Please input x,y,z offset')
        self._offset = tuple(value)
        return
    
    @property
    def speed_up(self) -> int:
        return self.speed.up
    @speed_up.setter
    def speed_up(self, value:int):
        self.speed = Speed(int(value), self.speed_down)
        return
    
    @property
    def speed_down(self) -> int:
        return self.speed.down
    @speed_down.setter
    def speed_down(self, value:int):
        self.speed = Speed(self.speed_up, int(value))
        return
    
    def cycle(self, volume, speed=None, wait=0, reagent='', cycles=1, channel=None):
        """
        Cycle the channel with aspirate and dispense

        Args:
            volume (int, or float): volume to be cycled
            speed (int, optional): speed to cycle. Defaults to None.
            wait (int, optional): wait time between steps in seconds. Defaults to 0.
            reagent (str, optional): name of reagent. Defaults to ''.
            cycles (int, optional): number of cycles to perform. Defaults to 1.
            channel (int, optional): channel to cycle. Defaults to None.
        """
        for _ in range(cycles):
            self.aspirate(volume=volume, speed=speed, wait=wait, reagent=reagent, channel=channel)
            self.dispense(volume=volume, speed=speed, wait=wait, force_dispense=True, channel=channel)
        return

    def empty(self, speed=None, wait=0, pause=False, channel=None):
        """
        Empty the channel of its contents

        Args:
            speed (int, optional): speed to empty. Defaults to None.
            wait (int, optional): wait time between steps in seconds. Defaults to 0.
            pause (bool, optional): whether to pause for intervention / operator input. Defaults to False.
            channel (int, optional): channel to empty. Defaults to None.
        """
        self.dispense(volume=self.capacity, speed=speed, wait=wait, force_dispense=True, pause=pause, channel=channel)
        self.blowout(channel=channel)
        return
    
    def fill(self, speed=None, wait=0, reagent='', pause=False, cycles=PRE_FILL_CYCLES, channel=None):
        """
        Fill the channel with reagent to its capacity

        Args:
            speed (int, optional): speed to fill. Defaults to None.
            wait (int, optional): wait time between steps in seconds. Defaults to 0.
            reagent (str, optional): name of reagent. Defaults to ''.
            pause (bool, optional): whether to pause for intervention / operator input. Defaults to False.
            cycles (bool, optional): whether to pre-wet the channel. Defaults to True.
            channel (int, optional): channel to fill. Defaults to None.
        """
        volume = self.capacity - self.volume
        if cycles:
            self.cycle(volume=volume, speed=speed, wait=wait, reagent=reagent, cycles=cycles, channel=channel)
        self.aspirate(volume=volume, speed=speed, wait=wait, reagent=reagent, pause=pause, channel=channel)
        self.pullback(channel=channel)
        return
    
    def rinse(self, volume, speed=None, wait=0, reagent='', cycles=3, channel=None):
        """
        Rinse the channel with aspirate and dispense cycles

        Args:
            volume (int, or float): volume to be rinsed
            speed (int, optional): speed to cycle. Defaults to None.
            wait (int, optional): wait time between steps in seconds. Defaults to 0.
            reagent (str, optional): name of reagent. Defaults to ''.
            cycles (int, optional): number of cycles to perform. Defaults to 3.
            channel (int, optional): channel to cycle. Defaults to None.
        """
        return self.cycle(volume=volume, speed=speed, wait=wait, reagent=reagent, cycles=cycles, channel=channel)
    
    def setFlag(self, **kwargs):
        """
        Set a flag's truth value

        Args:
            `name` (str): label
            `value` (bool): flag value
        """
        if not all([type(v)==bool for v in kwargs.values()]):
            raise ValueError("Ensure all assigned flag values are boolean.")
        for key, value in kwargs.items():
            self.flags[key] = value
        return

    # Protected method(s)
    def _diagnostic(self):
        """
        Run diagnostic on tool
        """
        self.pullback()
        return
