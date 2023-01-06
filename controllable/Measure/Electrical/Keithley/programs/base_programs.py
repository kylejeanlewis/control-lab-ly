# %% -*- coding: utf-8 -*-
"""
Created: Tue 2022/11/02 17:13:35
@author: Chang Jie

Notes / actionables:
-
"""
# Standard library imports
import pandas as pd
import time

# Local application imports
from ..keithley_device import KeithleyDevice
print(f"Import: OK <{__name__}>")

class Program(object):
    """
    Base Program template

    Args:
        device (KeithleyDevice): Keithley Device object
        parameters (dict, optional): dictionary of measurement parameters. Defaults to {}.
    
    ==========
    Parameters:
        None
    """
    details = {
        'inputs_and_defaults': {},
        'short_doc': '',
        'tooltip': ''
    }
    def __init__(self, device:KeithleyDevice, parameters={}, **kwargs):
        self.device = device
        self.parameters = parameters
        
        self.data_df = pd.DataFrame
        self._flags = {}
        return
    
    @classmethod
    def getDetails(cls, verbose=False):
        """
        Get the input fields and defaults
        
        Args:
            verbose: whether to print out truncated docstring. Defaults to False.

        Returns:
            dict: dictionary of program details
        """
        doc = cls.__doc__
        
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
        parameter_list = sorted([_l.strip() for _l in lines[end+2:] if len(_l.strip())])
        short_lines = lines[:start-1] + lines[end:]
        short_doc = '\n'.join(short_lines)
        tooltip = '\n'.join(['Parameters:'] + [f'- {_p}' for _p in parameter_list])
        if verbose:
            print(short_doc)
        
        # Extract input fields and defaults
        input_parameters = {}
        for parameter in parameter_list:
            if len(parameter) == 0:
                continue
            _input = parameter.split(' ')[0]
            _default = parameter.split(' ')[-1][:-1] if 'Defaults' in parameter else ''
            input_parameters[_input] = _default
        
        cls.details = {
            'inputs_and_defaults': input_parameters,
            'short_doc': short_doc,
            'tooltip': tooltip
        }
        return cls.details
    
    def run(self):
        """
        Run the measurement program
        """
        return


class IV_Scan(Program):
    """
    I-V Scan program

    Args:
        device (KeithleyDevice): Keithley Device object
        parameters (dict, optional): dictionary of measurement parameters. Defaults to {}.
    
    ==========
    Parameters:
        count (int, optional): number of readings to take and average over. Defaults to 1.
        currents (iterable): current values to measure. Defaults to 0,.
    """
    def __init__(self, device:KeithleyDevice, parameters={}, **kwargs):
        super().__init__(device, parameters, **kwargs)
        return
    
    def run(self):
        """
        Run the measurement program
        """
        device = self.device
        count = self.parameters.get('count', 1)
        
        device.reset()
        device.configure(['ROUTe:TERMinals FRONT'])
        device.configureSource('current', measure_limit=200)
        device.configureSense('voltage', 200, True, count=count)
        device.makeBuffer()
        device.beep()
        
        for current in self.parameters.get('currents', []):
            device.setSource(value=current)
            device.toggleOutput(on=True)
            device.start()
            time.sleep(0.1*count)
        time.sleep(1)
        self.data_df = device.readAll()
        device.beep()
        device.getErrors()
        return


class OCV(Program):
    """
    Open Circuit Voltage program

    Args:
        device (KeithleyDevice): Keithley Device object
        parameters (dict, optional): dictionary of measurement parameters. Defaults to {}.
    
    ==========
    Parameters:
        count (int, optional): number of readings to take and average over. Defaults to 1.
    """
    def __init__(self, device:KeithleyDevice, parameters={}, **kwargs):
        super().__init__(device, parameters, **kwargs)
        return
    
    def run(self):
        """
        Run the measurement program
        """
        device = self.device
        count = self.parameters.get('count', 1)
        
        device.reset()
        device.configure(['ROUTe:TERMinals FRONt', 'OUTPut:SMODe HIMPedance'])
        device.configureSource('current', limit=1, measure_limit=20)
        device.configureSense('voltage', 20, count=count)
        device.makeBuffer()
        device.beep()
        
        device.setSource(value=0)
        device.toggleOutput(on=True)
        device.start()
        time.sleep(0.1*count)
        self.data_df = device.readAll()
        device.beep()
        device.getErrors()
        return


