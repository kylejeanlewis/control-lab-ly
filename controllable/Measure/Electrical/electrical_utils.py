# %% -*- coding: utf-8 -*-
"""
Created: Tue 2022/11/02 17:13:35
@author: Chang Jie

Notes / actionables:
-
"""
# Standard library imports
import pandas as pd

# Local application imports
from ...Analyse.Data import Types
print(f"Import: OK <{__name__}>")

class Electrical(object):
    """
    Electrical measurer class.
    """
    model = ''
    def __init__(self, **kwargs):
        self.device = None
        
        self.buffer_df = pd.DataFrame()
        self.datatype = None
        self.program_type = None
        self._data = None
        self._program = None
        
        self.verbose = False
        self._flags = {
            'busy': False,
            'measured': False,
            'read': False
        }
        self._last_used_parameters = {}
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
        if self._program is None:
            print("Please load a program first.")
            return False
        self.buffer_df = pd.DataFrame(self._program.data[0], columns=self._program.field_titles)
        self._fix_column_names()
        if len(self._program.data[0]) == 0:
            print("No data found.")
            return False
        self.setFlag('read', True)
        return True
        
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
        self._data = None
        self._program = None
        self.setFlag('measured', False)
        self.setFlag('read', False)
        return
    
    def connect(self):
        """
        Make connection to device.
        """
        return self.device.connect()
    
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
            self._data = self.datatype(data=self.buffer_df, instrument=self.model)
        return self.buffer_df
    
    def isBusy(self):
        """
        Checks whether the Biologic is busy
        
        Returns:
            bool: whether the Biologic is busy
        """
        return self._flags['busy']
    
    def isConnected(self):
        """
        Check whether Biologic is connected

        Returns:
            bool: whether Biologic is connected
        """
        if self.device is None:
            return False
        return True
    
    def loadDataType(self, name=None, datatype=None):
        """
        Load a custom datatype to analyse and plot data

        Args:
            name (str, optional): name of custom datatype in Analyse.Data.Types submodule. Defaults to None.
            datatype (any, optional): custom datatype to load. Defaults to None.

        Raises:
            Exception: Select a valid custom datatype name
            Exception: Input only one of 'name' or 'datatype'
        """
        if name is None and datatype is not None:
            self.datatype = datatype
        elif name is not None and datatype is None:
            if name not in Types.TYPES_LIST:
                raise Exception(f"Please select a valid custom datatype from: {', '.join(Types.TYPES_LIST)}")
            datatype = getattr(Types, name)
            self.datatype = datatype
        else:
            raise Exception("Please input only one of 'name' or 'datatype'")
        print(f"Loaded datatype: {datatype.__class__}")
        return
    
    def loadProgram(self, name=None, program_type=None):
        """
        Load a program for device to run and its parameters

        Args:
            name (str, optional): name of program type in Biologic.programs.base_programs submodule. Defaults to None.
            program_type (any, optional): program to load. Defaults to None.

        Raises:
            Exception: Select a valid program name
            Exception: Input only one of 'name' or 'program_type'
        """
        if name is None and program_type is not None:
            self.program_type = program_type
        elif name is not None and program_type is None:
            if name not in Types.TYPES_LIST:
                raise Exception(f"Please select a program name from: {', '.join(['',''])}")
            # program_type = getattr(base_programs, name)
            self.program_type = program_type
        else:
            raise Exception("Please input only one of 'name' or 'program_type'")
        print(f"Loaded program: {program_type.__class__}")
        return
    
    def measure(self, params={}, channels=[0], **kwargs):
        """
        Performs measurement and tries to plot the data

        Args:
            params (dict, optional): dictionary of parameters. Use help() to find out about program parameters. Defaults to {}.
            channels (list, optional): list of channels to assign the program to. Defaults to [0].
        """
        self.setFlag('busy', True)
        print("Measuring...")
        self.clearCache()
        self._program = self.program_type(self.device, params, channels=channels, **kwargs)
        self._last_used_parameters = params
        self._program.run()
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
            if self._data is not None:
                self._data.plot(plot_type)
                return True
            print(self.buffer_df.head())
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
        self.datatype = None
        self.program_type = None
        self._data = None
        self._program = None
        
        self.verbose = False
        self._flags = {
            'busy': False,
            'measured': False,
            'read': False
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
