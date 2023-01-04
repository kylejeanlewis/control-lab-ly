# %% -*- coding: utf-8 -*-
"""
Created: Tue 2022/11/02 17:13:35
@author: Chang Jie

Notes / actionables:
- validation on copper
"""
# Local application imports
from ..electrical_utils import Electrical
from .keithley_device import KeithleyDevice
from .programs import base_programs
print(f"Import: OK <{__name__}>")

BUFFER_SIZE = 100
NUM_READINGS = 3

class Keithley(Electrical):
    """
    Keithley class.
    
    Args:
        ip_address (str, optional): IP address of Keithley. Defaults to '192.168.1.125'.
        name (str, optional): nickname for Keithley. Defaults to 'def'.
    """
    model = 'keithley_'
    available_programs = base_programs.PROGRAM_LIST
    possible_inputs = base_programs.INPUTS_LIST
    def __init__(self, ip_address='192.168.1.125', name='def'):
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
            name (str): nickname for Keithley.
            
        Returns:
            KeithleyDevice: object representation
        """
        self._ip_address = ip_address
        self.device = KeithleyDevice(ip_address=ip_address, name=name)
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

        Returns:
            dict: dictionary of program details
        """
        if self.program_type is None:
            raise Exception('Load a program first.')
        doc = self.program_type.__doc__
        
        # Extract truncated docstring and parameter listing
        lines = doc.split('\n')
        start, end = 0,0
        for i,line in enumerate(lines):
            line = line.strip()
            if line.startswith('Args:'):
                start = i
            if line.startswith('==========') and start:
                end = i
                break
        short_lines = lines[:start-1] + lines[end:]
        short_doc = '\n'.join(short_lines)
        tooltip = '\n'.join(['Parameters:'] + [f'- {_l.strip()}' for _l in lines[end+2:] if len(_l.strip())])
        print(short_doc)
        
        # Extract input fields and defaults
        input_parameters = {}
        parameter_list = [_s.strip() for _s in doc.split('Parameters:')[-1].split('\n')]
        for parameter in parameter_list:
            if len(parameter) == 0:
                continue
            _input = parameter.split(' ')[0]
            _default = parameter.split(' ')[-1][:-1] if 'Defaults' in parameter else 0
            input_parameters[_input]= _default
        
        self.program_details = {
            'inputs_and_defaults': input_parameters,
            'short_doc': short_doc,
            'tooltip': tooltip
        }
        return
    
    def connect(self):
        """
        Establish connection to Keithley.

        Returns:
            KeithleyDevice: object representation
        """
        return self._connect(self.ip_address, self.name)
    
    def loadProgram(self, name=None, program_type=None, program_module=base_programs):
        """
        Load a program for device to run and its parameters

        Args:
            name (str, optional): name of program type in program_module. Defaults to None.
            program_type (any, optional): program to load. Defaults to None.
            program_module (module, optional): module containing relevant programs. Defaults to Keithley.programs.base_programs.

        Raises:
            Exception: Provide a module containing relevant programs
            Exception: Select a valid program name
            Exception: Input only one of 'name' or 'program_type'
        """
        return super().loadProgram(name=name, program_type=program_type, program_module=program_module)

    def reset(self):
        """
        Reset the Keithley and clear the program, data, and flags
        """
        self.device.reset()
        return super().reset()
