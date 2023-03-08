# %% -*- coding: utf-8 -*-
"""
Adapted from @aniketchitre C3000_SyringePumpsv2

Created: Tue 2022/11/01 17:13:35
@author: Chang Jie

Notes / actionables:
-
"""
# Standard library imports
import string
import time

# Third party imports

# Local application imports
from ....misc import Helper
from .pump_utils import Pump
from .tricontinent_lib import ErrorCode, StatusCode
from .tricontinent_lib import ERRORS, STATUSES
print(f"Import: OK <{__name__}>")

READ_TIMEOUT_S = 2

class TriContinent(Pump):
    def __init__(self, port:str, channel:int, model:str, output_direction:str, syringe_volume:int, name:str = '', device=None, verbose=False):
        if device is None:
            super().__init__(port, verbose)
        else:
            super().__init__('', verbose)
            self.device = device
            self.port = port
        
        self.action_message = ''
        self.channel = channel
        self.model = model
        self.name = name
        self.output_direction = ''
        self.step_limit = int(''.join(filter(str.isdigit, self.model)))
        self.syringe_volume = syringe_volume
        self.resolution = self.syringe_volume / self.step_limit
        
        self._flags['init_status'] = False
        self._flags['execute_now'] = True
        
        self.initialise(output_direction)
        return
    
    # Properties
    @property
    def position(self):
        response = self._query('?')
        _position = int(response[3:]) if len(response) else -1
        return _position
    
    @property
    def status(self):
        response = self._query('Q')
        _status_code = response[2] if len(response) else ''
        if _status_code not in STATUSES and self.device is not None:
            raise Exception(f"Unable to get status from pump {self.channel}")
    
        busy = None
        if _status_code in StatusCode.Busy.value:
            busy = True
        elif _status_code in StatusCode.Idle.value:
            busy = False
        
        code = ''
        if _status_code.isalpha():
            index = 1 + string.ascii_lowercase.index(_status_code.lower())
            code = f"er{index}"
            print(ErrorCode[code].value)
            if index in [1,7,9,10]:
                raise Exception(f"Please reinitialize pump {self.channel}.")
        else:
            code = 'er0'
        error = ErrorCode[code].value if code in ERRORS else 'Unknown'
        return busy, error
    
    def _is_expected_reply(self, message:str, response:str):
        if len(response) == 0:
            return False
        if response[0] != '/':
            return False
        if response[1] != str(self.channel) and response[1] != str(0):
            return False
        return True
    
    def _query(self, message_string:str, timeout_s=READ_TIMEOUT_S):
        """
        Send query and wait for response

        Args:
            message_string (str): message string
            timeout_s (int, optional): duration to wait before timeout. Defaults to READ_TIMEOUT_S.

        Returns:
            str: message readout
        """
        start_time = time.time()
        message = self._write(message_string=message_string)
        response = ''
        while not self._is_expected_reply(message, response):
            if time.time() - start_time > timeout_s:
                break
            response = self._read()
            if response == '__break__':
                response = ''
                break
        # print(time.time() - start_time)
        return response

    def _read(self):
        """
        Read response from device

        Returns:
            str: response string
        """
        response = ''
        try:
            response = self.device.read_until().decode('utf-8')
            response = response.split('\x03')[0]
        except Exception as e:
            if self.verbose:
                print(e)
                response = '__break__'
        return response
    
    def _write(self, message_string:str):
        """
        Sends message to device

        Args:
            message_string (str): <message code><value>

        Returns:
            str: two-character message code
        """
        fstring = f'/{self.channel}{message_string}\r' # message template: <PRE><ADR><STRING><POST>
        bstring = fstring.encode('utf-8')
        try:
            # Typical timeout wait is 2s
            self.device.write(bstring)
        except Exception as e:
            if self.verbose:
                print(fstring)
                print(e)
        return fstring
    
    # Decorators
    def _single_action(func):
        def wrapper(self, *args, **kwargs):
            message = func(self, *args, **kwargs)
            if self._flags.get('execute_now', False):
                return self.run(message)
            return message
        return wrapper
    
    def _compound_action(func):
        def wrapper(self, *args, **kwargs):
            self.setFlag('execute_now', False)
            message = func(self, *args, **kwargs)
            self.setFlag('execute_now', True)
            return message
        return wrapper
    
    @staticmethod
    def loop(cycles, *args):
        return f"g{''.join(args)}G{cycles}"
    
    # Single actions
    @_single_action
    def empty(self, channel:int = None):
        message = "OA0"
        return message
    
    @_single_action
    def fill(self, channel:int = None):
        message = f"IA{self.step_limit}"
        return message
    
    @_single_action
    def initialise(self, output_direction:str = None, channel:int = None):
        if output_direction is None:
            output_direction = self.output_direction
        else:
            output_direction = output_direction.upper()[0]
        if output_direction not in ['L', 'R']:
            raise Exception("Please input either '[L]eft' or '[R]ight'.")
        self.output_direction = output_direction
        message = 'Z' if output_direction == 'R' else 'Y'
        return message
    
    @_single_action
    def moveBy(self, steps:int, channel:int = None):
        message = f"P{abs(steps)}" if steps >0 else f"D{abs(steps)}"
        return message
    
    @_single_action
    def moveTo(self, position:int, channel:int = None):
        message = f"A{position}"
        return message
    
    @_single_action
    def setSpeedRamp(self, ramp:int, channel:int = None):
        message = f"L{ramp}"
        return message
    
    @_single_action
    def setStartSpeed(self, speed:int, channel:int = None):
        message = f"v{speed}"
        return message
    
    @_single_action
    def setTopSpeed(self, speed:int, channel:int = None):
        message = f"V{speed}"
        return message
    
    @_single_action
    def setValve(self, position:str, value:int = None, channel:int = None):
        """
        Set valve position to one of [I]nput, [O]utput, [B]ypass, [E]xtra

        Args:
            position (str): one of the above positions
            value (int, optional): only for 6-way distribution. Defaults to None.

        Raises:
            Exception: Please select a valid position

        Returns:
            str: machine message
        """
        positions = ['I','O','B','E']
        position = position.upper()[0]
        if position not in positions:
            raise Exception(f"Please select a position from {', '.join(positions)}")
        message = position
        if value in [1,2,3,4,5,6]:
            message = f'{position}{value}'
        return message
    
    @_single_action
    def wait(self, time_ms:int, channel:int = None):
        message = f"M{time_ms}"
        return message
    
    # Standard actions
    def isBusy(self):
        busy,_ = self.status
        if busy is None and self.device is not None:
            raise Exception('Unable to determine whether the device is busy')
        return busy

    def queue(self, actions:list = [], channel:int = None):
        message = ''.join(actions)
        self.action_message = self.action_message + message
        return message
    
    def reset(self, channel:int = None):
        self.initialise()
        return
    
    def run(self, message:str = None, channel:int = None):
        if message is None:
            message = self.action_message
            self.action_message = ''
        message = f"{message}R"
        self._query(message)
        while self.isBusy():
            time.sleep(0.2)
        if 'Z' in message or 'Y' in message:
            self.setFlag('init_status', True)
        return message
    
    def stop(self, channel:int = None):
        response = self._query('T')
        return response
    
    # Compound actions
    @_compound_action
    def dose(self, volume:int, start_speed:int = 50, top_speed:int = 200, channel:int = None):
        steps = int(volume/self.resolution)
        volume = steps * self.resolution
        self.queue([
            self.setStartSpeed(start_speed),
            self.setTopSpeed(top_speed),
            self.setSpeedRamp(1)
        ])
        if self.position < 0.75*self.step_limit:
            self.queue([
                self.setValve('I'),
                self.moveTo(self.step_limit)
            ])
        self.queue([
            self.setValve('O'),
            self.moveBy(-abs(steps))
        ])
        self.run()
        print(f"Dispensing {volume}uL {self.name} is complete")
        return
    
    @_compound_action
    def prime(self, cycles:int, channel:int = None):
        self.queue([
            self.initialise(),
            self.setStartSpeed(50),
            self.setTopSpeed(200),
            self.setSpeedRamp(1),
            self.loop(cycles,
                self.setValve('I'),
                self.moveTo(self.step_limit),
                self.setValve('O'),
                self.moveTo(0)
            )
        ])
        self.run()
        print(f"Priming of pump {self.channel} complete")
        return


