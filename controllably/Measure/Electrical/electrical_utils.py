# %% -*- coding: utf-8 -*-
"""
Created: Tue 2022/11/02 17:13:35
@author: Chang Jie

Notes / actionables:
- add multi channel support
"""
# Standard library imports
import pandas as pd
from typing import Protocol

# Local application imports
from ..measure_utils import Measurer
print(f"Import: OK <{__name__}>")

class Data(Protocol):
    def plot(self, *args, **kwargs):
        ...

class Program(Protocol):
    data_df: pd.DataFrame
    def getDetails(self, *args, **kwargs):
        ...
    def run(self, *args, **kwargs):
        ...

class Electrical(Measurer):
    """
    Electrical measurer class.
    """
    model = ''
    available_programs = []
    possible_inputs = []
    def __init__(self, **kwargs):
        self.name = kwargs.get('name', 'def')
        self.device = None
        
        self.buffer_df = pd.DataFrame()
        self.data = None
        self.datatype = None
        self.program = None
        self.program_type = None
        self.program_details = {
            'inputs_and_defaults': {},
            'short_doc': '',
            'tooltip': ''
        }
        self._last_used_parameters = {}
        self._measure_method_docstring = self.measure.__doc__
        
        self.verbose = False
        self._flags = {
            'busy': False,
            'measured': False,
            'read': False,
            'stop_measure': False
        }
        self._connect(**kwargs)
        return
    
    def __delete__(self):
        self._shutdown()
        return
    
    def _connect(self, **kwargs):
        """
        Connect to device
            
        Returns:
            any: device object
        """
        return self.device
    
    def _extract_data(self):
        """
        Extract data output from device, through the program object
        
        Returns:
            bool: whether the data extraction from program is successful
        """
        if self.program is None:
            print("Please load a program first.")
            return False
        self.buffer_df = self.program.data_df
        if len(self.buffer_df) == 0:
            print("No data found.")
            return False
        self.setFlag('read', True)
        return True
    
    def _get_program_details(self):
        """
        Get the input fields and defaults

        Raises:
            Exception: Load a program first
        """
        if self.program_type is None:
            raise Exception('Load a program first.')
        self.program_details = self.program_type.getDetails(verbose=self.verbose)
        return
        
    def _shutdown(self):
        """
        Close connection and shutdown
        """
        return
    
    def clearCache(self):
        """
        Reset data and flags
        """
        self.buffer_df = pd.DataFrame()
        self.data = None
        self.program = None
        self.setFlag('measured', False)
        self.setFlag('read', False)
        self.setFlag('stop_measure', False)
        return
    
    def connect(self):
        """
        Make connection to device.
        """
        return self._connect()
    
    def getData(self):
        """
        Read the data and cast into custom data type for extended functions.
            
        Returns:
            pd.DataFrame: raw dataframe of measurement
        """
        if not self._flags['read']:
            self._extract_data()
        if not self._flags['read']:
            print("Unable to read data.")
            return self.buffer_df
        if self.datatype is not None:
            self.data = self.datatype(data=self.buffer_df, instrument=self.model)
        return self.buffer_df
    
    def isBusy(self):
        """
        Checks whether the device is busy
        
        Returns:
            bool: whether the device is busy
        """
        return self._flags['busy']
    
    def isConnected(self):
        """
        Check whether device is connected

        Returns:
            bool: whether device is connected
        """
        if self.device is None:
            return False
        return True
    
    def loadDataType(self, datatype:Data):
        """
        Load a custom datatype to analyse and plot data

        Args:
            datatype (Callable): custom datatype to load
        """
        self.datatype = datatype
        print(f"Loaded datatype: {self.datatype.__name__}")
        return
    
    def loadProgram(self, program_type:Program):
        """
        Load a program for device to run and its parameters

        Args:
            program_type (Callable): program to load
        """
        self.program_type = program_type
        print(f"Loaded program: {self.program_type.__name__}")
        self._get_program_details()
        self.measure.__func__.__doc__ = self._measure_method_docstring + self.program_details['short_doc']
        return
    
    def measure(self, parameters={}, channels=[0], **kwargs):
        """
        Performs measurement and tries to plot the data

        Args:
            parameters (dict, optional): dictionary of parameters. Use help() to find out about program parameters. Defaults to {}.
            channels (list, optional): list of channels to assign the program to. Defaults to [0].
            
        Raises:
            Exception: Load a program first
        """
        if self.program_type is None:
            raise Exception('Load a program first.')
        self.setFlag('busy', True)
        print("Measuring...")
        self.clearCache()
        self.program = self.program_type(self.device, parameters, channels=channels, **kwargs)
        self._last_used_parameters = parameters
        
        # Run test
        self.program.run()
        self.setFlag('measured', True)
        self.getData()
        self.plot()
        self.setFlag('busy', False)
        return
    
    def plot(self, plot_type=None):
        """
        Plot the measurement data
        
        Args:
            plot_type (str, optional): perform the requested plot of the data. Defaults to None.
        """
        if self._flags['measured'] and self._flags['read']:
            if self.data is not None:
                self.data.plot(plot_type)
                return True
            print(self.buffer_df.head())
            print(f'{len(self.buffer_df)} row(s) of data')
        return False
    
    def recallParameters(self):
        """
        Recall the last used parameters.
        
        Returns:
            dict: keyword parameters 
        """
        return self._last_used_parameters
    
    def reset(self):
        """
        Reset the program, data, and flags
        """
        self.buffer_df = pd.DataFrame()
        self.data = None
        self.program = None
        self.datatype = None
        self.program_type = None
        self.measure.__func__.__doc__ = self._measure_method_docstring
        
        self.verbose = False
        self._flags = {
            'busy': False,
            'measured': False,
            'read': False,
            'stop_measure': False
        }
        return
    
    def saveData(self, filepath:str):
        """
        Save dataframe to csv file.
        
        Args:
            filepath (str): filepath to which data will be saved
        """
        if not self._flags['read']:
            self.getData()
        if len(self.buffer_df):
            self.buffer_df.to_csv(filepath)
        else:
            print('No data available to be saved.')
        return
    
    def setFlag(self, name:str, value:bool):
        """
        Set a flag truth value

        Args:
            name (str): label
            value (bool): flag value
        """
        self._flags[name] = value
        return
