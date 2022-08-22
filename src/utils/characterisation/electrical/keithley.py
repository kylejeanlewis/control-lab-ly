# %%
# -*- coding: utf-8 -*-
"""
Created on Fri 2022/03/18 09:00:00

@author: Chang Jie
"""
import time
import numpy as np
import pandas as pd
import pyvisa as visa
print(f"Import: OK <{__name__}>")

# %% Keithley
def edit_SCPI(string='', scpi=[], **kwargs):
    if len(string) == 0 and len(scpi) == 0:
        print('Please input either filename or SCPI instruction string!')
        return
    elif len(string) == 0 and len(scpi):
        scpi_join = ['\n'.join(s) for s in scpi]
        string = '\n###\n'.join(scpi_join)
    
    for k,v in kwargs.items():
        if type(v) == bool:
            v = 'ON' if v else 'OFF'
        string = string.replace(f'<{k}>', str(v))
    return string

def parse_SCPI(string):
    scpi_split = string.split('###')
    for i,s in enumerate(scpi_split):
        scpi_split[i] = [l.strip() for l in s.split('\n') if len(l)]
    if len(scpi_split) == 1:
        scpi_split = scpi_split[0]
    return scpi_split

class SCPI(object):
    def __init__(self, string='', scpi_list=[]):
        if len(string) == 0 and len(scpi_list):
            scpi_join = ['\n'.join(s) for s in scpi_list]
            string = '\n###\n'.join(scpi_join)
        elif string.endswith('.txt'):
            with open(string) as file:
                string = file.read()
        if len(string) == 0:
            raise Exception('Please input either filename or SCPI instruction string/list!')
        self.string = string

    def replace(self, inplace=False, **kwargs):
        string = self.string
        for k,v in kwargs.items():
            if type(v) == bool:
                v = 'ON' if v else 'OFF'
            string = string.replace(f'<{k}>', str(v))
        if inplace:
            self.string = string
            return
        return string

    def parse(self):
        scpi_split = self.string.split('###')
        for i,s in enumerate(scpi_split):
            scpi_split[i] = [l.strip() for l in s.split('\n') if len(l)]
        if len(scpi_split) == 1:
            scpi_split = scpi_split[0]
        return scpi_split


class Keithley(object):
    """
    Keithley relay.
    - address: (short) IP address of Keithley
    - settings: settings to be applied
    - numreadings: number of readings at each I-V combination
    - buffersize: size of buffer
    - name: nickname for Keithley
    """
    def __init__(self, address, name=''):
        print(f"\nSetting up {name.title()} Keithley comms...")
        
        self.address = address
        self.name = name
        self.inst = self.connect(address)
        self.buffer = f'{name}data'

        self.buffer_df = pd.DataFrame()
        self.buffersize = 0
        self.numreadings = 0
        self.source_read = [('',''), ('','')]
        self.scpi = []
        
        # print(f"{self.name.title()} Keithley ready")
        pass

    def connect(self, address):
        """
        Establish connection with Keithley
        - address: (short) IP address of Keithley

        Return: Keithley instance
        """
        inst = None
        try:
            full_address = f"TCPIP0::192.168.1.{address}::5025::SOCKET"
            rm = visa.ResourceManager('@py')
            inst = rm.open_resource(full_address)

            inst.write_termination = '\n'
            inst.read_termination = '\n'
            inst.write('SYST:BEEP 500, 1')
            inst.query('*IDN?')
        except Exception as e:
            print("Unable to connect to Keithley!")
            print(e)
            pass
        return inst

    def getSCPI(self, filename='', string='', **kwargs):
        """
        
        """
        if len(filename):
            with open(filename) as file:
                string = file.read()
                pass
        elif len(string) == 0:
            print('Please input either filename or SCPI instruction string!')
            return []

        string = edit_SCPI(string, **kwargs)
        if string.count('###') != 2:
            print('Check SCPI input! Please use only 2 "###" dividers.')
            return []
        self.scpi = parse_SCPI(string)
        return self.scpi

    def measure(self, batch=False):
        self.reset()
        settings, send_msg, recv_msg = self.scpi
        self.setParameters(settings)

        if batch:
            self.setParameters(send_msg)
            df = self.readData(recv_msg)
            pass
        else:
            # for loop
            # self.setParameters(send_msg)
            # df = self.readData(recv_msg)
            pass

        return df

    def readData(self, recv_msg, columns, average=False, cache=False):
        """
        Read data from Keithley and saving to self.buffer_df
        """
        outp = ''
        try:
            self.inst.write(recv_msg)
            outp = None
            while outp is None:
                outp = self.inst.read()
        except AttributeError as e:
            print(e)
        data = np.reshape(np.array(outp.split(',')), (-1,len(columns)))
        if average:
            avg = np.mean(data, axis=0)
            std = np.std(data, axis=0)
            data = np.concatenate([avg, std])
            columns = columns + [c+'_std' for c in columns]
        df = pd.DataFrame(data, columns=columns, dtype=np.float64)
        if cache:
            self.buffer_df = pd.concat([self.buffer_df, df])
        return df

    def reset(self):
        self.buffer_df = pd.DataFrame()
        self.buffersize = 0
        self.numreadings = 0
        self.source_read = [('',''), ('','')]
        self.setParameters(['*RST'])
        return

    def setParameters(self, params=[]):
        """
        Relay parameters to Keithley
        - params: list of parameters to write to Keithley
        """
        try:
            for param in params:
                if '<' in param or '>' in param:
                    continue
                self.inst.write(param)
        except AttributeError as e:
            print(e)
            pass
        return


