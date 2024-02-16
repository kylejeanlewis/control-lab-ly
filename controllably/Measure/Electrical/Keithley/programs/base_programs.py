# %% -*- coding: utf-8 -*-
"""
This module holds the program class for tools from Keithley.

Classes:
    IV_Scan (Program)
    LSV (Program)
    OCV (Program)
    Scan_Channels (Program)
"""
# Standard library imports
import csv
import pandas as pd
import time
from typing import Optional, Protocol

# Local application imports
from ....program_utils import Program
from ..keithley_lib import SenseDetails, SourceDetails
print(f"Import: OK <{__name__}>")

class Device(Protocol):
    sense: SenseDetails
    source: SourceDetails
    def beep(self, *args, **kwargs):
        ...
    def configureSense(self, *args, **kwargs):
        ...
    def configureSource(self, *args, **kwargs):
        ...
    def getErrors(self, *args, **kwargs):
        ...
    def makeBuffer(self, *args, **kwargs):
        ...
    def read(self, *args, **kwargs):
        ...
    def reset(self, *args, **kwargs):
        ...
    def run(self, *args, **kwargs):
        ...
    def sendCommands(self, *args, **kwargs):
        ...
    def setSource(self, *args, **kwargs):
        ...
    def toggleOutput(self, *args, **kwargs):
        ...

class IV_Scan(Program):
    """
    I-V Scan program

    ### Constructor
    Args:
        `device` (Device): device object
        `parameters` (Optional[dict], optional): dictionary of kwargs. Defaults to None.
        `verbose` (bool, optional): verbosity of class. Defaults to False.

    ### Attributes
    - `data_df` (pd.DataFrame): data collected from device when running the program
    - `device` (Device): device object
    - `parameters` (dict[str, ...]): parameters
    - `verbose` (bool): verbosity of class
    
    ### Methods
    - `run`: run the measurement program
    
    ==========
    
    ### Parameters:
        count (int, optional): number of readings to take and average over. Defaults to 1.
        currents (iterable): current values to measure. Defaults to (0,).
    """
    
    def __init__(self, 
        device: Device, 
        parameters: Optional[dict] = None,
        verbose: bool = False, 
        **kwargs
    ):
        """
        Instantiate the class

        Args:
            device (Device): device object
            parameters (Optional[dict], optional): dictionary of kwargs. Defaults to None.
            verbose (bool, optional): verbosity of class. Defaults to False.
        """
        super().__init__(device=device, parameters=parameters, verbose=verbose, **kwargs)
        return
    
    def run(self):
        """Run the measurement program"""
        device = self.device
        count = self.parameters.get('count', 1)
        
        device.reset()
        device.sendCommands(['ROUTe:TERMinals FRONT'])
        device.configureSource('current', measure_limit=200)
        device.configureSense('voltage', limit=200, four_point=True, count=count)
        device.makeBuffer()
        device.beep()
        
        for current in self.parameters.get('currents', (0,)):
            device.setSource(value=current)
            device.toggleOutput(on=True)
            device.run()
            time.sleep(0.1*count)
        time.sleep(1)
        self.data_df = device.readAll()
        device.beep()
        device.getErrors()
        return


class OCV(Program):
    """
    Open Circuit Voltage program

    ### Constructor
    Args:
        `device` (Device): device object
        `parameters` (Optional[dict], optional): dictionary of kwargs. Defaults to None.
        `verbose` (bool, optional): verbosity of class. Defaults to False.

    ### Attributes
    - `data_df` (pd.DataFrame): data collected from device when running the program
    - `device` (Device): device object
    - `parameters` (dict[str, ...]): parameters
    - `verbose` (bool): verbosity of class
    
    ### Methods
    - `run`: run the measurement program
    
    ==========
    
    ### Parameters:
        count (int, optional): number of readings to take and average over. Defaults to 1.
    """
    
    def __init__(self, 
        device: Device, 
        parameters: Optional[dict] = None,
        verbose: bool = False, 
        **kwargs
    ):
        """
        Instantiate the class

        Args:
            device (Device): device object
            parameters (Optional[dict], optional): dictionary of kwargs. Defaults to None.
            verbose (bool, optional): verbosity of class. Defaults to False.
        """
        super().__init__(device=device, parameters=parameters, verbose=verbose, **kwargs)
        return
    
    def run(self):
        """Run the measurement program"""
        device = self.device
        count = self.parameters.get('count', 1)
        
        device.reset()
        device.sendCommands(['ROUTe:TERMinals FRONt', 'OUTPut:SMODe HIMPedance'])
        device.configureSource('current', limit=1, measure_limit=20)
        device.configureSense('voltage', 20, count=count)
        device.makeBuffer()
        device.beep()
        
        device.setSource(value=0)
        device.toggleOutput(on=True)
        device.run()
        time.sleep(0.1*count)
        self.data_df = device.readAll()
        device.beep()
        device.getErrors()
        return


