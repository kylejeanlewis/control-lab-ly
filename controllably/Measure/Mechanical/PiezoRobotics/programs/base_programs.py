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
from ..piezorobotics_lib import FrequencyCode
print(f"Import: OK <{__name__}>")

FREQUENCIES = tuple([frequency.value for frequency in FrequencyCode])
"""Collection of all available frequency values"""

class Device(Protocol):
    def initialise(self, *args, **kwargs):
        ...
    def readAll(self, *args, **kwargs):
        ...
    def run(self, *args, **kwargs):
        ...
    def toggleClamp(self, *args, **kwargs):
        ...
    
class DMA(Program):
    """
    Dynamic Mechanical Analysis

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
        low_frequency (float): lower frequency limit to test
        high_frequency (float): upper frequency limit to test
        sample_thickness (float): thickness of measured sample. Defaults to 1E-3.
        repeat (int): number of times to run the measurement. Defaults to 1.
        pause (bool): whether to pause for loading samples. Defaults to True.
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
        repeat = self.parameters.get('repeat', 1)
        device.toggleClamp(False)
        device.initialise(
            low_frequency=self.parameters.get('low_frequency', FREQUENCIES[0]), 
            high_frequency=self.parameters.get('high_frequency', FREQUENCIES[-1])
        )
        
        if self.parameters.get('pause', True):
            input("Please load sample. Press 'Enter' to proceed")
        device.toggleClamp(True)
        for i in range(repeat):
            print(f"Start run {i+1} at {datetime.now()}")
            device.run(sample_thickness=self.parameters.get('sample_thickness', 1E-3))
            print(f"End run {i+1} at {datetime.now()}")
            time.sleep(1)
            df = device.readAll()
            df['run'] = i+1
            if i == 0:
                self.data_df = df
            else:
                self.data_df = pd.concat([self.data_df, df], ignore_index=True)
        device.toggleClamp(False)
        return
