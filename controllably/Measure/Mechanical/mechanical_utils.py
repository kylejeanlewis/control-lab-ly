# %% -*- coding: utf-8 -*-
"""

"""
# Local application imports
from ..measure_utils import Programmable
print(f"Import: OK <{__name__}>")

class Mechanical(Programmable):
    ...

# class Data(Protocol):
#     def plot(self, *args, **kwargs):
#         ...

# class Program(Protocol):
#     data_df: pd.DataFrame
#     def getDetails(self, *args, **kwargs):
#         ...
#     def run(self, *args, **kwargs):
#         ...

# class Mechanical(Measurer):
#     _default_datatype: Optional[Data] = None
#     _default_program: Optional[Program] = None
#     _default_flags = {
#         'busy': False,
#         'connected': False,
#         'measured': False,
#         'read': False,
#         'stop_measure': False
#     }
#     model = ''
#     available_programs: tuple[str] = ('',)      # FIXME
#     possible_inputs: tuple[str] = ('',)         # FIXME
#     def __init__(self, **kwargs):
#         super().__init__(**kwargs)
#         self.buffer_df = pd.DataFrame()
#         self.data: Optional[Data] = None
#         self.datatype: Optional[Data] = self._default_datatype
#         self.program: Optional[Program] = None
#         self.program_type: Optional[Program] = self._default_program
        
#         self.program_details = ProgramDetails()
#         self.recent_parameters = []
#         self._measure_method_docstring = self.measure.__doc__
#         return 
   
#     def clearCache(self):
#         """
#         Reset data and flags.

#         Args:
#             device_only (bool, optional): whether to only clear data from device. Defaults to True.
#         """
#         self.buffer_df = pd.DataFrame()
#         self.data = None
#         self.program = None
#         self.setFlag(measured=False, read=False, stop_measure=False)
#         return
    
#     def getData(self) -> pd.DataFrame:
#         """
#         Read the data and cast into custom data type for extended functions.
            
#         Returns:
#             pd.DataFrame: raw dataframe of measurement
#         """
#         if not self.flags['read']:
#             self._extract_data()
#         if not self.flags['read']:
#             print("Unable to read data.")
#             return self.buffer_df
        
#         if self.datatype is not None:
#             self.data = self.datatype(data=self.buffer_df, instrument=self.model)
#         return self.buffer_df
    
#     def loadDataType(self, datatype:Optional[Data] = None):
#         """
#         Load a custom datatype to analyse and plot data

#         Args:
#             datatype (Callable): custom datatype to load
#         """
#         self.datatype = self._default_datatype if datatype is None else datatype
#         print(f"Loaded datatype: {self.datatype.__name__}")
#         return

#     def loadProgram(self, program_type:Optional[Program] = None):
#         """
#         Load a program for device to run and its parameters

#         Args:
#             program_type (Callable, optional): program to load. Defaults to DMA.
#         """
#         self.program_type = self._default_program if program_type is None else program_type
#         print(f"Loaded program: {self.program_type.__name__}")
#         self._get_program_details()
#         self.measure.__func__.__doc__ = self._measure_method_docstring + self.program_details.short_doc
#         return

#     def measure(self, parameters: Optional[dict] = None, channel:Union[int, tuple[int]] = 0, **kwargs):
#         """
#         Performs measurement and tries to plot the data

#         Args:
#             parameters (dict, optional): dictionary of parameters. Use help() to find out about program parameters. Defaults to {}.
#             channels (list, optional): list of channels to assign the program to. Defaults to [0].
            
#         Raises:
#             Exception: Load a program first
#         """
#         if self.program_type is None:
#             self.loadProgram()
#         if self.program_type is None:
#             print('Load a program first.')
#             return
        
#         self.setFlag(busy=True)
#         print("Measuring...")
#         self.clearCache()
#         self.program = self.program_type(self.device, parameters, channels=channel, **kwargs)
#         self.recent_parameters.append(parameters)
        
#         # Run test
#         self.program.run()
#         self.setFlag(measured=True)
#         self.getData()
#         self.plot()
#         self.setFlag(busy=False)
#         return

#     def plot(self, plot_type:Optional[str] = None) -> bool:
#         """
#         Plot the measurement data
        
#         Args:
#             plot_type (str, optional): perform the requested plot of the data. Defaults to None.
#         """
#         if not self.flags['measured'] or not self.flags['read']:
#             return False
#         if self.data is None:
#             print(self.buffer_df.head())
#             print(f'{len(self.buffer_df)} row(s) of data')
#             return False
#         self.data.plot(plot_type=plot_type)
#         return True
    
#     def reset(self):
#         """
#         Reset the program, data, and flags
#         """
#         super().reset()
#         self.device.reset()
#         self.datatype = self._default_datatype
#         self.program_type = self._default_program
#         self.recent_parameters = []
#         self.measure.__func__.__doc__ = self._measure_method_docstring
#         return
    
#     # Protected method(s)
#     def _extract_data(self) -> bool:
#         """
#         Extract data output from device.
        
#         Returns:
#             bool: whether the data extraction is successful
#         """
#         if self.program is None:
#             print("Please load a program first.")
#             return False
#         self.buffer_df = self.program.data_df
#         if len(self.buffer_df) == 0:
#             print("No data found.")
#             return False
#         self.setFlag(read=True)
#         return True
    
#     def _get_program_details(self):
#         """
#         Get the input fields and defaults

#         Raises:
#             Exception: Load a program first
#         """
#         if self.program_type is None:
#             raise Exception('Load a program first.')
#         self.program_details: ProgramDetails = self.program_type.getDetails(verbose=self.verbose)
#         return
    