class LSV(Program):
    """
    Linear Sweep Voltammetry Scan program

    ### Constructor
    Args:
        `device` (Device): device object
        `parameters` (Optional[dict], optional): dictionary of kwargs. Defaults to None.
        `verbose` (bool, optional): verbosity of class. Defaults to False.
    
    ### Attributes
    - `data_df` (pd.DataFrame): data collected from device when running the program
    - `device` (Device): device object
    - `parameters` (dict[str, ...]): parameters
    - `verbose` (bool): verbosity of class
    
    ### Methods
    - `run`: run the measurement program
    
    ==========
    
    ### Parameters:
        lower (float): voltage below OCV. Defaults to 0.5.
        upper (float): voltage above OCV. Defaults to 0.5.
        bidirectional (bool): whether to sweep both directions. Defaults to True.
        mode (str): whether to use linear 'lin' or logarithmic 'log' mode. Defaults to 'lin'.
        step (float): voltage step. Defaults to 0.05.
        sweep_rate (float): voltage per seconds V/s. Defaults to 0.1.
        dwell_time (float): dwell time at each voltage. Defaults to 0.1.
        points (int): number of points. Defaults to 15.
    """
    
    def __init__(self, 
        device: Device, 
        parameters: Optional[dict] = None,
        verbose: bool = False, 
        **kwargs
    ):
        """
        Instantiate the class

        Args:
            device (Device): device object
            parameters (Optional[dict], optional): dictionary of kwargs. Defaults to None.
            verbose (bool, optional): verbosity of class. Defaults to False.
        """
        super().__init__(device=device, parameters=parameters, verbose=verbose, **kwargs)
        return
    
    def run(self):
        """Run the measurement program"""
        device= self.device
        # Get OCV
        ocv = self.runOCV()
        
        # Perform linear voltage sweep
        lower = self.parameters.get('lower', 0.5)
        upper = self.parameters.get('upper', 0.5)
        bidirectional = self.parameters.get('bidirectional', True)
        mode = self.parameters.get('mode', 'lin').lower()
        start = round(ocv - lower, 3)
        stop = round(ocv + upper, 3)
        
        if mode in ['lin', 'linear']:
            mode = 'lin'
            step = self.parameters.get('step', 0.05)
            sweep_rate = self.parameters.get('sweep_rate', 0.1)
            points = int( ((stop - start) / step) + 1 )
            dwell_time = step / sweep_rate
        elif mode in ['log', 'logarithmic']:
            mode = 'log'
            points = self.parameters.get('points', 15)
            dwell_time = self.parameters.get('dwell_time', 0.1)
        else:
            raise Exception("Please select one of 'lin' or 'log'")
        
        
        voltages = ",".join(str(v) for v in (start,stop,points))
        num_points = 2 * points - 1 if bidirectional else points
        wait = num_points * dwell_time * 2
        print(f'Expected measurement time: {wait}s')

        self.runSweep(voltages=voltages, dwell_time=dwell_time, mode=mode, bidirectional=bidirectional)
        time.sleep(wait+3)
        self.data_df = device.readAll()
        device.beep()
        device.getErrors()
        return
    
    def runOCV(self) -> float:
        """
        Run OCV program

        Returns:
            float: open circuit voltage
        """
        subprogram = OCV(self.device, dict(count=3))
        subprogram.run()
        df: pd.DataFrame = subprogram.data_df
        ocv = round(df.at[0, 'READing'], 3)
        print(f'OCV = {ocv}V')
        return ocv
    
    def runSweep(self, 
        voltages: str, 
        dwell_time: float, 
        mode: str = 'lin', 
        bidirectional: bool = True, 
        repeat: int = 1
    ):
        """
        Run linear voltage sweep

        Args:
            voltages (str): start,stop,points for voltages
            dwell_time (float): dwell time at each voltage in seconds
            mode (str, optional): linear or logarithmic interpolation of points. Defaults to 'lin'.
            bidirectional (bool, optional): whether to sweep in both directions. Defaults to True.
            repeat (int, optional): how many times to repeat the sweep. Defaults to 1.
        """
        device: Device = self.device
        bidirectional = 'ON' if bidirectional else 'OFF'
        if mode not in ['lin', 'log']:
            raise Exception("Please select one of 'lin' or 'log'")
        else:
            mode = 'LINear' if mode == 'lin' else 'LOG'
        
        device.reset()
        device.sendCommands(['ROUTe:TERMinals FRONt', 'OUTPut:SMODe HIMPedance'])
        device.configureSource('voltage', limit=20, measure_limit=1)
        device.configureSense('current', limit=None, probe_4_point=False, count=3)
        # device.makeBuffer()
        device.beep()
        
        parameters = [voltages, str(dwell_time), str(repeat), 'AUTO', 'OFF', bidirectional]
        device.sendCommands(
            [f'SOURce:SWEep:{device.source.function_type}:{mode} {",".join(parameters)}']
        )
        device.run(sequential_commands=False)
        return