class TriContinentEnsemble(Pump):
    def __init__(self, ports:list, channels:list, models:list, output_directions: list, syringe_volumes: list, names: list = [], verbose=True):
        if len(ports) == 1:
            super().__init__(ports[0], verbose)
            properties = Helper.zip_inputs('channel',
                port=ports*len(channels),
                channel=channels,
                model=models,
                output_direction=output_directions,
                syringe_volume=syringe_volumes,
                name=names,
                device=[self.device]*len(channels),
                verbose=verbose
            )
        else:
            properties = Helper.zip_inputs('channel',
                port=ports,
                channel=channels,
                model=models,
                output_direction=output_directions,
                syringe_volume=syringe_volumes,
                name=names,
                verbose=verbose
            )
        self.channels = {key: TriContinent(**value) for key,value in properties.items()}
        self.current_channel = None
        return
    
    @staticmethod
    def loop(cycles, *args):
        return TriContinent.loop(cycles, *args)
    
    def empty(self, channel:int = None):
        return self.channels.get(channel, self.current_channel).empty()
    def fill(self, channel:int = None):
        return self.channels.get(channel, self.current_channel).fill()
    def initialise(self, output_direction:str = None, channel:int = None):
        return self.channels.get(channel, self.current_channel).initialise(output_direction=output_direction)
    def moveBy(self, steps:int, channel:int = None):
        return self.channels.get(channel, self.current_channel).moveBy(steps=steps)
    def moveTo(self, position:int, channel:int = None):
        return self.channels.get(channel, self.current_channel).moveTo(position=position)
    def setSpeedRamp(self, ramp:int, channel:int = None):
        return self.channels.get(channel, self.current_channel).setSpeedRamp(ramp=ramp)
    def setStartSpeed(self, speed:int, channel:int = None):
        return self.channels.get(channel, self.current_channel).setStartSpeed(speed=speed)
    def setTopSpeed(self, speed:int, channel:int = None):
        return self.channels.get(channel, self.current_channel).setTopSpeed(speed=speed)
    def setValve(self, position:str, value:int = None, channel:int = None):
        """
        Set valve position to one of [I]nput, [O]utput, [B]ypass, [E]xtra

        Args:
            position (str): one of the above positions
            value (int, optional): only for 6-way distribution. Defaults to None.

        Raises:
            Exception: Please select a valid position

        Returns:
            str: machine message
        """
        return self.channels.get(channel, self.current_channel).setValve(position=position, value=value)
    def wait(self, time_ms:int, channel:int = None):
        return self.channels.get(channel, self.current_channel).wait(time_ms=time_ms)

    # Standard actions
    def isBusy(self):
        return any([pump.isBusy() for pump in self.channels.values()])
    def queue(self, actions:list = [], channel:int = None):
        return self.channels.get(channel, self.current_channel).queue(actions)
    def reset(self, channel:int = None):
        return self.channels.get(channel, self.current_channel).reset()
    def run(self, message:str = None, channel:int = None):
        return self.channels.get(channel, self.current_channel).run(message)
    def stop(self, channel:int = None):
        return self.channels.get(channel, self.current_channel).stop()
    
    # Compound actions
    def dose(self, volume, channel:int = None):
        return self.channels.get(channel, self.current_channel).dose(volume=volume)
    def prime(self, cycles:int, channel:int = None):
        return self.channels.get(channel, self.current_channel).prime(cycles=cycles)
