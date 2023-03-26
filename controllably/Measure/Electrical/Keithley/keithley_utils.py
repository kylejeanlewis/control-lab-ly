# %% -*- coding: utf-8 -*-
"""
Created: Tue 2022/11/02 17:13:35
@author: Chang Jie

Notes / actionables:
- validation on copper
"""
# Local application imports
from ..electrical_utils import Electrical
from .keithley_device import KeithleyDevice
print(f"Import: OK <{__name__}>")

class Keithley(Electrical):
    """
    Keithley class.
    
    Args:
        ip_address (str, optional): IP address of Keithley. Defaults to '192.168.1.125'.
        name (str, optional): nickname for Keithley. Defaults to 'def'.
    """
    model = 'keithley_'
    def __init__(self, ip_address:str = '192.168.1.125', name:str = 'def', **kwargs):
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
        Connect to device

        Args:
            ip_address (str): IP address of the Biologic device
            name (str): nickname for Keithley.
            
        Returns:
            KeithleyDevice: object representation
        """
        self.connection_details = {
            'ip_address': ip_address,
            'name': name
        }
        self._ip_address = ip_address
        self.device = KeithleyDevice(ip_address=ip_address, name=name)
        return