class Scan_Channels(Program):
    """
    Channel scanning program (Only for Keithley DAQ6510 model)

    ### Constructor
    Args:
        `device` (Device): device object
        `parameters` (Optional[dict], optional): dictionary of kwargs. Defaults to None.
        `verbose` (bool, optional): verbosity of class. Defaults to False.

    ### Attributes
    - `data_df` (pd.DataFrame): data collected from device when running the program
    - `device` (Device): device object
    - `parameters` (dict[str, ...]): parameters
    - `verbose` (bool): verbosity of class
    
    ### Methods
    - `run`: run the measurement program
    
    ==========
    
    ### Parameters:
        channel_count (int, optional): number of channels to scan. Defaults to 4.
        scan_count (int, optional): number of iterations to scan. Defaults to 100.
        scan_interval (float, optional): time interval in seconds between each reading. Defaults to 0.1.
        fields (Iterable[str], optional): Defaults to ('READing', 'CHANnel', 'RELative'). 
        volt_range (float, optional): voltage measurement range. Defaults to 1.
        display_off (bool, optional): whether to turn the instrument display off during scanning. Defaults to False.
        filename (Optional[str], optional): filename to save to. Defaults to None.
    """
    
    def __init__(self, 
        device: Device, 
        parameters: Optional[dict] = None,
        verbose: bool = False, 
        **kwargs
    ):
        """
        Instantiate the class

        Args:
            device (Device): device object
            parameters (Optional[dict], optional): dictionary of kwargs. Defaults to None.
            verbose (bool, optional): verbosity of class. Defaults to False.
        """
        super().__init__(device=device, parameters=parameters, verbose=verbose, **kwargs)
        return
    
    def run(self):
        """Run the measurement program"""
        device = self.device
        channel_count = self.parameters.get('channel_count', 4)
        scan_count = self.parameters.get('scan_count', 100)
        scan_interval = self.parameters.get('scan_interval', 0.1)
        fields = self.parameters.get('fields', ('READing', 'CHANnel', 'RELative')) 
        volt_range = self.parameters.get('volt_range', 1)
        display_off = self.parameters.get('display_off', False)
        filename = self.parameters.get('filename', None)
        
        device.reset()
        device.setDisplay(50)
        device.setScanCount(scan_count=scan_count)
        
        # Set-up
        cmd = """
            SENSe:FUNCtion 'VOLTage:DC'
            VOLTage:RANGe {volt_range}
            VOLTage:AVERage:STATe OFF
            DISPlay:VOLTage:DIGits 4
            VOLTage:NPLCycles 0.0005
            VOLTage:AZERo:STATe OFF
            CALCulate2:VOLTage:LIMit1:STATe OFF
            CALCulate2:VOLTage:LIMit2:STATe OFF
        """.format(volt_range=volt_range)
        channel_text = f'(@101:{100+channel_count})' if channel_count else ''
        commands = [f'{c.strip()}, {channel_text}' for c in cmd.split('\n') if c.strip()]
        device.sendCommands(commands)
        
        device.setScanInterval(scan_interval)
        device.clearBuffer()
        device.createScanList(channel_count=channel_count)
        
        # Calculate expected number of data points
        channel_count = int(device._query('ROUTe:SCAN:COUNt:STEP?'))
        read_count = scan_count * channel_count * len(fields)
        print(read_count)
        
        # Start scan
        if display_off:
            device.setDisplay(0)
        device._query('INITiate')
        
        # Open file if save to file
        if filename is not None:
            file = open(filename, 'w', newline='')
            writer = csv.writer(file)
            writer.writerow(fields)
        else:
            buffer = [tuple(fields)]
        
        # Scan loop
        count = 1
        start_time = time.perf_counter()
        while count < read_count:
            time.sleep(0.5)
            actual_readings = int(device._query('TRACe:ACTual?'))
            if count > actual_readings:
                break
            receive_buffer = device._query(f'TRACe:DATA? {count}, {actual_readings}, "defbuffer1", {", ".join(fields)}')
            data = receive_buffer.split(',')
            cols = [data[i::len(fields)] for i in range(len(fields))]
            count = actual_readings + 1
            if filename is not None:
                writer.writerows(list(zip(*cols)))
            else:
                buffer += list(zip(*cols))
        
        # with open(filename, 'w', newline='') as file:
        #     writer = csv.writer(file)
        #     writer.writerow(fields)
            
        #     # Scan loop
        #     count = 1
        #     start_time = time.perf_counter()
        #     while count < read_count:
        #         time.sleep(0.5)
        #         actual_readings = int(device._query('TRACe:ACTual?'))
        #         if count > actual_readings:
        #             break
        #         receive_buffer = device._query(f'TRACe:DATA? {count}, {actual_readings}, "defbuffer1", {", ".join(fields)}')
        #         data = receive_buffer.split(',')
        #         cols = [data[i::len(fields)] for i in range(len(fields))]
        #         writer.writerows(list(zip(*cols)))
        #         count = actual_readings + 1
        
        end_time = time.perf_counter()
        device.stop()
        device.setDisplay(50)
        
        # Close file if save to file
        if filename is not None:
            file.close()
            df = pd.read_csv(filename, header=0)
        else:
            header = buffer.pop(0)
            df = pd.DataFrame(buffer, columns=header)
        
        print(f"Elapsed time: {end_time-start_time}s")
        self.data_df = df
        device.beep()
        device.getErrors()
        return

# %%
