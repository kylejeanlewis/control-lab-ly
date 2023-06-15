# %% -*- coding: utf-8 -*-
"""
This module holds the class for tools from PiezoRobotics.

Classes:
    PiezoRobotics (Programmable)
"""
# Standard library imports
from __future__ import annotations

# Local application imports
from ...measure_utils import Programmable
from .piezorobotics_device import PiezoRoboticsDevice
from . import programs
print(f"Import: OK <{__name__}>")
        
class PiezoRobotics(Programmable):
    """
    PiezoRobotics provides methods to control the characterisation device from PiezoRobotics

    ### Constructor
    Args:
        `port` (str): COM port address
        `channel` (int, optional): channel id. Defaults to 1.
    
    ### Properties
    - `port` (str): COM port address
    
    ### Methods
    - `disconnect`: disconnect from device
    """
    
    _default_program = programs.DMA
    _place: str = '.'.join(__name__.split('.')[1:-1])
    model = 'piezorobotics_'
    def __init__(self, port:str, channel=1, **kwargs):
        """
        Instantiate the class

        Args:
            port (str): COM port address
            channel (int, optional): channel id. Defaults to 1.
        """
        super().__init__(**kwargs)
        self._connect(port=port, channel=channel)
        return
    
    # Properties
    @property
    def port(self) -> str:
        return self.connection_details.get('port', '')
    
    def disconnect(self):
        """Disconnect from device"""
        self.device.close()
        return

    # Protected method(s)
    def _connect(self, port:str, channel:int = 1):
        """
        Connection procedure for tool

        Args:
            port (str): COM port address
            channel (int, optional): assigned device serial number. Defaults to 1.
        """
        self.connection_details = {
            'port': port,
            'channel': channel
        }
        self.device = PiezoRoboticsDevice(port=port, channel=channel)
        return
 