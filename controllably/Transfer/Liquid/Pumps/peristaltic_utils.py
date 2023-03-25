# %% -*- coding: utf-8 -*-
"""
Adapted from @jaycecheng spinutils

Created: Tue 2022/11/01 17:13:35
@author: Chang Jie

Notes / actionables:
-
"""
# Standard library imports
from __future__ import annotations
import time
from typing import Optional, Union

# Third party imports
import serial # pip install pyserial

# Local application imports
from .pump_utils import Pump
print(f"Import: OK <{__name__}>")

class Peristaltic(Pump):
    """
    Peristaltic pump object

    Args:
        port (str): com port address
        verbose (bool, optional): whether to print output. Defaults to False.
    """
    _default_flags = {
        'busy': False, 
        'connected': False,
        'output_clockwise': False
    }
    def __init__(self, port:str, **kwargs):
        super().__init__(port=port, **kwargs)
        return
    
    def aspirate(self, speed:int, pump_time:int, channel:int=None, **kwargs) -> bool:
        self.setFlag(busy=True)
        self.setValve(open=True, channel=channel)
        
        if self.pull(speed=speed):
            time.sleep(pump_time)
        self.stop()
        
        self.setValve(open=False, channel=channel)
        self.setFlag(busy=False)
        return True
    
    def blowout(self, channel: Optional[Union[int, tuple[int]]] = None, **kwargs) -> bool: # NOTE: no implementation
        return False
    
    def dispense(self, speed:int, pump_time:int, channel:int=None, **kwargs) -> bool:
        self.setFlag(busy=True)
        self.setValve(open=True, channel=channel)
        
        if self.push(speed=speed):
            time.sleep(pump_time)
        self.stop()
        
        self.setValve(open=False, channel=channel)
        self.setFlag(busy=False)
        return True
    
    def pull(self, speed:int) -> bool:
        pull_func = self.turnAntiClockwise if self.flags['output_clockwise'] else self.turnClockwise
        return pull_func(speed=speed)
        
    def pullback(self, speed:int, pump_time:int, channel:int=None, **kwargs) -> bool:
        self.setFlag(busy=True)
        self.setValve(open=True, channel=channel)
        
        if self.pull(speed=speed):
            time.sleep(pump_time)
        self.stop()
        
        self.setValve(open=False, channel=channel)
        self.setFlag(busy=False)
        return True
    
    def push(self, speed:int) -> bool:
        push_func = self.turnClockwise if self.flags['output_clockwise'] else self.turnAntiClockwise
        return push_func(speed=speed)
    
    def setCurrentChannel(self, channel:Optional[int] = None) -> bool:
        return self.setValve(open=True, channel=channel)
    
    def setValve(self, open:bool = False, channel:Optional[int] = None) -> bool:
        """
        Relay instructions to valve.
        
        Args:
            state (int): open or close valve channel (-1~-8 open valve; 1~8 close valve; 9 close all valves)
        """
        state = 0
        if channel is None:
            state = 9
        elif type(channel) is int and (1<= channel <=8):
            state = -channel if open else channel
        if state == 0:
            raise ValueError("Please select a channel from 1-8.")
        return self._write(f"{state}\n")
    
    def stop(self) -> bool:
        return self._write("10\n")
    
    def turnAntiClockwise(self, speed:int) -> bool:
        """
        Relay instructions to pump
        
        Args:
            speed (int): speed of pump of rotation
        """
        return self._turn_pump(abs(speed))
    
    def turnClockwise(self, speed:int) -> bool:
        """
        Relay instructions to pump
        
        Args:
            speed (int): speed of pump of rotation
        """
        return self._turn_pump(-abs(speed))
     
    # Protected method(s)
    def _turn_pump(self, speed:int) -> bool:
        """
        Relay instructions to pump
        
        Args:
            speed (int): speed of pump of rotation
        """
        return self._write(f"{speed}\n")


    ### NOTE: DEPRECATE
    # def _push(self, speed:int, push_time:int, pullback_time:int, channel:int):
    #     """
    #     Dispense (aspirate) liquid from (into) syringe
        
    #     Args:
    #         speed (int): speed of pump of rotation (<0 aspirate; >0 dispense)
    #         push_time (int, or float): time to achieve desired volume
    #         pullback_time (int, or float): time to pullback the peristaltic pump
    #         channel (int): valve channel
    #     """
    #     run_time = pullback_time + push_time
    #     interval = 0.1
        
    #     start_time = time.time()
    #     self.setValve(open=True, channel=channel)
    #     self._turn_pump(speed)
        
    #     while(True):
    #         time.sleep(0.001)
    #         if (interval <= time.time() - start_time):
    #             interval += 0.1
    #         if (run_time <= time.time() - start_time):
    #             break
        
    #     start_time = time.time()
    #     self.setValve(open=True, channel=channel)
    #     self._turn_pump(-abs(speed))

    #     while(True):
    #         time.sleep(0.001)
    #         if (interval <= time.time() - start_time):
    #             interval += 0.1
    #         if (pullback_time <= time.time() - start_time):
    #             self._turn_pump(10)
    #             self.setValve(open=False, channel=channel)
    #             break
    #     return
    