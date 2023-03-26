# %% -*- coding: utf-8 -*-
"""
Created: Tue 2023/01/05 17:13:35
@author: Chang Jie

Notes / actionables:
-
"""
# Standard library imports
from datetime import datetime
import pandas as pd
import time
from typing import Optional, Protocol

# Local application imports
from ....program_utils import Program, ProgramDetails
from ..piezorobotics_lib import FrequencyCode
print(f"Import: OK <{__name__}>")

FREQUENCIES = tuple([frequency.value for frequency in FrequencyCode])

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

    Args:
        device (PiezoRoboticsDevice): PiezoRobotics Device object
        parameters (dict, optional): dictionary of measurement parameters. Defaults to {}.
    
    ==========
    Parameters:
        low_frequency (float): lower frequency limit to test
        high_frequency (float): upper frequency limit to test
        sample_thickness (float): thickness of measured sample. Defaults to 1E-3.
        pause (bool): whether to pause for loading samples. Defaults to True.
    """
    def __init__(self, 
        device: Device, 
        parameters: Optional[dict] = None,
        verbose: bool = False, 
        **kwargs
    ):
        super().__init__(device=device, parameters=parameters, verbose=verbose **kwargs)
        return
    
    def run(self):
        """
        Run the measurement program
        """
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


PROGRAMS = [DMA]
PROGRAM_NAMES = [prog.__name__ for prog in PROGRAMS]
INPUTS = [item for item in [[key for key in prog.getDetails().inputs] for prog in PROGRAMS]]
INPUTS_SET = sorted( list(set([item for sublist in INPUTS for item in sublist])) )
