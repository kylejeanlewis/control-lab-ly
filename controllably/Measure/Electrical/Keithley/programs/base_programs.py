# -*- coding: utf-8 -*-
# Standard library imports

# Third-party imports
from pymeasure.instruments.keithley import Keithley2450

# Local application imports
from .... import Program


class KeithleyProgram(Program):
    """
    Base Program template

    ### Constructor:
        `instrument` (Measurer, optional): Measurer object. Defaults to None.
        `parameters` (dict, optional): dictionary of kwargs. Defaults to None.
        `verbose` (bool, optional): verbosity of class. Defaults to False.
        
    ### Attributes and properties:
        `data` (deque): data collected from device when running the program
        `instrument` (Measurer): Measurer object
        `parameters` (dict): dictionary of kwargs
        `verbose` (bool): verbosity of class
        `data_df` (pd.DataFrame): dataframe of data collected
        
    ### Methods:
        `getDataframe`: get dataframe of data collected
        `run`: measurement program to run
        `saveData`: save data to file

    ==========
    ### Parameters:
        count (int, optional): number of measurements to perform and average over. Defaults to 1.
    """

    def __init__(self, device: Keithley2450, **kwargs):
        super().__init__(device, **kwargs)
        self.device: Keithley2450 = device
        return

    def run(self):
        """
        Run the Keithley program.
        Override this method in subclasses to implement specific measurement logic.
        """
        self.device.reset()
        self.device.use_front_terminals()
        self.device.sour
        return

class OCV(Program):
    ...

class IVScan(Program):
    """
    Base class for IV scan programs.
    This class provides a template for implementing IV scan measurements.
    """

    def __init__(self, device: Keithley2450, **kwargs):
        super().__init__(device, **kwargs)
        self.device: Keithley2450 = device

    def run(self):
        """
        Run the IV scan measurement.
        Override this method in subclasses to implement specific measurement logic.
        """
        self.device.reset()
        self.device.use_front_terminals()
        self.device.wires = 2
        # Configure source
        
        # Configure sense
        self.device.apply_voltage()
        self.device.measure_current()
        
        self.device.source_voltage_range = 10.0
        self.device.compliance_current = 10e-3
        self.device.source_voltage = 0.0
        self.device.apply_voltage()
        self.device.measure_current()
        
        
        self.device.current_range = 10e-3
        self.device.current_nplc = 1.0
        
        return

class FourTerminalSensing(Program):
    """
    Base class for four-terminal sensing programs.
    This class provides a template for implementing four-terminal sensing measurements.
    """

    def __init__(self, device: Keithley2450, **kwargs):
        super().__init__(device, **kwargs)
        self.device: Keithley2450 = device

    def run(self):
        """
        Run the four-terminal sensing measurement.
        Override this method in subclasses to implement specific measurement logic.
        """
        self.device.reset()
        self.device.use_front_terminals()
        self.device.wires = 4
        # Configure source
        
        # Configure sense
        self.device.apply_current()
        self.device.measure_voltage()
        
        self.device.source_current_range = 10e-3
        self.device.compliance_voltage = 10.0
        self.device.source_current = 0.0
        
        
        self.device.voltage_range = 10.0
        self.device.voltage_nplc = 1.0
        
        return
    