# %% -*- coding: utf-8 -*-
"""
Easy BioLogic package documentation can be found at:
https://github.com/bicarlsen/easy-biologic

Created: Tue 2022/11/02 17:13:35
@author: Chang Jie

Notes / actionables:
- add LSV function to BioLogic
"""
# Standard library imports
import nest_asyncio
import pandas as pd

# Third party imports
import easy_biologic as biologic_api # pip install easy-biologic
import easy_biologic.base_programs as base_programs

# Local application imports
from ....Analyse.Data.Types.eis_datatype import ImpedanceSpectrum
from .. import ElectricalMeasurer
print(f"Import: OK <{__name__}>")

# INITIALIZING
nest_asyncio.apply()

class BioLogic(ElectricalMeasurer):
    def __init__(self, ip_address='192.109.209.128'):
        self.ip_address = ip_address
        self.inst = biologic_api.BiologicDevice(ip_address, populate_info=True)
        self.buffer_df = pd.DataFrame()
        self.data = None
        self.program = None
        self.flags = {
            'measured': False,
            'read': False
        }
        
        self._parameters = {}
        return
    
    def _map_column_names(self):
        name_map = {
            "Impendance phase": "Impedance phase [rad]",
            "Impendance_ce phase": "Impedance_ce phase [rad]"
        }
        self.buffer_df.rename(columns=name_map, inplace=True)
        return
    
    def _read_data(self):
        try:
            self.buffer_df = pd.DataFrame(self.program.data[0], columns=self.program.field_titles)
            self._map_column_names()
            if len(self.program.data[0]):
                self.flags['read'] = True
            else:
                print("No data found.")
        except AttributeError:
            print("Please load a program first.")
        return
    
    def connect(self):
        return self.inst.connect()
    
    def getData(self, datatype=None):
        if not self.flags['read']:
            self._read_data()
        if self.flags['read']:
            try:
                self.data = datatype(data=self.buffer_df, instrument='biologic_')
            except Exception as e:
                print(e)
        return self.buffer_df
    
    def loadProgram(self, program='', params={}, channels=[0], **kwargs):
        program_list = ['OCV', 'CA', 'CP', 'CALimit', 'PEIS', 'GEIS','JV_Scan', 'MPP', 'MPP_Tracking', 'MPP_Cycles']
        if program in program_list:
            program_class = getattr(base_programs, program)
        else:
            print(f"Select program from list: {', '.join(program_list)}")
            return
        self.program = program_class(self.inst, params, channels=channels, **kwargs)
        self._parameters = params
        return
    
    def measure(self, datatype):
        self.program.run()
        self.getData(datatype)
        if len(self.buffer_df):
            self.flags['measured'] = True
        self.plot()
        return
    
    def plot(self, plot_type=''):
        if self.flags['measured'] and self.flags['read']:
            self.data.plot(plot_type)
        return
    
    def recallParameters(self):
        return self._parameters
    
    def reset(self):
        self.buffer_df = pd.DataFrame()
        self.data = None
        self.program = None
        self.flags['measured'] = False
        self.flags['read'] = False
        return
    
    def saveData(self, filename):
        if not self.flags['read']:
            self._read_data()
        if self.flags['read']:
            self.buffer_df.to_csv(filename)
        return
