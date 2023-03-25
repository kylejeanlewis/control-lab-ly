# %% -*- coding: utf-8 -*-
"""
Created: Tue 2023/01/03 17:13:35
@author: Chang Jie

Notes / actionables:
-
"""
# Standard library imports
import pandas as pd
from typing import Protocol

# Local application imports
from ..mechanical_utils import Mechanical
from .piezorobotics_device import PiezoRoboticsDevice
from .programs import base_programs
print(f"Import: OK <{__name__}>")

class Data(Protocol):
    def plot(self, *args, **kwargs):
        ...

class Program(Protocol):
    data_df: pd.DataFrame
    def run(self, *args, **kwargs):
        ...
        
class PiezoRobotics(Mechanical):
    _default_flags = {
        'busy': False,
        'connected': False,
        'initialised': False,
        'measured': False,
        'read': False
    }
    """
    PiezoRobotics object

    Args:
        port (str): com port address to device
        channel (int, optional): assigned device serial number. Defaults to 1.
    """
    model = 'piezorobotics_'
    available_programs = base_programs.PROGRAM_NAMES
    possible_inputs = base_programs.INPUTS_SET
    def __init__(self, port:str, channel=1, **kwargs):
        super().__init__(**kwargs)
        self.channel = 1
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

        self.port = ''
        self._connect(port, channel)
        return
    
    def _connect(self, port:str, channel:int = 1):
        """
        Connect to device

        Args:
            port (str): com port address
            channel (int, optional): assigned device serial number. Defaults to 1.
            
        Returns:
            PiezoRoboticsDevice: PiezoRoboticsDevice object
        """
        self.port = port
        self.channel = channel
        self.device = PiezoRoboticsDevice(port=port, channel=channel)
        return self.device
    
    def _extract_data(self):
        """
        Extract data output from device.
        
        Returns:
            bool: whether the data extraction is successful
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

    def shutdown(self):
        """
        Close serial connection and shutdown
        """
        self.device.close()
        self.reset()
        return

    def clearCache(self, device_only=True):
        """
        Reset data and flags.

        Args:
            device_only (bool, optional): whether to only clear data from device. Defaults to True.
        """
        self.buffer_df = pd.DataFrame()
        self.data = None
        self.program = None
        self.setFlag('measured', False)
        self.setFlag('read', False)
        return
    
    def connect(self):
        """
        Reconnect to device using existing port and channel
        
        Returns:
            PiezoRoboticsDevice: PiezoRoboticsDevice object
        """
        return self._connect(self.port, self.channel)
    
    def getData(self):
        """
        Read the data and cast into custom data type for extended functions.
            
        Returns:
            pd.DataFrame: raw dataframe of measurement
        """
        if not self.flags['read']:
            self._extract_data()
        if not self.flags['read']:
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
        return self.flags['busy']
    
    def isConnected(self):
        """
        Check whether device is connected

        Returns:
            bool: whether device is connected
        """
        return self.flags['connected']
    
    def loadDataType(self, datatype:Data):
        """
        Load a custom datatype to analyse and plot data

        Args:
            datatype (Callable): custom datatype to load
        """
        self.datatype = datatype
        print(f"Loaded datatype: {self.datatype.__module__}")
        return

    def loadProgram(self, program_type:Program = base_programs.DMA):
        """
        Load a program for device to run and its parameters

        Args:
            program_type (Callable, optional): program to load. Defaults to DMA.
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
            try: 
                self.loadProgram()
            except Exception:
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
        if self.flags['measured'] and self.flags['read']:
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
        self.device.reset()
        self.buffer_df = pd.DataFrame()
        self.data = None
        self.program = None
        self.datatype = None
        self.program_type = None
        self.measure.__func__.__doc__ = self._measure_method_docstring
        
        self.verbose = False
        self.flags = {
            'busy': False,
            'connected': False,
            'initialised': False,
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
        if not self.flags['read']:
            self.getData()
        if len(self.buffer_df):
            self.buffer_df.to_csv(filepath)
        else:
            print('No data available to be saved.')
        return
       
    def stopClamp(self):
        """
        Stop clamp movement
        """
        return self.device.stopClamp()
    
    def toggleClamp(self, on=False):
        """
        Toggle between clamp and release state

        Args:
            on (bool, optional): whether to clamp down on sample. Defaults to False.
        """
        return self.device.toggleClamp(on=on)
