# %% -*- coding: utf-8 -*-
"""
Created on Fri 2022/06/18 09:00:00

@author: Chang Jie

Easy BioLogic package documentation can be found at:
https://github.com/bicarlsen/easy-biologic

Notes:
- (actionables)
"""
# Standard library imports
import nest_asyncio
import numpy as np
import os
import pandas as pd
import sys
import time

# Third party imports
import easy_biologic as biologic_api # pip install easy-biologic
import easy_biologic.base_programs as base_programs
from easy_biologic.program import BiologicProgram
import plotly.express as px # pip install plotly-express

# Local application imports
from eis_datatype import ImpedanceSpectrum
print(f"Import: OK <{__name__}>")

# CONSTANTS
IP_ADDRESS = '192.109.209.128'

# INITIALIZING
nest_asyncio.apply()

# %%
class BioLogic(object):
    def __init__(self, name='', address=IP_ADDRESS):
        self.name = name
        self.address = address
        self.inst = biologic_api.BiologicDevice(address, populate_info=True)
        self.buffer_df = pd.DataFrame()
        self.program = None
        self.flags = {
            'measured': False
        }
        return
    
    def _connect(self):
        return self.inst.connect()
    
    def _readData(self):
        try:
            self.buffer_df = pd.DataFrame(self.program.data[0], columns=self.program.field_titles)
            if len(self.program.data[0]):
                self.flags['read'] = True
            else:
                print("No data found.")
        except AttributeError:
            print("Please load a program first.")
        return
    
    def getData(self):
        if not self.flags['read']:
            self._readData()            
        return self.buffer_df
    
    def loadProgram(self, program='', params={}, channels=[0], **kwargs):
        program = program.upper()
        program_list = ['OCV', 'CA', 'CP', 'CALimit', 'PEIS', 'GEIS','JV_Scan', 'MPP', 'MPP_Tracking', 'MPP_Cycles']
        if program in program_list:
            program_class = getattr(base_programs, program)
        else:
            print(f'Select program from list: {program_list}')
            return
        self.program = program_class(self.inst, params, channels=channels, **kwargs)
        return
    
    def measure(self):
        self.program.run()
        self._readData()
        self.flags['measured'] = True
        self.plotNyquist()
        return
    
    # Program specific
    def plotNyquist(self):
        if self.flags['measured']:
            df = pd.DataFrame(self.program.data[0], columns=self.program.field_titles)
            df['Impedance magnitude']= df['abs( Voltage ) [V]']/df['abs( Current ) [A]']
            df = df[['Frequency [Hz]', 'Impedance magnitude', 'Impendance phase']].copy()
            df.columns = ['Frequency', 'Real', 'Imaginary']
            df.dropna(inplace=True)

            spectrum = ImpedanceSpectrum(df)
            spectrum.plotNyquist()
        return
    
    def reset(self):
        self.program = None
        self.flags['measured'] = False
        self.flags['read'] = False
        return
    
    def saveData(self, filename):
        self.program.save_data(filename)
        return
    
    def setParameters(self, params={}):
        return
    
# %%
device = BioLogic(address=IP_ADDRESS)

params = {
	'voltage': 0,
    'amplitude_voltage': 0.01,
    'initial_frequency': 200E3,
    'final_frequency': 100E-3,
    'frequency_number': 38,
    'duration': 120,
    'repeat': 2,
    'wait': 0.10
}

device.loadProgram('PEIS', params, channels=[0])
device.measure()
# %%
# params = {
# 	'time':1,
#     'voltage_interval':0.01
# }

# ocv = base_programs.OCV(bl, params, channels=[0])

# %%run program
# ocv.run()
# ocv.save_data()