class LSV(Program):
    """
    Linear Sweep Voltammetry program

    Args:
        device (KeithleyDevice): Keithley Device object
        parameters (dict, optional): dictionary of measurement parameters. Defaults to {}.
    
    ==========
    Parameters:
        None
    """
    def __init__(self, device: KeithleyDevice, parameters={}, **kwargs):
        super().__init__(device, parameters, **kwargs)
        return
    
    def run(self):
        """
        Run the measurement program
        """
        device= self.device
        # Get OCV
        ocv = self.runOCV()
        
        # Perform linear voltage sweep
        lower = self.parameters.get('lower', 0.5)
        upper = self.parameters.get('upper', 0.5)
        bidirectional = self.parameters.get('bidirectional', True)
        
        mode = self.parameters.get('mode', 'lin').lower()
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
        
        start = round(ocv - lower, 3)
        stop = round(ocv + upper, 3)
        voltages = ",".join(str(v) for v in (start,stop,points))
        num_points = 2 * points - 1 if bidirectional else points
        wait = num_points * dwell_time
        print(f'Expected measurement time: {wait}s')

        self.runSweep(voltages, dwell_time, bidirectional)
        time.sleep(wait+3)
        self.data_df = device.readAll()
        device.beep()
        device.getErrors()
        return
    
    def runOCV(self):
        """
        Run OCV program

        Returns:
            float: open circuit voltage
        """
        subprogram = OCV(self.device, dict(count=3))
        subprogram.run()
        df = subprogram.data_df
        ocv = round(df.at[0, 'READing'], 3)
        print(f'OCV = {ocv}V')
        return ocv
    
    def runSweep(self, voltages:str, dwell_time:float, mode:str = 'lin', bidirectional:bool = True, repeat:int = 1):
        """
        Run linear voltage sweep

        Args:
            voltages (str): start,stop,points for voltages
            dwell_time (float): dwell time at each voltage in seconds
            mode (str, optional): linear or logarithmic interpolation of points. Defaults to 'lin'.
            bidirectional (bool, optional): whether to sweep in both directions. Defaults to True.
            repeat (int, optional): how many times to repeat the sweep. Defaults to 1.
        """
        device = self.device
        bidirectional = 'ON' if bidirectional else 'OFF'
        if mode not in ['lin', 'log']:
            raise Exception("Please select one of 'lin' or 'log'")
        else:
            mode = 'LINear' if mode is 'lin' else 'LOG'
        
        device.reset()
        device.configure(['ROUTe:TERMinals FRONt', 'OUTPut:SMODe HIMPedance'])
        device.configureSource('voltage', limit=20, measure_limit=1)
        device.configureSense('current', limit=None, probe_4_point=False, count=3)
        # device.makeBuffer()
        device.beep()
        
        parameters = [voltages, dwell_time, repeat, 'AUTO', 'OFF', bidirectional]
        device.configure(
            [f'SOURce:SWEep:{device.source}:{mode} {",".join(parameters)}']
        )
        device.start(sequential_commands=False)
        return


PROGRAMS = [IV_Scan, OCV, LSV]
PROGRAM_NAMES = [prog.__name__ for prog in PROGRAMS]
INPUTS = [item for item in [[key for key in prog.getDetails().get('inputs_and_defaults', {})] for prog in PROGRAMS]]
INPUTS_SET = sorted( list(set([item for sublist in INPUTS for item in sublist])) )

# """======================================================================================"""
# import pkgutil
# from .scpi_datatype import SCPI
# 
# MAX_BUFFER_SIZE = 10000
# PROGRAM_LIST = ['IV_Scan', 'Logging', 'LSV', 'OCV', 'SweepV']
#
# class Programme(object):
#     def __init__(self, device, params={}):
#         self.data_df = pd.DataFrame()
#         self.device = device
#         self.parameters = params
#         self.scpi = None
#         self.sub_program = {}
#         self.flags = {
#             'parameters_set': False,
#             'stop_measure': False,
#         }
        
#         self._program_template = None
#         pass
    
#     def loadSCPI(self, program, params={}):
#         if type(program) == str:
#             if program.endswith('.txt'):
#                 commands = pkgutil.get_data(__name__, program).decode('utf-8')
#             program = SCPI(commands)
#         elif 'SCPI' in str(type(program)):
#             pass
#         else:
#             print('Please input either filename or SCPI instruction string!')
#             return
        
