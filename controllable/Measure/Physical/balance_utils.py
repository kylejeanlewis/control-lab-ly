# %% -*- coding: utf-8 -*-
"""
Created: Tue 2023/01/16 11:11:00
@author: Chang Jie

Notes / actionables:
-
"""
# Standard library imports
from threading import Thread
import time

# Third party imports
import serial # pip install pyserial

# Local application imports
print(f"Import: OK <{__name__}>")

DEFAULT_STEPS = {
    'air_gap': 10,
    'pullback': 5
}
READ_TIMEOUT_S = 2
WETTING_CYCLES = 1

# z = 250 (w/o tip)
# z = 330 (w/ tip)
class Sartorius:
    def __init__(self, port:str, **kwargs):
        """
        Sartorius object

        Args:
            port (str): com port address
            channel (int, optional): device channel. Defaults to 1.
            offset (tuple, optional): x,y,z offset of tip. Defaults to (0,0,0).
        """
        self.device = None
        self._flags = {
            'busy': False,
            'connected': False,
            'get_feedback': False,
            'pause_feedback':False
        }
        self._mass = 0
        self._precision = 3
        self._threads = {}
        
        self.verbose = True
        self.port = ''
        self._baudrate = None
        self._timeout = None
        self._connect(port)
        return
    
    @property
    def mass(self):
        return round(self._mass, self._precision)
    
    @property
    def precision(self):
        return 10**(-self._precision)
    
    def __delete__(self):
        self._shutdown()
        return
    
    def _connect(self, port:str, baudrate=9600, timeout=1):
        """
        Connect to machine control unit

        Args:
            port (str): com port address
            baudrate (int): baudrate. Defaults to 9600.
            timeout (int, optional): timeout in seconds. Defaults to None.
            
        Returns:
            serial.Serial: serial connection to machine control unit if connection is successful, else None
        """
        self.port = port
        self._baudrate = baudrate
        self._timeout = timeout
        device = None
        try:
            device = serial.Serial(port, self._baudrate, timeout=self._timeout)
            self.device = device
            print(f"Connection opened to {port}")
            self.setFlag('connected', True)
            self.zero()
            self.toggleFeedbackLoop(on=True)
        except Exception as e:
            if self.verbose:
                print(f"Could not connect to {port}")
                print(e)
        return self.device
    
    def _is_expected_reply(self, message_code:str, response:str):
        """
        Check whether the response is an expected reply

        Args:
            message_code (str): two-character message code
            response (str): response string from device

        Returns:
            bool: whether the response is an expected reply
        """
        # if response in ERRORS:
        #     return True
        # if message_code not in QUERIES and response == 'ok':
        #     return True
        # if message_code in QUERIES and response[:2] == message_code.lower():
        #     reply_code, data = response[:2], response[2:]
        #     if self.verbose:
        #         print(f'[{reply_code}] {data}')
        #     return True
        return False
    
    def _loop_feedback(self):
        """
        Feedback loop to constantly check status and liquid level
        """
        print('Listening...')
        while self._flags['get_feedback']:
            if self._flags['pause_feedback']:
                continue
            self.getMass()
        print('Stop listening...')
        return
    
    def _query(self, string:str, timeout_s=READ_TIMEOUT_S):
        """
        Send query and wait for response

        Args:
            string (str): message string
            timeout_s (int, optional): duration to wait before timeout. Defaults to READ_TIMEOUT_S.

        Returns:
            str: message readout
        """
        # message_code = string[:2]
        # if message_code not in STATUS_QUERIES:
        #     self.setFlag('pause_feedback', True)
        #     time.sleep(timeout_s)
        # if self.isBusy():
        #     time.sleep(timeout_s)
        
        # message_code = self._write(string)
        # _start_time = time.time()
        response = ''
        # while not self._is_expected_reply(message_code, response):
        #     if time.time() - _start_time > timeout_s:
        #         break
        #     response = self._read()
        # if message_code in QUERIES:
        #     response = response[2:]
        # if message_code not in STATUS_QUERIES:
        #     self.setFlag('pause_feedback', False)
        return response

    def _read(self):
        """
        Read response from device

        Returns:
            str: response string
        """
        response = ''
        try:
            response = self.device.readline()
            if len(response) == 0:
                response = self.device.readline()
            response = response[2:-2].decode('utf-8')
            # if response in ERRORS:
            #     print(ErrorCode[response].value)
            #     return response
            # elif response == 'ok':
            #     return response
        except Exception as e:
            if self.verbose:
                # print(e)
                pass
        return response
    
    def _shutdown(self):
        """
        Close serial connection and shutdown
        """
        self.toggleFeedbackLoop(on=False)
        self.device.close()
        self._flags = {
            'busy': False,
            'connected': False,
            'get_feedback': False,
            'pause_feedback':False
        }
        return
    
    def _write(self, string:str):
        """
        Sends message to device

        Args:
            string (str): <message code><value>

        Returns:
            str: two-character message code
        """
        message_code = string[:2]
        fstring = f'{self.channel}{string}º\r' # message template: <PRE><ADR><CODE><DATA><LRC><POST>
        bstring = bytearray.fromhex(fstring.encode('utf-8').hex())
        try:
            # Typical timeout wait is 400ms
            self.device.write(bstring)
        except Exception as e:
            if self.verbose:
                print(e)
        return message_code
    
    def connect(self):
        """
        Reconnect to device using existing port and baudrate
        
        Returns:
            serial.Serial: serial connection to machine control unit if connection is successful, else None
        """
        return self._connect(self.port, self._baudrate, self._timeout)
    
    def getMass(self):
        """
        Get the mass by measuring force response
        
        Returns:
            str: device response
        """
        response = self._query('DN')
        try:
            self._mass = int(response)
        except ValueError:
            pass
        return response

    def isBusy(self):
        """
        Checks whether the pipette is busy
        
        Returns:
            bool: whether the pipette is busy
        """
        return self._flags['busy']
    
    def isConnected(self):
        """
        Check whether pipette is connected

        Returns:
            bool: whether pipette is connected
        """
        return self._flags['connected']
   
    def reset(self):
        """
        Alias for zero
        
        Args:
            channel (int, optional): channel to reset. Defaults to None.

        Returns:
            str: device response
        """
        return self.zero()

    def setFlag(self, name:str, value:bool):
        """
        Set a flag truth value

        Args:
            name (str): label
            value (bool): flag value
        """
        self._flags[name] = value
        return
    
    def tare(self):
        """
        Alias for zero
        
        Args:
            channel (int, optional): channel to reset. Defaults to None.

        Returns:
            str: device response
        """
        return self.zero()
    
    def toggleFeedbackLoop(self, on:bool):
        """
        Toggle between start and stopping feedback loop
        
        Args:
            channel (int, optional): channel to toggle feedback loop. Defaults to None.

        Args:
            on (bool): whether to listen to feedback
        """
        self.setFlag('get_feedback', on)
        if on:
            thread = Thread(target=self._loop_feedback)
            thread.start()
            self._threads['feedback_loop'] = thread
        else:
            self._threads['feedback_loop'].join()
        return

    def zero(self):
        """
        Zero the plunger position
        
        Args:
            channel (int, optional): channel to zero. Defaults to None.

        Returns:
            str: device response
        """
        response = self._query('RZ')
        time.sleep(2)
        return response
