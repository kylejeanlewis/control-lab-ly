# %% -*- coding: utf-8 -*-
"""
This module holds the program class for tools from PiezoRobotics.

Classes:
    DMA (Program)

Other constants and variables:
    FREQUENCIES (tuple)
"""
# Standard library imports
from datetime import datetime
import pandas as pd
import time
from typing import Optional, Protocol

# Local application imports
from ....program_utils import Program
print(f"Import: OK <{__name__}>")

class Device(Protocol):
    def initialise(self, *args, **kwargs):
        ...
    def readAll(self, *args, **kwargs):
        ...
    def run(self, *args, **kwargs):
        ...
    def toggleClamp(self, *args, **kwargs):
        ...
    
class pHMonitor(Program):
    """
    ph Monitor

    ### Constructor
    Args:
        `device` (Device): device object
        `parameters` (Optional[dict], optional): dictionary of kwargs. Defaults to None.
        `verbose` (bool, optional): verbosity of class. Defaults to False.
    
    ### Attributes
    - `data_df` (pd.DataFrame): data collected from device when running the program
    - `device` (Device): device object
    - `parameters` (dict[str, ...]): parameters
    - `verbose` (bool): verbosity of class
    
    ### Methods
    - `run`: run the measurement program
    
    ==========
    
    ### Parameters:
        duration (float): duration, in seconds, to monitor the pH. Defaults to 10.
    """
    
    def __init__(self, 
        device: Device, 
        parameters: Optional[dict] = None,
        verbose: bool = False, 
        **kwargs
    ):
        """
        Instantiate the class

        Args:
            device (Device): device object
            parameters (Optional[dict], optional): dictionary of kwargs. Defaults to None.
            verbose (bool, optional): verbosity of class. Defaults to False.
        """
        super().__init__(device=device, parameters=parameters, verbose=verbose, **kwargs)
        return
    
    def run(self):
        """Run the measurement program"""
        device = self.device
        duration = self.parameters.get('duration', 10)
        device.toggleFeedbackLoop(True)
        time.sleep(duration)
        device.toggleFeedbackLoop(False)
        self.data_df = device.buffer_df
        return
