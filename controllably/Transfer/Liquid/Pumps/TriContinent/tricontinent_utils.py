# %% -*- coding: utf-8 -*-
"""
Adapted from @aniketchitre C3000_SyringePumpsv2

Created: Tue 2022/11/01 17:13:35
@author: Chang Jie

Notes / actionables:
-
"""
# Standard library imports
from __future__ import annotations
from functools import wraps
import string
import time
from typing import Callable, Optional, Union

# Local application imports
from .....misc import Helper
from ...liquid_utils import Speed
from ..pump_utils import Pump
from .tricontinent_lib import ErrorCode, StatusCode, TriContinentPump
print(f"Import: OK <{__name__}>")

class TriContinent(Pump):
    _default_flags = {
        'busy': False, 
        'connected': False,
        'execute_now': True
    }
    def __init__(self, 
        port: str, 
        channel: Union[int, tuple[int]], 
        model: Union[str, tuple[str]], 
        capacity: Union[int, tuple[int]], 
        output_right: Union[bool, tuple[bool]], 
        name: Union[str, tuple[str]] = '',
        **kwargs
    ):
        super().__init__(port, **kwargs)
        self.channels = self._get_pumps(
            channel = channel,
            model = model,
            capacity = capacity,
            output_right = output_right,
            name = name
        )
        self.current_channel = None
        
        self.channel = list(self.channels)[0]
        self.name = ''
        self.capacity = 0
        self.resolution = 1
        self.step_limit = 1
        
        self.position = 0
        for channel in self.channels:
            self.setCurrentChannel(channel=channel)
            self.initialise()
        self.resetChannel()
        return
    
    # Properties
    @property
    def current_pump(self) -> TriContinentPump:
        return self.current_channel

    @property
    def pumps(self) -> dict[int, TriContinentPump]:
        return self.channels
    
    @property
    def status(self) -> str:
        return self.getStatus()
    
    @property
    def volume(self) -> float:
        return self.position/self.step_limit * self.capacity
    
    # Decorators
    def _single_action(func: Callable) -> Callable:
        """
        Turns a method into a single action that runs only if it is not contained in a compound action

        Args:
            func (Callable): action method
        
        Returns:
            Callable: wrapped method
        """
        @wraps(func)
        def wrapper(self, *args, **kwargs) -> str:
            channel = kwargs.get('channel')
            self.setCurrentChannel(channel)
            command = func(self, *args, **kwargs)
            if self.flags['execute_now']:
                return self.run(command)
            return command
        return wrapper
    
    def _compound_action(func: Callable) -> Callable:
        """
        Turns a method into a compound action that suppresses single actions within from running

        Args:
            func (Callable): action method
        
        Returns:
            Callable: wrapped method
        """
        @wraps(func)
        def wrapper(self, *args, **kwargs) -> str:
            channel = kwargs.get('channel')
            self.setCurrentChannel(channel)
            self.setFlag(execute_now=False)
            command = func(self, *args, **kwargs)
            self.setFlag(execute_now=True)
            return command
        return wrapper

    # Public methods
    @_compound_action
    def aspirate(self, 
        volume: float, 
        speed: int = 200, 
        wait: int = 0, 
        pause: bool = False, 
        start_speed: int = 50,
        reagent: Optional[str] = None, 
        channel: Optional[Union[int, tuple[int]]] = None,
        **kwargs
    ) -> str:
        steps = min(int(volume/self.resolution), self.step_limit-self.position)
        volume = steps * self.resolution
        self.queue([
            self.setStartSpeed(start_speed),
            self.setTopSpeed(speed),
            self.setSpeedRamp(1),
            self.setValve('I'),
            self.moveBy(steps),
            self.wait(wait)
        ], channel=channel)
        command = self.current_pump.command
        print(f"Pump: {self.name}")
        print(f"Aspirating {volume}uL...")
        self.run()
        if reagent is not None:
            self.current_pump.reagent = reagent
        if pause:
            input("Press 'Enter' to proceed.")
        return command
    
    def blowout(self, channel: Optional[Union[int, tuple[int]]] = None, **kwargs) -> str: # NOTE: no implementation
        return ''
    
    @_compound_action
    def cycle(self, 
        volume: float, 
        speed: Optional[float] = 200, 
        wait: int = 0,  
        cycles: int = 3,
        start_speed: int = 50,
        channel: Optional[Union[int, tuple[int]]] = None,
        **kwargs
    ) -> str:
        """
        Cycle between aspirate and dispense

        Args:
            volume (float): target volume
            speed (Optional[float], optional): speed to aspirate and dispense at. Defaults to 200.
            wait (int, optional): time delay after each action. Defaults to 0.
            cycles (int, optional): number of cycles. Defaults to 3.
            start_speed (int, optional): starting speed of plunger. Defaults to 50.
            channel (Optional[Union[int, tuple[int]]], optional): channel id(s). Defaults to None.

        Returns:
            str: command string
        """
        self.queue([
            self.initialise(),
            self.setStartSpeed(start_speed),
            self.setTopSpeed(speed),
            self.setSpeedRamp(1),
            self.loop(cycles,
                self.aspirate(volume, speed=speed, wait=wait, start_speed=start_speed),
                self.wait(wait),
                self.dispense(volume, speed=speed, wait=wait, start_speed=start_speed),
                self.wait(wait)
            )
        ], channel=channel)
        command = self.current_pump.command
        print(f"Pump: {self.name}")
        self.run()
        print(f"Cycling complete: {cycles} time(s)")
        return command     
    
    @_compound_action
    def dispense(self, 
        volume: float, 
        speed: int = 200, 
        wait: int = 0, 
        pause: bool = False, 
        start_speed: int = 50,
        channel: Optional[Union[int, tuple[int]]] = None,
        **kwargs
    ) -> str:
        steps = min(int(volume/self.resolution), self.step_limit)
        volume = steps * self.resolution
        self.queue([
            self.setStartSpeed(start_speed),
            self.setTopSpeed(speed),
            self.setSpeedRamp(1)
        ], channel=channel)
        if self.position <= steps:
            self.queue([self.fill()], channel=channel)
        self.queue([
            self.setValve('O'),
            self.moveBy(-abs(steps)),
            self.wait(wait)
        ], channel=channel)
        command = self.current_pump.command
        print(f"Pump: {self.name}")
        print(f"Dispensing {volume}uL...")
        self.run()
        if pause:
            input("Press 'Enter' to proceed.")
        return command

    @_single_action
    def empty(self, channel:Optional[int] = None, **kwargs) -> str:
        """
        Empty the syringe pump

        Args:
            channel (int, optional): channel address. Defaults to None.

        Returns:
            str: command string
        """
        self.position = 0
        self.current_pump.position = self.position
        return "OA0"

    @_single_action
    def fill(self, channel:Optional[int] = None, **kwargs) -> str:
        """
        Fill the syringe pump

        Args:
            channel (int, optional): channel address. Defaults to None.

        Returns:
            str: command string
        """
        self.position = self.step_limit
        self.current_pump.position = self.position
        return f"IA{self.step_limit}"

    def getPosition(self, channel:Optional[int] = None) -> int:
        self.setCurrentChannel(channel=channel)
        response = self._query('?')
        self.position = int(response[3:]) if len(response) else self.position
        self.current_pump.position = self.position
        return self.position
    
    def getStatus(self, channel:Optional[int] = None) -> str:
        self.setCurrentChannel(channel=channel)
        response = self._query('Q')
        _status_code = response[2] if len(response) else ''
        if self.device is not None:
            if _status_code not in StatusCode.Busy and _status_code not in StatusCode.Idle:
                raise RuntimeError(f"Unable to get status from Pump: {self.name}")
    
        if _status_code in StatusCode.Busy.value:
            self.setFlag(busy=True)
            self.current_pump.busy = True
        elif _status_code in StatusCode.Idle.value:
            self.setFlag(busy=False)
            self.current_pump.busy = False
        else:
            self.setFlag(busy=False)
            self.current_pump.busy = False
        
        code = 'er0'
        if _status_code.isalpha():
            index = 1 + string.ascii_lowercase.index(_status_code.lower())
            code = f"er{index}"
            print(ErrorCode[code].value)
            if index in [1,7,9,10]:
                raise ConnectionError(f"Please reinitialize: Pump {self.channel}.")
        self.current_pump.status = code
        return ErrorCode[code].value
 
    @_single_action
    def initialise(self, output_right:Optional[bool] = None, channel:Optional[int] = None) -> str:
        """
        Empty the syringe pump

        Args:
            output_right (str, optional): liquid output direction ('left' or 'right'). Defaults to None.
            channel (int, optional): channel address. Defaults to None.

        Returns:
            str: command string
        """
        output_right = self.current_pump.output_right if output_right is None else output_right
        command = 'Z' if output_right else 'Y'
        return command
    
    def isBusy(self) -> bool:
        """
        Check whether the device is busy

        Raises:
            Exception: Unable to determine whether the device is busy

        Returns:
            bool: whether the device is busy
        """
        self.getStatus()
        return super().isBusy()

    @staticmethod
    def loop(cycles:int, *args) -> str:
        """
        Specify how many times to loop the following actions

        Args:
            cycles (int): number of times to cycle

        Returns:
            str: command string
        """
        return f"g{''.join(args)}G{cycles}"
     
    @_single_action
    def move(self, steps:int, up:bool, channel:Optional[int] = None) -> str:
        """
        Move plunger either up or down

        Args:
            axis (str): desired direction of plunger (up / down)
            value (int): number of steps to move plunger by
            channel (int, optional): channel to move. Defaults to None.
        Raises:
            Exception: Axis direction either 'up' or 'down'

        Returns:
            str: command string
        """
        steps = abs(steps)
        command = ''
        if up:
            self.position -= steps
            command =  f"D{steps}"
        else:
            self.position += steps
            command =  f"P{steps}"
        self.current_pump.position = self.position
        return command
        
    @_single_action
    def moveBy(self, steps:int, channel:Optional[int] = None) -> str:
        """
        Move plunger by specified number of steps

        Args:
            steps (int): number of steps to move plunger by >0: aspirate/move down; <0 dispense/move up)
            channel (int, optional): channel to move by. Defaults to None.

        Returns:
            str: command string
        """
        self.position += steps
        self.current_pump.position = self.position
        command = f"P{abs(steps)}" if steps > 0 else f"D{abs(steps)}"
        return command
    
    @_single_action
    def moveTo(self, position:int, channel:Optional[int] = None) -> str:
        """
        Move plunger to specified position

        Args:
            position (int): desired plunger position
            channel (int, optional): channel to move to. Defaults to None.

        Returns:
            str: command string
        """
        self.position = position
        self.current_pump.position = self.position
        return f"A{position}"
    
    def prime(self, cycles:int = 3, channel:Optional[int] = None) -> str:
        """
        Prime the pump by cycling the plunger through its max and min positions

        Args:
            cycles (int): number of times to cycle
            channel (int, optional): channel to prime. Defaults to None.
            
        Returns:
            str: command string
        """
        command = self.rinse(cycles=cycles, channel=channel, print_message=False)
        print(f"Priming complete")
        return command
    
    def pullback(self, channel: Optional[Union[int, tuple[int]]] = None, **kwargs) -> bool: # NOTE: no implementation
        return ''

    def queue(self, actions:list[str], channel:Optional[int] = None) -> str:
        """
        Queue several commands together before sending to the device

        Args:
            actions (list, optional): list of actions. Defaults to [].
            channel (int, optional): channel to set. Defaults to None.

        Returns:
            str: command string
        """
        self.setCurrentChannel(channel=channel)
        command = ''.join(actions)
        self.current_pump.command = self.current_pump.command + command
        return command
    
    def reset(self, channel:Optional[int] = None) -> str:
        """
        Reset and initialise the device

        Args:
            channel (int, optional): channel to reset. Defaults to None.
        """
        return self.initialise()
    
    def resetChannel(self):
        self.setCurrentChannel(list(self.channels)[0])
        return
    
    @_compound_action
    def rinse(self, 
        speed: int = 200, 
        wait: int = 0, 
        cycles: int = 3, 
        start_speed: int = 50,
        channel: Optional[Union[int, tuple[int]]] = None,
        **kwargs
    ) -> str:
        self.queue([
            self.initialise(),
            self.setStartSpeed(start_speed),
            self.setTopSpeed(speed),
            self.setSpeedRamp(1),
            self.loop(cycles,
                self.fill(),
                self.wait(wait),
                self.empty(),
                self.wait(wait)
            )
        ], channel=channel)
        command = self.current_pump.command
        print(f"Pump: {self.name}")
        self.run()
        if kwargs.get('print_message', True):
            print(f"Rinsing complete")
        return command

    def run(self, command:Optional[str] = None, channel:Optional[int] = None) -> str:
        """
        Send the command to the device and run the action

        Args:
            command (str, optional): command string of commands. Defaults to None.
            channel (int, optional): channel to run. Defaults to None.

        Returns:
            str: command string
        """
        self.setCurrentChannel(channel=channel)
        if command is None:
            command = self.current_pump.command
            self.current_pump.command = ''
        command = f"{command}R"
        self._query(command)
        while self.isBusy():
            time.sleep(0.2)
        if 'Z' in command or 'Y' in command:
            self.current_pump.init_status = True
        self.getPosition()
        self.getStatus()
        return command
    
    def setCurrentChannel(self, channel:Optional[int] = None) -> TriContinentPump:
        channel = self.channel if channel not in self.channels else channel
        self.current_channel = self.channels[channel]
        pump = self.current_pump
        
        self.channel = pump.channel
        self.name = pump.name
        self.capacity = pump.capacity
        self.resolution = pump.resolution
        self.step_limit = pump.step_limit
        self.position = pump.position
        return
 
    @_single_action
    def setSpeedRamp(self, ramp:int, channel:Optional[int] = None) -> str:
        """
        Set the ramp up between start speed and top speed

        Args:
            ramp (int): ramp speed
            channel (int, optional): channel to set. Defaults to None.

        Returns:
            str: command string
        """
        return f"L{ramp}"
    
    @_single_action
    def setStartSpeed(self, speed:int, channel:Optional[int] = None) -> str:
        """
        Set the starting speed of the plunger

        Args:
            speed (int): starting speed of plunger
            channel (int, optional): channel to set. Defaults to None.

        Returns:
            str: command string
        """
        return f"v{speed}"
    
    @_single_action
    def setTopSpeed(self, speed:int, channel:Optional[int] = None) -> str:
        """
        Set the top speed of the plunger

        Args:
            speed (int): top speed of plunger
            channel (int, optional): channel to set. Defaults to None.

        Returns:
            str: command string
        """
        self.speed = Speed(speed,speed)
        return f"V{speed}"
    
    @_single_action
    def setValve(self, 
        valve: str, 
        value: Optional[int] = None, 
        channel: Optional[int] = None
    ) -> str:
        """
        Set valve position to one of [I]nput, [O]utput, [B]ypass, [E]xtra

        Args:
            valve (str): one of the above positions
            value (int, optional): only for 6-way distribution. Defaults to None.
            channel (int, optional): channel to set. Defaults to None.

        Raises:
            Exception: Please select a valid position

        Returns:
            str: command string
        """
        valves = ['I','O','B','E']
        valve = valve.upper()[0]
        if valve not in valves:
            raise Exception(f"Please select a valve position from {', '.join(valves)}")
        command = valve
        if value in [1,2,3,4,5,6]:
            command = f'{valve}{value}'
        return command
   
    def stop(self, channel:Optional[int] = None) -> str:
        """
        Stops the device immediately, terminating any actions in progress or in queue

        Args:
            channel (int, optional): channel to stop. Defaults to None.

        Returns:
            str: command string
        """
        _channel = self.channel
        self.channel = _channel if channel is None else channel
        response = self._query('T')
        self.channel = _channel
        return response
   
    @_single_action
    def wait(self, time_ms:int, channel:Optional[int] = None) -> str:
        """
        Wait for a specified amount of time

        Args:
            time_ms (int): duration in milliseconds
            channel (int, optional): channel to wait. Defaults to None.

        Returns:
            str: command string
        """
        command = f"M{time_ms}" if time_ms else ""
        return command

    # Protected method(s)
    @staticmethod
    def _get_pumps(**kwargs) -> dict[int, TriContinentPump]:
        channel_arg = kwargs.get('channel', 1)
        n_channel = 1 if type(channel_arg) is int else len(channel_arg)
        for key, arg in kwargs.items():
            if type(arg) is not tuple and type(arg) is not list:
                kwargs[key] = [arg] * n_channel
            elif len(arg) != n_channel:
                raise ValueError("Ensure that the length of inputs are the same as the number of channels.")
        properties = Helper.zip_inputs(primary_keyword='channel', **kwargs)
        return {key: TriContinentPump(**value) for key,value in properties.items()}
    
    def _is_expected_reply(self, response:str, **kwargs) -> bool:
        """
        Check whether the response is an expected reply

        Args:
            command_code (str): two-character command code
            response (str): response string from device

        Returns:
            bool: whether the response is an expected reply
        """
        if len(response) == 0:
            return False
        if response[0] != '/':
            return False
        if response[1] != str(self.channel) and response[1] != str(0):
            return False
        return True
    
    def _query(self, command:str, timeout_s:int = 2) -> str:
        """
        Send query and wait for response

        Args:
            command (str): command string
            timeout_s (int, optional): duration to wait before timeout. Defaults to 2.

        Returns:
            str: command readout
        """
        # self.connect()
        start_time = time.time()
        self._write(command)
        response = ''
        while not self._is_expected_reply(response):
            if not self.isConnected():
                break
            if time.time() - start_time > timeout_s:
                break
            response = self._read()
            if response == '__break__':
                response = ''
                break
        # print(time.time() - start_time)
        # self.disconnect()
        return response

    def _read(self) -> str:
        """
        Read response from device

        Returns:
            str: response string
        """
        response = ''
        try:
            response = self.device.read_until().decode('utf-8')
            response = response.split('\x03')[0]
        except AttributeError:
            pass
        except Exception as e:
            if self.verbose:
                print(e)
            response = '__break__'
        return response
    
    def _write(self, command:str) -> bool:
        """
        Sends command to device

        Args:
            command (str): <command code><value>

        Returns:
            str: two-character command code
        """
        if self.verbose:
            print(command)
        fstring = f'/{self.channel}{command}\r' # command template: <PRE><ADR><STRING><POST>
        try:
            # Typical timeout wait is 2s
            self.device.write(fstring.encode('utf-8'))
        except AttributeError:
            pass
        except Exception as e:
            if self.verbose:
                print(e)
            return False
        return True
    

