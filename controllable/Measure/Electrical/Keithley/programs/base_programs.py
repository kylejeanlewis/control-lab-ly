# %% -*- coding: utf-8 -*-
"""
Created: Tue 2022/11/02 17:13:35
@author: Chang Jie

Notes / actionables:
-
"""
# Standard library imports
import numpy as np
import pandas as pd
import pkgutil
import time

# Local application imports
from .....Analyse.Data.Types.scpi_datatype import SCPI
print(f"Import: OK <{__name__}>")

class Program(object):
    def __init__(self, device, params={}):
        self.data_df = pd.DataFrame()
        self.device = device
        self.parameters = params
        self.scpi = None
        self.sub_program = {}
        
        self._program_template = None
        pass
    
    def loadSCPI(self, program, params={}):
        if type(program) == str:
            if program.endswith('.txt'):
                program = pkgutil.get_data(__name__, program).decode('utf-8')
            program = SCPI(program)
        elif 'SCPI' in str(type(program)):
            pass
        else:
            print('Please input either filename or SCPI instruction string!')
            return
        
        if program.string.count('###') != 2:
            raise Exception('Check SCPI input! Please use exact 2 "###" dividers to separate settings, inputs, and outputs.')
        self._program_template = program
        self.scpi = program
        
        if len(params):
            self.setParameters(params)
        return
    
    def run(self, field_titles=[], values=[], average=False, wait=0):
        # connect to device
        self.device._write(['*RST'])
        prompts = self.scpi.getPrompts()
        self.device._write(prompts['settings'])
        
        if len(values):
            for value in values:
                # if self.flags['stop_measure']:
                #     break
                prompt = [l.format(value=value) for l in prompts['inputs']]
                self.device._write(prompt)
                time.sleep(wait)
                df = self.device._read(prompts['outputs'], field_titles=field_titles, average=average)
                self.data_df = pd.concat([self.data_df, df], ignore_index=True)
        else:
            self.device._write(prompts['inputs'])
            time.sleep(wait)
            self.data_df = self.device._read(prompts['outputs'], field_titles=field_titles, average=average)

        self.device._write(['OUTP OFF'])
        # disconnect from device
        return self.data_df
    
    def setParameters(self, params={}):
        if len(params) == 0:
            raise Exception('Please input parameters.')
        this_program = None
        this_program = SCPI(self._program_template.replace(**params))
        # self.flags['parameters_set'] = True
        self.scpi = this_program
        self.parameters = params
        return


class IV_Scan(Program):
    def __init__(self, device, params={}):
        super().__init__(device, params)
        super().loadSCPI('SCPI_iv.txt')
        return
    
    def run(self, values):
        return super().run(field_titles=['I', 'V'], values=values, average=True)


class OCV(Program):
    def __init__(self, device, params={}):
        super().__init__(device, params)
        super().loadSCPI('SCPI_bias.txt')
        return
    
    def run(self):
        return super().run(field_titles=['V'], average=True)


class SweepV(Program):
    def __init__(self, device, params={}):
        super().__init__(device, params)
        super().loadSCPI('SCPI_sweep_volt.txt')
        return
    
    def run(self, voltages, dwell_time, num_points, wait):
        self.setParameters(dict(voltages=voltages, dwell_time=dwell_time, num_points=num_points))
        return super().run(field_titles=['V', 'I', 't'], wait=wait)


class LSV(Program):
    def __init__(self, device, params={}):
        super().__init__(device, params)
        self.sub_program['OCV'] = OCV(device)
        self.sub_program['sweep'] = SweepV(device)
        return
    
    def run(self, volt_range, sweep_rate=0.01, dual=True):
        df = self.sub_program['OCV'].run()
        potential = round(df.at[0,'V'], 3)
        print(f'OCV = {potential}V')
        
        start, stop, step = volt_range
        points = ((stop - start) / step) + 1
        num_points = 2 * points - 1 if dual else points

        voltages = ", ".join(str(v) for v in (start,stop,points))
        dwell_time = step / sweep_rate
        wait = num_points * dwell_time * 2
        print(time.time())
        print(f'Expected measurement time: {wait}s')
        
        self.sub_program['sweep'].run(voltages=voltages, dwell_time=dwell_time, num_points=num_points, wait=wait)
        return
