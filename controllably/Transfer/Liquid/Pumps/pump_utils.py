# %% -*- coding: utf-8 -*-
"""
Adapted from @jaycecheng spinutils

Created: Tue 2022/11/01 17:13:35
@author: Chang Jie

Notes / actionables:
-
"""
# Standard library imports
import time

# Third party imports
import serial # pip install pyserial

# Local application imports
from ..liquid_utils import LiquidHandler
print(f"Import: OK <{__name__}>")

class Pump(LiquidHandler):
    def __init__(self, port:str, **kwargs):
        super().__init__(**kwargs)
        self._connect(port, **kwargs)
        return
    
    def disconnect(self):
        """
        Disconnect serial connection to robot
        
        Returns:
            None: None is successfully disconnected, else serial.Serial
        """
        try:
            self.device.close()
        except Exception as e:
            if self.verbose:
                print(e)
        self.setFlag(connected=False)
        return self.device
     
    # Protected method(s)
    def _connect(self, port:str, baudrate:int = 9600, timeout:int = 1, **kwargs):
        """
        Connect to machine control unit

        Args:
            `port` (str): com port address
            `baudrate` (int, optional): baudrate. Defaults to 9600.
            `timeout` (int, optional): timeout in seconds. Defaults to 1.
            
        Returns:
            `serial.Serial`: serial connection to machine control unit if connection is successful, else `None`
        """
        self.connection_details = {
            'port': port,
            'baudrate': baudrate,
            'timeout': timeout
        }
        
        if device in kwargs:
            self.device = kwargs['device']
            return
        
        device = None
        try:
            device = serial.Serial(port, baudrate, timeout=timeout)
        except Exception as e:
            print(f"Could not connect to {port}")
            if self.verbose:
                print(e)
        else:
            time.sleep(2)   # Wait for grbl to initialize
            device.flushInput()
            print(f"Connection opened to {port}")
            self.setFlag(connected=True)
        self.device = device
        return
    
    def _write(self, message:str) -> bool:
        try:
            self.device.write(message.encode('utf-8'))
        except Exception as e:
            if self.verbose:
                print(e)
            return False
        return True
