# %% -*- coding: utf-8 -*-
"""
Created: Tue 2023/01/03 17:13:35
@author: Chang Jie

Notes / actionables:
-
"""
# Standard library imports

# Local application imports
from __future__ import annotations
from ..mechanical_utils import Mechanical
from .piezorobotics_device import PiezoRoboticsDevice
from . import programs
print(f"Import: OK <{__name__}>")
        
class PiezoRobotics(Mechanical):
    """
    PiezoRobotics object

    Args:
        port (str): com port address to device
        channel (int, optional): assigned device serial number. Defaults to 1.
    """
    _default_program = programs.DMA
    model = 'piezorobotics_'
    available_programs: tuple[str] = tuple(programs.PROGRAM_NAMES)      # FIXME
    possible_inputs: tuple[str] = tuple(programs.INPUTS_SET)            # FIXME
    def __init__(self, port:str, channel=1, **kwargs):
        super().__init__(**kwargs)
        self._connect(port=port, channel=channel)
        return
    
    # Properties
    @property
    def port(self) -> str:
        return self.connection_details.get('port', '')
    
    def disconnect(self):
        self.device.close()
        return

    # Protected method(s)
    def _connect(self, port:str, channel:int = 1):
        """
        Connect to device

        Args:
            port (str): com port address
            channel (int, optional): assigned device serial number. Defaults to 1.
            
        Returns:
            PiezoRoboticsDevice: PiezoRoboticsDevice object
        """
        self.connection_details = {
            'port': port,
            'channel': channel
        }
        self.device = PiezoRoboticsDevice(port=port, channel=channel)
        return
 