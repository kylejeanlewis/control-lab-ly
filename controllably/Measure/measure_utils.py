# %% -*- coding: utf-8 -*-
"""
This module holds the base class for measurement tools.

Classes:
    Measurer (ABC)
    Programmable (Measurer)
"""
# Standard library imports
from __future__ import annotations
from abc import ABC, abstractmethod
import logging
import pandas as pd
from typing import Callable, Protocol

# Local application imports
from .program_utils import ProgramDetails, get_program_details

_logger = logging.getLogger("controllably.Measure")
_logger.debug(f"Import: OK <{__name__}>")

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
logger.addHandler(handler)

class Data(Protocol):
    def plot(self, *args, **kwargs):
        ...

class Program(Protocol):
    data_df: pd.DataFrame
    def run(self, *args, **kwargs):
        ...

class Measurer(ABC):
    """
    Abstract Base Class (ABC) for Measurer objects (i.e. tools that perform characterisation tasks).
    ABC cannot be instantiated, and must be subclassed with abstract methods implemented before use.
    
    ### Constructor
    Args:
        `verbose` (bool, optional): verbosity of class. Defaults to False.
    
    ### Attributes
    - `buffer_df` (pd.DataFrame): buffer dataframe to store collected data
    - `connection_details` (dict): dictionary of connection details (e.g. COM port / IP address)
    - `device` (Callable): device object that communicates with physical tool
    - `flags` (dict[str, bool]): keywords paired with boolean flags
    
    ### Properties
    - `instrument` (Callable): Alias for `device`
    - `verbose` (bool): verbosity of class
    
    ### Methods
    #### Abstract
    - `clearCache`: clear most recent data and configurations
    - `disconnect`: disconnect from device
    - `_connect`: connection procedure for tool
    #### Public
    - `connect`: establish connection with device
    - `isBusy`: checks and returns whether the device is busy
    - `isConnected`: checks and returns whether the device is connected
    - `reset`: reset the device
    - `resetFlags`: reset all flags to class attribute `_default_flags`
    - `saveData`: save data in buffer into file
    - `setFlag`: set flags by using keyword arguments
    - `shutdown`: shutdown procedure for tool
    """
    
    _default_flags: dict[str, bool] = {'busy': False, 'connected': False}
    def __init__(self,
        verbose: bool = False,
        **kwargs
    ):
        """
        Instantiate the class

        Args:
            verbose (bool, optional): verbosity of class. Defaults to False.
        """
        self.buffer_df = pd.DataFrame()
        self.connection_details = {}
        self.device = None
        self.flags = self._default_flags.copy()
        self.verbose = verbose
        return
    
    def __del__(self):
        self.shutdown()
        return
    
    @abstractmethod
    def clearCache(self):
        """Clear most recent data and configurations"""
    
    @abstractmethod
    def disconnect(self):
        """Disconnect from device"""
    
    @abstractmethod
    def _connect(self, *args, **kwargs):
        """Connection procedure for tool"""
        self.connection_details = {}
        self.device = None
        self.setFlag(connected=True)
        return
    
    # Properties
    @property
    def instrument(self) -> Callable:
        return self.device
    @instrument.setter
    def instrument(self, device:Callable):
        self.device = device
        return
    
    @property
    def verbose(self) -> bool:
        return self._verbose
    @verbose.setter
    def verbose(self, value:bool):
        self._verbose = bool(value)
        try:
            self.device.verbose = self._verbose
        except AttributeError:
            pass
        return
    @verbose.deleter
    def verbose(self):
        del self._verbose
        return
    
    def connect(self):
        """Establish connection with device"""
        return self._connect(**self.connection_details)

    def isBusy(self) -> bool:
        """
        Checks and returns whether the device is busy
        
        Returns:
            bool: whether the device is busy
        """
        return self.flags.get('busy', False)
    
    def isConnected(self) -> bool:
        """
        Checks and returns whether the device is connected

        Returns:
            bool: whether the device is connected
        """
        if not self.flags.get('connected', False):
            logger.warning(f"{self.__class__} is not connected. Details: {self.connection_details}")
        return self.flags.get('connected', False)
    
    def reset(self):
        """Reset the device"""
        is_connected = self.flags.get('connected',False)
        self.resetFlags()
        self.clearCache()
        self.setFlag(connected=is_connected)
        return
    
    def resetFlags(self):
        """Reset all flags to class attribute `_default_flags`"""
        self.flags = self._default_flags.copy()
        return

    def saveData(self, filepath:str):
        """
        Save data in buffer into file
        
        Args:
            filepath (str): filepath to which data will be saved
        """
        if not self.flags['read']:
            self.getData()
        if len(self.buffer_df):
            self.buffer_df.to_csv(filepath)
        else:
            logger.warning('No data available to be saved.')
        return

    def setFlag(self, **kwargs):
        """
        Set flags by using keyword arguments

        Kwargs:
            key, value: (flag name, boolean) pairs
        """
        if not all([type(v)==bool for v in kwargs.values()]):
            raise ValueError("Ensure all assigned flag values are boolean.")
        self.flags.update(kwargs)
        # for key, value in kwargs.items():
        #     self.flags[key] = value
        return
    
    def shutdown(self):
        """Shutdown procedure for tool"""
        self.reset()
        self.disconnect()
        return


