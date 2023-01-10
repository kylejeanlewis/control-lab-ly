# %% -*- coding: utf-8 -*-
"""
Created: Tue 2022/11/01 17:13:35
@author: Chang Jie

Notes / actionables:
- 
"""
# Local application imports
print(f"Import: OK <{__name__}>")

PRE_WET_CYCLES = 1

class LiquidHandler(object):
    """
    Liquid handler class

    Args:
        **kwargs: catch-all for stray inputs
    """
    def __init__(self, **kwargs):
        self.capacity = 0
        self.channel = 0
        self.offset = (0,0,0)
        self.reagent = ''
        self.volume = 0
        
        self._speed_in = 0
        self._speed_out = 0
        self.verbose = kwargs.get('verbose', False)
        self._flags = {}
        return
    
    @property
    def speed(self):
        speed = {
            'in': self._speed_in,
            'out': self._speed_out
        }
        return speed
    @speed.setter
    def speed(self, value:int, direction:str):
        if direction == 'in':
            self._speed_in = value
        elif direction == 'out':
            self._speed_out = value
        else:
            raise Exception("Please select either 'in' or 'out' for direction parameter")
        return
    
    def _diagnostic(self):
        """
        Run diagnostic on tool
        """
        self.pullback()
        return

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
        return
    
    def blowout(self, channel=None):
        """
        Blowout liquid from tip

        Args:
            channel (int, optional): channel to pullback. Defaults to None.
        """
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
    
    def fill(self, speed=None, wait=0, reagent='', pause=False, pre_wet=True, channel=None):
        """
        Fill the channel with reagent to its capacity

        Args:
            speed (int, optional): speed to fill. Defaults to None.
            wait (int, optional): wait time between steps in seconds. Defaults to 0.
            reagent (str, optional): name of reagent. Defaults to ''.
            pause (bool, optional): whether to pause for intervention / operator input. Defaults to False.
            pre_wet (bool, optional): whether to pre-wet the channel. Defaults to True.
            channel (int, optional): channel to fill. Defaults to None.
        """
        volume = self.capacity - self.volume
        if pre_wet:
            self.cycle(volume=volume, speed=speed, wait=wait, reagent=reagent, cycles=PRE_WET_CYCLES, channel=channel)
        self.aspirate(volume=volume, speed=speed, wait=wait, reagent=reagent, pause=pause, channel=channel)
        self.pullback(channel=channel)
        return

    def pullback(self, channel=None):
        """
        Pullback liquid from tip

        Args:
            channel (int, optional): channel to pullback. Defaults to None.
        """
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
    
    def setFlag(self, name:str, value:bool):
        """
        Set a flag truth value

        Args:
            name (str): label
            value (bool): flag value
        """
        self._flags[name] = value
        return
