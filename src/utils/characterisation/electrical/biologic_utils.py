# %% -*- coding: utf-8 -*-
"""
Created on Fri 2022/06/18 09:00:00

@author: Chang Jie

Easy BioLogic package documentation can be found at:
https://github.com/bicarlsen/easy-biologic

Notes / actionables:
- add LSV function to BioLogic
"""
# Standard library imports
import math
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
    
    def _mapColumnNames(self):
        name_map = {
            "Impendance phase": "Impedance phase [rad]",
            "Impendance_ce phase": "Impedance_ce phase [rad]"
        }
        self.buffer_df.rename(columns=name_map, inplace=True)
        return
    
    def _readData(self):
        try:
            self.buffer_df = pd.DataFrame(self.program.data[0], columns=self.program.field_titles)
            self._mapColumnNames()
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
            df['Impedance magnitude [ohm]'] = df['abs( Voltage ) [V]'] / df['abs( Current ) [A]']
            
            polar = list(zip(df['Impedance magnitude [ohm]'].to_list(), df['Impedance phase [rad]'].to_list()))
            df['Real'] = [p[0]*math.cos(p[1]) for p in polar]
            df['Imaginary'] = [p[0]*math.sin(p[1]) for p in polar]
            
            df = df[['Frequency [Hz]', 'Real', 'Imaginary']].copy()
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
        self.buffer_df.to_csv(filename)
        # self.program.save_data(filename)
        return
    
    def setParameters(self, params={}):
        return
    
# %%
if __name__ == "__main__":
    df = pd.read_csv('examples/biologic_test3.csv', header=1)
    df['Impedance magnitude [ohm]'] = df['abs( Voltage ) [V]'] / df['abs( Current ) [A]']
    
    df = df[(abs(df['Impedance magnitude [ohm]']) < 5000)&(abs(df['Impedance phase [rad]']) < 3000)]
    
    polar = list(zip(df['Impedance magnitude [ohm]'].to_list(), df['Impedance phase [rad]'].to_list()))
    df['Real'] = [p[0]*math.cos(p[1]) for p in polar]
    df['Imaginary'] = [p[0]*math.sin(p[1]) for p in polar]
    
    df = df[['Frequency [Hz]', 'Real', 'Imaginary']].copy()
    df.columns = ['Frequency', 'Real', 'Imaginary']
    df.dropna(inplace=True)
    
    spectrum = ImpedanceSpectrum(df)
    spectrum.plotNyquist()
    # spectrum.fit()
    spectrum.fit()
    spectrum.getCircuitDiagram()
    spectrum.plotNyquist()
    pass

# %%
if __name__ == "__main__":
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
if __name__ == "__main__":
    params = {
        'time': 1,
        'voltage_interval': 0.01
    }

    device.loadProgram('OCV', params, channels=[0])
    device.measure()