#         if program.string.count('###') != 2:
#             raise Exception('Check SCPI input! Please use exact 2 "###" dividers to separate settings, inputs, and outputs.')
#         self._program_template = program
#         self.scpi = program
        
#         if len(params):
#             self.setParameters(params)
#         return
    
#     def plot(self):
#         print(self.data_df)
#         return
    
#     def run(self, field_titles=[], values=[], average=False, wait=0, fill_attributes=False):
#         # connect to device
#         self.device._write(['*RST'])
#         prompts = self.scpi.getPrompts()
#         self.device._write(prompts['settings'], fill_attributes)
        
#         if len(values):
#             for value in values:
#                 if self.flags['stop_measure']:
#                     break
#                 prompt = [l.format(value=value) for l in prompts['inputs']]
#                 self.device._write(prompt, fill_attributes)
#                 time.sleep(wait)
#                 df = self.device._read(prompts['outputs'], field_titles=field_titles, average=average)
#                 self.data_df = pd.concat([self.data_df, df], ignore_index=True)
#         else:
#             self.device._write(prompts['inputs'], fill_attributes)
#             time.sleep(wait)
#             self.data_df = self.device._read(prompts['outputs'], field_titles=field_titles, average=average, fill_attributes=fill_attributes)

#         self.device._write(['OUTP OFF'], fill_attributes)
#         # disconnect from device
#         return self.data_df
    
#     def setParameters(self, params={}):
#         if len(params) == 0:
#             raise Exception('Please input parameters.')
#         this_program = None
#         this_program = SCPI(self._program_template.replace(**params))
#         self.flags['parameters_set'] = True
#         self.scpi = this_program
#         self.parameters = params
#         return


# ### Single programs
# class Logging(Programme):
#     def __init__(self, device, params={}):
#         super().__init__(device, params)
#         self.field_title = ''
        
#     def plot(self):
#         return self.data_df.plot.line('t', self.field_title)

#     def run(self, field_title='value', average=False, timestep=1):
#         self.field_title = field_title
#         while not self.flags['stop_measure'] and len(self.data_df) < MAX_BUFFER_SIZE:
#             prompt = ['TRAC:TRIG "defbuffer1"', 'FETCH? "defbuffer1", READ, REL']
#             df = self.device._read(prompt, [field_title, 't'], average=average)
#             self.data_df = pd.concat([self.data_df, df], ignore_index=True)
#             time.sleep(timestep)
#         return self.data_df

# class SweepV(Programme):
#     def __init__(self, device, params={}):
#         super().__init__(device, params)
#         super().loadSCPI('SCPI_sweep_volt.txt')
#         return
    
#     def plot(self):
#         return self.data_df.plot.line('V', 'I')
    
#     def run(self, voltages, dwell_time, num_points, wait):
#         self.setParameters(dict(voltages=voltages, dwell_time=dwell_time, num_points=num_points))
#         return super().run(field_titles=['V', 'I', 't'], wait=wait)


# ### Compound programs
# class LSV(Programme):
#     def __init__(self, device, params={}):
#         super().__init__(device, params)
#         self.sub_program['OCV'] = OCV(device)
#         self.sub_program['sweep'] = SweepV(device)
#         return
    
#     def plot(self):
#         return self.sub_program['sweep'].plot()
    
#     def run(self, volt_range, sweep_rate=0.01, dual=True):
#         df = self.sub_program['OCV'].run()
#         potential = round(df.at[0,'V'], 3)
#         print(f'OCV = {potential}V')
        
#         below, above, step = volt_range
#         start = round(potential + below, 3)
#         stop = round(potential + above, 3)
#         points = int( ((stop - start) / step) + 1 )
#         num_points = 2 * points - 1 if dual else points

#         voltages = ", ".join(str(v) for v in (start,stop,points))
#         dwell_time = step / sweep_rate
#         wait = num_points * dwell_time * 2
#         print(time.time())
#         print(f'Expected measurement time: {wait}s')
        
#         self.data_df = self.sub_program['sweep'].run(voltages=voltages, dwell_time=dwell_time, num_points=num_points, wait=wait)
#         return

# %%