### NOTE: DEPRECATE
# class TriContinentEnsemble(Pump):
#     def __init__(self, 
#         port: str, 
#         channels: int, 
#         models: str, 
#         capacities: int, 
#         output_rights: bool, 
#         names: str = '',
#         **kwargs
#     ):
#         super().__init__(port=port, **kwargs)
#         self.disconnect()
#         verbose = kwargs.pop('verbose', False)
#         self.channels = self._get_pumps(
#             primary_keyword = 'channel',
#             port = [port]*len(channels),
#             channel = channels,
#             model = models,
#             capacity = capacities,
#             output_right = output_rights,
#             name = names,
#             device = [self.device]*len(channels),
#             verbose = [verbose]*len(channels)
#         )
        
#         # if len(ports) == 1:
#         #     super().__init__(ports[0], verbose)
#         #     properties = Helper.zip_inputs('channel',
#         #         port=ports*len(channels),
#         #         channel=channels,
#         #         model=models,
#         #         output_right=output_directions,
#         #         capacity=syringe_volumes,
#         #         name=names,
#         #         device=[self.device]*len(channels),
#         #         verbose=verbose
#         #     )
#         # self.channels = {key: TriContinent(**value) for key,value in properties.items()}
#         self.current_channel = None
#         return
    
#     @staticmethod
#     def _get_pumps(primary_keyword:str, **kwargs) -> dict[int, TriContinent]:
#         properties = Helper.zip_inputs(primary_keyword=primary_keyword, **kwargs)
#         return {key: TriContinent(**value) for key,value in properties.items()}
    
