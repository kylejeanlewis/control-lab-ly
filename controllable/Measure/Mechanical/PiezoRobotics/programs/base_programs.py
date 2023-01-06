# %% -*- coding: utf-8 -*-
"""
Created: Tue 2023/01/05 17:13:35
@author: Chang Jie

Notes / actionables:
-
"""
# Standard library imports
import pandas as pd
import time

# Local application imports
from ..piezorobotics_device import PiezoRoboticsDevice
from ..piezorobotics_lib import FREQUENCIES
print(f"Import: OK <{__name__}>")

class Program(object):
    """
    Base Program template

    Args:
        device (PiezoRoboticsDevice): PiezoRobotics Device object
        parameters (dict, optional): dictionary of measurement parameters. Defaults to {}.
    
    ==========
    Parameters:
        None
    """
    details = {
        'inputs_and_defaults': {},
        'short_doc': '',
        'tooltip': ''
    }
    def __init__(self, device:PiezoRoboticsDevice, parameters={}, **kwargs):
        self.device = device
        self.parameters = parameters
        
        self.data_df = pd.DataFrame
        self._flags = {}
        return
    
    @classmethod
    def getDetails(cls, verbose=False):
        """
        Get the input fields and defaults
        
        Args:
            verbose: whether to print out truncated docstring. Defaults to False.

        Returns:
            dict: dictionary of program details
        """
        doc = cls.__doc__
        
        # Extract truncated docstring and parameter listing
        lines = doc.split('\n')
        start, end = 0,0
        for i,line in enumerate(lines):
            line = line.strip()
            if line.startswith('Args:'):
                start = i
            if line.startswith('==========') and start:
                end = i
                break
        parameter_list = sorted([_l.strip() for _l in lines[end+2:] if len(_l.strip())])
        short_lines = lines[:start-1] + lines[end:]
        short_doc = '\n'.join(short_lines)
        tooltip = '\n'.join(['Parameters:'] + [f'- {_p}' for _p in parameter_list])
        if verbose:
            print(short_doc)
        
        # Extract input fields and defaults
        input_parameters = {}
        for parameter in parameter_list:
            if len(parameter) == 0:
                continue
            _input = parameter.split(' ')[0]
            _default = parameter.split(' ')[-1][:-1] if 'Defaults' in parameter else ''
            input_parameters[_input] = _default
        
        cls.details = {
            'inputs_and_defaults': input_parameters,
            'short_doc': short_doc,
            'tooltip': tooltip
        }
        return cls.details
    
    def run(self):
        """
        Run the measurement program
        """
        return
    
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
        sample_thickness (float): thickness of measured sample
    """
    def __init__(self, device:PiezoRoboticsDevice, parameters={}, **kwargs):
        super().__init__(device, parameters, **kwargs)
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
        
        input("Please load sample. Press 'Enter' to proceed")
        device.toggleClamp(True)
        for i in range(repeat):
            device.start(sample_thickness=self.parameters.get('sample_thickness', 1E-3))
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
INPUTS = [item for item in [[key for key in prog.getDetails().get('inputs_and_defaults', {})] for prog in PROGRAMS]]
INPUTS_SET = sorted( list(set([item for sublist in INPUTS for item in sublist])) )
