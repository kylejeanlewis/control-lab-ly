# %% -*- coding: utf-8 -*-
"""
Easy BioLogic package documentation can be found at:
https://github.com/bicarlsen/easy-biologic

Created: Tue 2022/11/02 17:13:35
@author: Chang Jie

Notes / actionables:
-
"""
# Standard library imports
import nest_asyncio
import pandas as pd

# Third party imports
import easy_biologic as biologic_api # pip install easy-biologic
# import easy_biologic.base_programs as base_programs

# Local application imports
from .. import ElectricalMeasurer
from .programs import base_programs
print(f"Import: OK <{__name__}>")

# INITIALIZING
nest_asyncio.apply()

class Biologic(ElectricalMeasurer):
    """
    BioLogic class.
    
    Args:
        ip_address (str, optional): IP address of BioLogic device. Defaults to '192.109.209.128'.
    """
    def __init__(self, ip_address='192.109.209.128'):
        self.ip_address = ip_address
        self.inst = biologic_api.BiologicDevice(ip_address, populate_info=True)
        self.buffer_df = pd.DataFrame()
        self.data = None
        self.program = None
        self._flags = {
            'measured': False,
            'read': False
        }
        self._parameters = {}
        return
    
    def __delete__(self):
        self.inst.disconnect()
        return
    
    def _map_column_names(self):
        """
        Map column names of raw output
        """
        name_map = {
            "Impendance phase": "Impedance phase [rad]",
            "Impendance_ce phase": "Impedance_ce phase [rad]"
        }
        self.buffer_df.rename(columns=name_map, inplace=True)
        return
    
    def _read_data(self):
        """
        Read data output from Keithley, through the program object
        """
        try:
            self.buffer_df = pd.DataFrame(self.program.data[0], columns=self.program.field_titles)
            self._map_column_names()
            if len(self.program.data[0]):
                self._flags['read'] = True
            else:
                print("No data found.")
        except AttributeError:
            print("Please load a program first.")
        return
    
    def connect(self):
        """
        Make connection to device.
        """
        return self.inst.connect()
    
    def getData(self, datatype=None):
        """
        Read the data and cast into custom data type for extended functions.
        
        Args:
            datatype (class, optional): custom data type. Defaults to 'None'.
            
        Returns:
            pd.DataFrame: raw dataframe of measurement
        """
        if not self._flags['read']:
            self._read_data()
        if self._flags['read']:
            try:
                self.data = datatype(data=self.buffer_df, instrument='biologic_')
            except Exception as e:
                print(e)
        return self.buffer_df
    
    def loadProgram(self, program, params={}, channels=[0], **kwargs):
        """
        Load a program for device to run.
        
        Args:
            program (str, or class): String representation of class name [See base_programs.PROGRAM_LIST] or class object.
            params (dict, optional): Dictionary of parameters. Use help() to find out about program parameters. Defaults to {}.
            channels (list, optional): List of channels to assign program to. Defaults to [0].
            **kwargs: other keyword arguments to be passed to program.
        """
        if type(program) == str:
            if program in base_programs.PROGRAM_LIST:
                program_class = getattr(base_programs, program)
            else:
                print(f"Select program from list: {', '.join(base_programs.PROGRAM_LIST)}")
                return
        elif str(type(program)) == "<class 'abc.ABCMeta'>":
            program_class = program
        else:
            raise Exception('Please input a BioLogic program or a string representation.')
        self.program = program_class(self.inst, params, channels=channels, **kwargs)
        self._parameters = params
        return
    
    def measure(self, datatype=None, **kwargs):
        """
        Performs measurement and tries to plot the data.
        
        Args:
            datatype (class, optional): custom data type. Defaults to 'None'.
        """
        self.reset(keep_program=True)
        print("Measuring...")
        self.program.run()
        self.getData(datatype)
        if len(self.buffer_df):
            self._flags['measured'] = True
        self.plot()
        return
    
    def plot(self, plot_type=''):
        """
        Plot the measurement data.
        
        Args:
            plot_type (str, optional): perform the requested plot of the data. Defaults to ''.
        """
        if self._flags['measured'] and self._flags['read']:
            try:
                self.data.plot(plot_type)
            except AttributeError:
                print(self.buffer_df.head())
                print("Please use 'getData' method to load datatype before plotting.")
                print("Otherwise, retrieve the dataframe using the 'buffer_df' attribute.")
        return
    
    def recallParameters(self):
        """
        Recall the last used parameters.
        
        Returns:
            dict: keyword parameters 
        """
        return self._parameters
    
    def reset(self, keep_program=False):
        """
        Reset the program, data, and flags

        Args:
            keep_program (bool, optional): whether to keep the loaded program. Defaults to False.
        """
        self.buffer_df = pd.DataFrame()
        self.data = None
        if not keep_program:
            self.program = None
        self._flags['measured'] = False
        self._flags['read'] = False
        return
    
    def saveData(self, filename:str):
        """
        Save dataframe to csv file.
        
        Args:
            filename (str): filename to which data will be saved
        """
        if not self._flags['read']:
            self._read_data()
        if self._flags['read']:
            self.buffer_df.to_csv(filename)
        else:
            print('No data available to be saved.')
        return