#     @staticmethod
#     def loop(cycles, *args):
#         return TriContinent.loop(cycles, *args)
    
#     # Single actions
#     def empty(self, channel:Optional[int] = None):
#         return self.channels.get(channel, self.current_channel).empty()
#     def fill(self, channel:Optional[int] = None):
#         return self.channels.get(channel, self.current_channel).fill()
#     def initialise(self, output_right:str = None, channel:Optional[int] = None):
#         return self.channels.get(channel, self.current_channel).initialise(output_right=output_right)
#     def moveBy(self, steps:int, channel:Optional[int] = None):
#         return self.channels.get(channel, self.current_channel).moveBy(steps=steps)
#     def moveTo(self, position:int, channel:Optional[int] = None):
#         return self.channels.get(channel, self.current_channel).moveTo(position=position)
#     def setSpeedRamp(self, ramp:int, channel:Optional[int] = None):
#         return self.channels.get(channel, self.current_channel).setSpeedRamp(ramp=ramp)
#     def setStartSpeed(self, speed:int, channel:Optional[int] = None):
#         return self.channels.get(channel, self.current_channel).setStartSpeed(speed=speed)
#     def setTopSpeed(self, speed:int, channel:Optional[int] = None):
#         return self.channels.get(channel, self.current_channel).setTopSpeed(speed=speed)
#     def setValve(self, position:str, value:int = None, channel:Optional[int] = None):
#         return self.channels.get(channel, self.current_channel).setValve(position=position, value=value)
#     def wait(self, time_ms:int, channel:Optional[int] = None):
#         return self.channels.get(channel, self.current_channel).wait(time_ms=time_ms)

