# %% -*- coding: utf-8 -*-
"""
This module holds the base class for liquid pumps.

Classes:
    Pump (LiquidHandler)
"""
# Standard library imports
import logging
import time

# Third party imports
import serial # pip install pyserial

# Local application imports
from ..liquid_utils import LiquidHandler

logger = logging.getLogger(__name__)
logger.debug(f"Import: OK <{__name__}>")

class Pump(LiquidHandler):
    """
    Abstract Base Class (ABC) for Pump objects (i.e. tools that moves liquids).
    ABC cannot be instantiated, and must be subclassed with abstract methods implemented before use.
    
    ### Constructor
    Args:
        `port` (str): COM port address
    
    ### Properties
    - `port` (str): COM port address
    
    ### Methods
    #### Abstract
    - `aspirate`: aspirate desired volume of reagent
    - `blowout`: blowout liquid from tip
    - `dispense`: dispense desired volume of reagent
    - `pullback`: pullback liquid from tip
    #### Public
    - `disconnect`: disconnect from device
    """
    
    def __init__(self, port:str, **kwargs):
        """
        Instantiate the class

        Args:
            port (str): COM port address
        """
        super().__init__(**kwargs)
        self._connect(port)
        return
    
    # Properties
    @property
    def port(self) -> str:
        return self.connection_details.get('port', '')
    
    def disconnect(self):
        """Disconnect from device"""
        try:
            self.device.close()
        except Exception as e:
            if self.verbose:
                print(e)
        self.setFlag(connected=False)
        return
     
    # Protected method(s)
    def _connect(self, port:str, baudrate:int = 9600, timeout:int = 1):
        """
        Connection procedure for tool

        Args:
            port (str): COM port address
            baudrate (int, optional): baudrate. Defaults to 9600.
            timeout (int, optional): timeout in seconds. Defaults to 1.
        """
        self.connection_details = {
            'port': port,
            'baudrate': baudrate,
            'timeout': timeout
        }
        device = None
        try:
            device = serial.Serial(port, baudrate, timeout=timeout)
        except Exception as e:
            print(f"Could not connect to {port}")
            if self.verbose:
                print(e)
        else:
            time.sleep(2)   # Wait for grbl to initialize
            device.reset_input_buffer()
            print(f"Connection opened to {port}")
            self.setFlag(connected=True)
        self.device = device
        return
    
    def _write(self, command:str) -> bool:
        """
        Write command to device

        Args:
            command (str): command string

        Returns:
            bool: whether command was sent successfully
        """
        if self.verbose:
            print(command)
        try:
            self.device.write(command.encode('utf-8'))
        except Exception as e:
            if self.verbose:
                print(e)
            return False
        return True
