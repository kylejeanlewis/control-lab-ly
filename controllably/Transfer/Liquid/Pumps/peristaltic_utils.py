# %% -*- coding: utf-8 -*-
"""
This module holds the class for peristaltic pumps.

Classes:
    Peristaltic (Pump)
"""
# Standard library imports
from __future__ import annotations
import time
from typing import Optional, Union

# Local application imports
from .pump_utils import Pump
print(f"Import: OK <{__name__}>")

class Peristaltic(Pump):
    """
    Peristaltic provides methods to control a generic peristaltic pump

    ### Constructor
    Args:
        `port` (str): COM port address
        `output_clockwise` (bool, optional): whether liquid is pumped out when turned clockwise. Defaults to False.
    
    ### Methods
    - `aspirate`: aspirate desired volume of reagent
    - `blowout`: blowout liquid from tip (NOTE: not implemented)
    - `dispense`: dispense desired volume of reagent
    - `pull`: pull liquid in, away from outlet
    - `pullback`: pullback liquid from tip
    - `push`: push liquid out, towards the outlet
    - `setCurrentChannel`: set the current active channel
    - `setValve`: open or close the valve for a specified channel
    - `stop`: stop the pump
    - `turnAntiClockwise`: spin the pump anti-clockwise at a specified speed
    - `turnClockwise`: spin the pump clockwise at a specified speed
    """
    
    _default_flags = {
        'busy': False, 
        'connected': False,
        'output_clockwise': False
    }
    def __init__(self, port:str, output_clockwise:bool = False, **kwargs):
        """
        Instantiate the class

        Args:
            port (str): COM port address
            output_clockwise (bool, optional): whether liquid is pumped out when turned clockwise. Defaults to False.
        """
        super().__init__(port=port, **kwargs)
        self.setFlag(output_clockwise=output_clockwise)
        return
    
    def aspirate(self, speed:int, pump_time:int, channel:Optional[int] = None, **kwargs) -> bool:
        """
        Aspirate desired volume of reagent

        Args:
            speed (int): speed of pump rotation
            pump_time (int): duration to run pump for
            channel (Optional[int], optional): channel id. Defaults to None.

        Returns:
            bool: whether the action is successful
        """
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
    
    def dispense(self, speed:int, pump_time:int, channel:Optional[int] = None, **kwargs) -> bool:
        """
        Dispense desired volume of reagent

        Args:
            speed (int): speed of pump rotation
            pump_time (int): duration to run pump for
            channel (Optional[int], optional): channel id. Defaults to None.

        Returns:
            bool: whether the action is successful
        """
        self.setFlag(busy=True)
        self.setValve(open=True, channel=channel)
        
        if self.push(speed=speed):
            time.sleep(pump_time)
        self.stop()
        
        self.setValve(open=False, channel=channel)
        self.setFlag(busy=False)
        return True
    
    def pull(self, speed:int) -> bool:
        """
        Pull liquid in, away from outlet

        Args:
            speed (int): speed of pump rotation

        Returns:
            bool: whether the action is successful
        """
        pull_func = self.turnAntiClockwise if self.flags['output_clockwise'] else self.turnClockwise
        return pull_func(speed=speed)
        
    def pullback(self, speed:int = 300, pump_time:int = 1, channel:Optional[int] = None, **kwargs) -> bool:
        """
        Pullback liquid from tip

        Args:
            speed (int, optional): speed of pump rotation. Defaults to 300.
            pump_time (int, optional): duration to run pump for. Defaults to 1.
            channel (Optional[int], optional): channel id. Defaults to None.

        Returns:
            bool: whether the action is successful
        """
        self.setFlag(busy=True)
        self.setValve(open=True, channel=channel)
        
        if self.pull(speed=speed):
            time.sleep(pump_time)
        self.stop()
        
        self.setValve(open=False, channel=channel)
        self.setFlag(busy=False)
        return True
    
    def push(self, speed:int) -> bool:
        """
        Push liquid out, towards the outlet

        Args:
            speed (int): speed of pump rotation

        Returns:
            bool: whether the action is successful
        """
        push_func = self.turnClockwise if self.flags['output_clockwise'] else self.turnAntiClockwise
        return push_func(speed=speed)
    
    def setCurrentChannel(self, channel:Optional[int] = None) -> bool:
        """
        Set the current active channel

        Args:
            channel (Optional[int], optional): channel id. Defaults to None.

        Returns:
            bool: whether the action is successful
        """
        self.setValve(False)
        return self.setValve(open=True, channel=channel)
    
    def setValve(self, open:bool = False, channel:Optional[int] = None) -> bool:
        """
        Open or close the valve for a specified channel.
        Closes all valves if no input is given.

        Args:
            open (bool, optional): whether to open or close the valve. Defaults to False.
            channel (Optional[int], optional): channel id. Defaults to None.

        Raises:
            ValueError: Please select a channel from 1-8

        Returns:
            bool: whether the action is successful
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
        """Stop the pump"""
        return self._write("10\n")
    
    def turnAntiClockwise(self, speed:int) -> bool:
        """
        Spin the pump anti-clockwise at a specified speed
        
        Args:
            speed (int): speed of pump rotation
        """
        return self._turn_pump(abs(speed))
    
    def turnClockwise(self, speed:int) -> bool:
        """
        Spin the pump clockwise at a specified speed
        
        Args:
            speed (int): speed of pump rotation
        """
        return self._turn_pump(-abs(speed))
     
    # Protected method(s)
    def _connect(self, port: str, baudrate: int = 9600, timeout: int = 1):
        """
        Connection procedure for tool

        Args:
            port (str): COM port address
            baudrate (int, optional): baudrate. Defaults to 9600.
            timeout (int, optional): timeout in seconds. Defaults to 1.
        """
        super()._connect(port, baudrate, timeout)
        self.setValve(False)
        return
    
    def _turn_pump(self, speed:int) -> bool:
        """
        Relay instructions to pump
        
        Args:
            speed (int): speed of pump rotation
        """
        return self._write(f"{speed}\n")
    