#     # Standard actions
#     def isBusy(self):
#         return any([pump.isBusy() for pump in self.channels.values()])
#     def queue(self, actions:list = [], channel:Optional[int] = None):
#         return self.channels.get(channel, self.current_channel).queue(actions)
#     def reset(self, channel:Optional[int] = None):
#         return self.channels.get(channel, self.current_channel).reset()
#     def run(self, command:str = None, channel:Optional[int] = None):
#         return self.channels.get(channel, self.current_channel).run(command)
#     def stop(self, channel:Optional[int] = None):
#         return self.channels.get(channel, self.current_channel).stop()
    
#     # Compound actions
#     def aspirate(self, volume:int, start_speed:int = 50, top_speed:int = 200, channel:Optional[int] = None):
#         return self.channels.get(channel, self.current_channel).aspirate(volume=volume, start_speed=start_speed, top_speed=top_speed)
#     def cycle(self, cycles:int, channel:Optional[int] = None):
#         return self.channels.get(channel, self.current_channel).cycle(cycles=cycles)
#     def dispense(self, volume:int, start_speed:int = 50, top_speed:int = 200, channel:Optional[int] = None):
#         return self.channels.get(channel, self.current_channel).dispense(volume=volume, start_speed=start_speed, top_speed=top_speed)
#     def dose(self, volume:int, start_speed:int = 50, top_speed:int = 200, channel:Optional[int] = None):
#         return self.channels.get(channel, self.current_channel).dose(volume=volume, start_speed=start_speed, top_speed=top_speed)
#     def prime(self, cycles:int, channel:Optional[int] = None):
#         return self.channels.get(channel, self.current_channel).prime(cycles=cycles)
#     def rinse(self, cycles:int, channel:Optional[int] = None):
#         return self.channels.get(channel, self.current_channel).rinse(cycles=cycles)
    