class Programmable(Measurer):
    """
    Abstract Base Class (ABC) for Programmable Measurer objects (i.e. tools that perform characterisation tasks).
    ABC cannot be instantiated, and must be subclassed with abstract methods implemented before use.
    
    ### Constructor
    Kwargs:
        key, value: (`Measurer` keyword argument, value) pairs
    
    ### Attributes
    #### Class
    - `model` (str): model name of class
    #### Instance
    - `data` (Data): instantiated Data class with data in buffer
    - `datatype` (Data): Data class
    - `program` (Program): instantiated Program class with parameters provided
    - `program_details` (ProgramDetails): program details such as inputs, defaults, and docstring
    - `program_type` (Program): Program class
    - `recent_parameters` (list[dict[str, ...]]): list of previously used parameters
    
    ### Properties
    - `instrument` (Callable): alias for `device`
    - `program_parser` (Callable): function to get the program details from the program class docstring
    
    ### Methods
    #### Abstract
    - `disconnect`: disconnect from device
    - `_connect`: connection procedure for tool
    #### Public
    - `clearCache`: clear most recent data and configurations
    - `getData`: retrieve data from device and store in buffer
    - `loadDataType`: load desired Data class
    - `loadProgram`: load desired Program class
    - `loadProgramParser`: load a program interpreter to get the program details from the program class docstring
    - `measure`: perform measurement using loaded Program and parameters provided
    - `plot`: present data visualisation using loaded DataType, using its `plot()` method
    - `reset`: reset the device
    """
    
    _default_datatype: Data|None = None
    _default_program: Program|None = None
    _default_program_parser: dict[str, function] = {"parser": get_program_details}
    _default_flags = {
        'busy': False,
        'connected': False,
        'measured': False,
        'read': False,
        'stop_measure': False
    }
    _place: str = '.'.join(__name__.split('.')[1:-1])
    model: str = ''
    def __init__(self, **kwargs):
        """Instantiate the class"""
        super().__init__(**kwargs)
        self.data: Data|None = None
        self.datatype: Data|None = self._default_datatype
        self.program: Program|None = None
        self._program_parser = self._default_program_parser
        self.program_type: Program|None = self._default_program
        
        self.program_details = ProgramDetails()
        self.recent_parameters = []
        self._measure_method_docstring = self.measure.__doc__
        return
    
    # Properties
    @property
    def program_parser(self) -> Callable:
        return self._program_parser.get('parser', lambda x:x)
    @program_parser.setter
    def program_parser(self, func: Callable):
        self._program_parser['parser'] = func
        return 
          
    def clearCache(self):
        """Clear most recent data and configurations """
        self.buffer_df = pd.DataFrame()
        self.data = None
        self.program = None
        self.setFlag(measured=False, read=False, stop_measure=False)
        return
   
    def getData(self) -> pd.DataFrame:
        """
        Retrieve data from device and store in buffer
            
        Returns:
            pd.DataFrame: raw dataframe of measurement
        """
        if not self.flags['read']:
            self._extract_data()
        if not self.flags['read']:
            logger.warning("Unable to read data.")
            return self.buffer_df
        
        if self.datatype is not None:
            self.data = self.datatype(data=self.buffer_df, instrument=self.model)
        return self.buffer_df

    def loadDataType(self, datatype:Data|None = None):
        """
        Load desired Data class

        Args:
            datatype (Data|None, optional): custom datatype to load. Defaults to None.
        """
        self.datatype = self._default_datatype if datatype is None else datatype
        logger.info(f"Loaded datatype: {self.datatype.__name__}")
        return
    
    def loadProgram(self, program_type:Program|None = None):
        """
        Load desired Program class

        Args:
            program_type (Program|None, optional): program type to load. Defaults to None.
        """
        self.program_type = self._default_program if program_type is None else program_type
        logger.info(f"Loaded program: {self.program_type.__name__}")
        self._get_program_details()
        logger.info(self.program_details.short_doc)
        self.measure.__func__.__doc__ = self._measure_method_docstring + self.program_details.short_doc
        return
    
    def loadProgramInterpreter(self, program_parser: function|None = None):
        """
        Load a program interpreter to get the program details from the program class docstring

        Args:
            program_parser (function|None, optional): function that interprets the program class docstring. Defaults to None.
        """
        self._program_parser = self._default_program_parser if program_parser is None else {"parser": program_parser}
        return
    
    def measure(self, parameters: dict|None = None, channel:int|tuple[int] = 0, **kwargs):
        """
        Perform measurement using loaded Program and parameters provided.
        Use `help()` to find out about program parameters.

        Args:
            parameters (dict|None, optional): dictionary of kwargs. Defaults to None.
            channels (int|tuple[int], optional): channel id(s). Defaults to 0.
        """
        parameters = {} if parameters is None else parameters
        parameters.update(kwargs)
        if self.program_type is None:
            self.loadProgram()
        if self.program_type is None:
            logger.warning('Load a program first.')
            return
        
        self.setFlag(busy=True)
        print("Measuring...")
        self.clearCache()
        self.program = self.program_type(self.device, parameters, channels=channel, **kwargs)
        self.recent_parameters.append(parameters)
        
        # Run test
        self.program.run()
        self.setFlag(measured=True)
        self.getData()
        self.plot()
        self.setFlag(busy=False)
        return
    
    def plot(self, plot_type:str|None = None) -> bool:
        """
        Present data visualisation using loaded DataType, using its `plot()` method
        
        Args:
            plot_type (str|None , optional): perform the requested plot of the data. Defaults to None.
        """
        if not self.flags['measured'] or not self.flags['read']:
            return False
        if self.data is None:
            print(self.buffer_df.head())
            logger.info(f'{len(self.buffer_df)} row(s) of data')
            return False
        self.data.plot(plot_type=plot_type)
        return True
    
    def reset(self):
        """Reset the device"""
        super().reset()
        # self.device.reset()
        self.datatype = self._default_datatype
        self.program_type = self._default_program
        self.recent_parameters = []
        self.measure.__func__.__doc__ = self._measure_method_docstring
        return
    
    # Protected method(s)
    def _extract_data(self) -> bool:
        """
        Extract data output from device
        
        Returns:
            bool: whether the data extraction is successful
        """
        if self.program is None:
            logger.warning("Please load a program first.")
            return False
        self.buffer_df = self.program.data_df
        if len(self.buffer_df) == 0:
            logger.warning("No data found.")
            return False
        self.setFlag(read=True)
        return True
    
    def _get_program_details(self) -> ProgramDetails:
        """
        Get the input fields and defaults

        Raises:
            Exception: Load a program first
            
        Returns:
            ProgramDetails: details of program class
        """
        if self.program_type is None:
            raise Exception('Load a program first.')
        details = self.program_parser(program_class=self.program_type, verbose=self.verbose)
        self.program_details: ProgramDetails = details
        return details
    