class KeithleyFET(Keithley):
    def __init__(self, address, name=''):
        super().__init__(address, name)
        return

    def measure(self, batch=False):
        self.getSCPI('keithley/SCPI_fet.txt', count=3, buff_name=self.buffer, buff_size=self.buffersize)
        return super().measure(batch)


class KeithleyHYS(Keithley):
    def __init__(self, address, name=''):
        super().__init__(address, name)
        return

    def measure(self, batch=False):
        self.getSCPI('keithley/SCPI_hysteresis.txt', count=3, buff_name=self.buffer, buff_size=self.buffersize)
        return super().measure(batch)


class KeithleyIV(Keithley):
    def __init__(self, address, name=''):
        super().__init__(address, name)
        return

    def measure(self, batch=False):
        self.getSCPI('keithley/SCPI_iv.txt', count=3, buff_name=self.buffer, buff_size=self.buffersize)
        return super().measure(batch)


class KeithleyLSV(Keithley):
    def __init__(self, address, name=''):
        super().__init__(address, name)
        return

    def measure(self, name, margin=0.5):
        bias = self.measure_bias()
        lsv_df = self.measure_sweep((bias-margin, bias+margin, margin*2*100+1))
        lsv_df.to_csv(f'{name}.csv')
        return lsv_df

    def measure_bias(self):
        self.getSCPI('keithley/SCPI_bias.txt', count=3, buff_name=self.buffer, buff_size=self.buffersize)
        settings, send_msg, recv_msg = self.scpi
        self.setParameters(settings)
        self.setParameters(send_msg)
        # scpi = [
        #     '*RST',
        #     'ROUT:TERM FRONT',
        #     'OUTP:SMOD HIMP',

        #     'SOUR:FUNC CURR',
        #     'SOUR:CURR 0',
        #     'SOUR:CURR:RANG 1',
        #     'SOUR:CURR:VLIM 20',
            
        #     'SENS:FUNC "VOLT"',
        #     'SENS:VOLT:RANG 20',
        #     'SENS:COUN 3',

        #     'TRAC:MAKE "biasdata", 100',
        #     'SYST:BEEP 440, 1',

        #     'SOUR:CURR 0',
        #     'TRAC:CLE "biasdata"',
        #     'OUTP ON',
        #     'TRAC:TRIG "biasdata"'
        # ]
        # self.set_parameters(scpi)
        # recv = 'TRAC:DATA? 1, 3, "biasdata", READ'
        df = self.readData(recv_msg, ['V'], average=True)

        ocv = round(df.at[0,0], 3)
        print(f'OCV = {ocv}V')
        return ocv

    def measure_sweep(self, volt_range=(np.nan, np.nan, np.nan), dwell_time=0.1):
        num_points = 2 * volt_range[2] - 1
        voltages = ", ".join(str(v) for v in volt_range)
        self.getSCPI('keithley/SCPI_sweep_volt.txt', voltages=voltages, dwell_time=dwell_time, num_points=num_points)
        settings, send_msg, recv_msg = self.scpi
        # scpi = [
        #     '*RST',
        #     'ROUT:TERM FRONT',
        #     'OUTP:SMOD HIMP',

        #     'SOUR:FUNC VOLT',
        #     'SOUR:VOLT:RANG 20',
        #     'SOUR:VOLT:ILIM 1',

        #     'SENS:FUNC "CURR"',
        #     'SENS:CURR:RANG:AUTO ON',
        #     'SENS:CURR:RSEN OFF',
            
        #     'SYST:BEEP 440, 1',
            
        #     f'SOUR:SWE:VOLT:LIN {", ".join(str(v) for v in volt_range)}, {dwell_time}, 1, BEST, OFF, ON',
        #     'INIT',
        #     '*WAI',
        # ]
        # self.set_parameters(scpi)
        # recv = f'TRAC:DATA? 1, {2*volt_range[2]-1}, "defbuffer1", SOUR, READ, REL'

        self.setParameters(settings)
        self.setParameters(send_msg)
        time.sleep(2*volt_range[2] * 2*dwell_time)
        df = self.readData(recv_msg, ['V', 'I', 't'])
        self.setParameters(['OUTP OFF'])
        
        df.plot('V', 'I')
        diff = df.diff()
        df['Q'] = df['I'] * diff['t']
        df['dQdV'] = df['Q'].diff() / df['V'].diff()
        df.plot('V', 'dQdV')
        return df


# %%
