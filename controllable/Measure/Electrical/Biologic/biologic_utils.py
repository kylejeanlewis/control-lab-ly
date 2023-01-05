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
# import easy_biologic as biologic_api # pip install easy-biologic
# import easy_biologic.base_programs as base_programs
from easy_biologic.lib import ec_lib as ecl

# Local application imports
from ..electrical_utils import Electrical
from .biologic_api import BiologicDeviceLocal
from .programs import base_programs
print(f"Import: OK <{__name__}>")

# INITIALIZING
nest_asyncio.apply()

class Biologic(Electrical):
    """
    BioLogic class.
    
    Args:
        ip_address (str, optional): IP address of Biologic device. Defaults to '192.109.209.128'.
    """
    model = 'biologic_'
    available_programs = base_programs.PROGRAM_NAMES
    possible_inputs = base_programs.INPUTS_SET
    def __init__(self, ip_address='192.109.209.128', name='def'):
        self._ip_address = ''
        super().__init__(ip_address=ip_address, name=name)
        return
    
    @property
    def ip_address(self):
        return self._ip_address
        
    def _connect(self, ip_address:str, name:str):
        """
        Connect to device

        Args:
            ip_address (str): IP address of the Biologic device
            
        Returns:
            BiologicDevice: object representation from API
        """
        self._ip_address = ip_address
        # self.device = biologic_api.BiologicDevice(ip_address, populate_info=True)
        try:
            self.device = BiologicDeviceLocal(ip_address, populate_info=True)
        except ecl.EcError:
            print('Could not establish communication with instrument.')
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
        if len(self.buffer_df) == 0:
            print("No data found.")
            return False
        self.setFlag('read', True)
        return True
    
    def _fix_column_names(self):
        """
        Map column names of raw output, and fix mistakes in spelling
        """
        name_map = {
            "Impendance phase": "Impedance phase [rad]",
            "Impendance_ce phase": "Impedance_ce phase [rad]"
        }
        self.buffer_df.rename(columns=name_map, inplace=True)
        return
        
    def _shutdown(self):
        """
        Close connection and shutdown
        """
        self.device.disconnect()
        return
    
    def connect(self):
        """
        Make connection to device.
        """
        return self.device.connect()

    def loadProgram(self, name=None, program_type=None, program_module=base_programs):
        """
        Load a program for device to run and its parameters

        Args:
            name (str, optional): name of program type in program_module. Defaults to None.
            program_type (any, optional): program to load. Defaults to None.
            program_module (module, optional): module containing relevant programs. Defaults to Biologic.programs.base_programs.

        Raises:
            Exception: Provide a module containing relevant programs
            Exception: Select a valid program name
            Exception: Input only one of 'name' or 'program_type'
        """
        return super().loadProgram(name=name, program_type=program_type, program_module=program_module)
    