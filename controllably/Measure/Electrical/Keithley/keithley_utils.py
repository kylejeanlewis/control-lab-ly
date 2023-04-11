# %% -*- coding: utf-8 -*-
"""
This module holds the class for tools from Keithley.

Classes:
    Keithley (Programmable)
"""
# Local application imports
from __future__ import annotations
from ...measure_utils import Programmable
from .keithley_device import KeithleyDevice
from . import programs
print(f"Import: OK <{__name__}>")

class Keithley(Programmable):
    """
    Keithley provides methods to control potentiometers from Keithley
    
    ### Constructor
    Args:
        `ip_address` (str): IP address of device. Defaults to '192.168.1.125'.
        `name` (str): name of device. Defaults to 'def'.
        
    ### Properties
    - `ip_address` (str): IP address of device
    
    ### Methods
    - `disconnect`: disconnect from device
    """
    model = 'keithley_'
    available_programs: tuple[str] = tuple(programs.PROGRAM_NAMES)      # FIXME
    possible_inputs: tuple[str] = tuple(programs.INPUTS_SET)            # FIXME
    def __init__(self, ip_address:str = '192.168.1.125', name:str = 'def', **kwargs):
        """
        Instantiate the class
        
        Args:
            ip_address (str): IP address of device. Defaults to '192.168.1.125'.
            name (str): name of device. Defaults to 'def'.
        """
        super().__init__(**kwargs)
        self._connect(ip_address=ip_address, name=name)
        return

    # Properties
    @property
    def ip_address(self) -> str:
        return self.connection_details.get('ip_address', '')

    def disconnect(self):
        self.device.close()
        return

    # Protected method(s)
    def _connect(self, ip_address:str, name:str = 'def'):
        """
        Connection procedure for tool

        Args:
            ip_address (str): IP address of device
            name (str): name of device
        """
        self.connection_details = {
            'ip_address': ip_address,
            'name': name
        }
        self._ip_address = ip_address
        self.device = KeithleyDevice(ip_address=ip_address, name=name)
        return
