# %% -*- coding: utf-8 -*-
"""
Created: Tue 2022/11/02 17:13:35
@author: Chang Jie

Notes / actionables:
-
"""
# Standard library imports
import numpy as np
import pandas as pd
import pkgutil
import time

# Local application imports
from .....Analyse.Data.Types.scpi_datatype import SCPI
from ..keithley_utils import Device
print(f"Import: OK <{__name__}>")

DEVICE = Device

class Program(object):
    def __init__(self):
        self.data_df = pd.DataFrame()
        self.parameters = {}
        self.scpi = None
        
        self._program_template = None
        pass
    
    def run(self, device=DEVICE, field_titles=[], values=[], average=False, wait=0):
        # connect to device
        device._write(['*RST'])
        prompts = self.scpi.getPrompts()
        device._write(prompts['settings'])
        
        if len(values):
            for value in values:
                # if self.flags['stop_measure']:
                #     break
                prompt = [l.format(value=value) for l in prompts['inputs']]
                device._write(prompt)
                time.sleep(wait)
                df = device._read(prompts['outputs'], field_titles=field_titles, average=average)
                self.data_df = pd.concat([self.data_df, df], ignore_index=True)
        else:
            device._write(prompts['inputs'])
            time.sleep(wait)
            self.data_df = device._read(prompts['outputs'], field_titles=field_titles, average=average)

        device._write(['OUTP OFF'])
        # disconnect from device
        return
    
    def setParameters(self, params={}):
        if len(params) == 0:
            raise Exception('Please input parameters.')
        this_program = None
        this_program = SCPI(self._program_template.replace(**params))
        # self.flags['parameters_set'] = True
        self.program = this_program
        self.parameters = params
        return
