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
        self.retrieve_data_SCPI = ''
        self.source_read = ('','')
        
        print(f"{self.name.title()} Keithley ready")
        pass
    
    def applySettings(self, source, numreadings, buffersize=100, **kwargs):
        """
        Apply settings to Keithley
        - settings: list of strings to be fed to Keithley
        - numbreadings: number of readings per measurement
        - buffersize: buffer size

        Return: str, str (tags for reading I,V data)
        """
        kw = kwargs
        scpi = self.getSCPI(
            numreadings = numreadings,
            buffersize = buffersize
        )
        self.setParameters(scpi)
        return

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

    def getSCPI(self, filename='', **kwargs):
        """
        
        """
        scpi = []
        # if len(filename):
        #     with open(filename) as file:
        #         scpi = ''
        #         pass
        
        # for k,v in kwargs:
        #     scpi.replace(f'<k>', str(v))
        
        # self.inst.write(f'SENS:COUN {kwargs["numreadings"]}')
        # self.inst.write(f'TRAC:MAKE {self.buffer}, {kwargs["buffersize"]}')
        # self.inst.write(f'TRAC:DATA? 1, {self.numreadings}, {self.buffer}, SOUR, READ')

        # for instruction in scpi:
        #     if instruction.startswith('TRAC:DATA?') or instruction.startswith('trace:data?'):
        #         self.retrieve_data_SCPI = instruction
        # self.source_read = ('V', 'I')
        return scpi

    def readData(self, columns, average=False, cache=False):
        """
        Read data from Keithley and saving to self.buffer_df
        """
        outp = ''
        try:
            self.inst.write(self.retrieve_data_SCPI)
            outp = None
            while outp is None:
                outp = self.inst.read()
        except AttributeError as e:
            print(e)
        data = np.reshape(np.array(outp.split(',')), (-1,len(columns)))
        if average:
            data = np.mean(data, axis=0)
        df = pd.DataFrame(data, columns=columns, dtype=np.float64)
        if cache:
            self.buffer_df = pd.concat([self.buffer_df, df])
        return df

    def setParameters(self, params=[]):
        """
        Relay parameters to Keithley
        - params: list of parameters to write to Keithley
        """
        try:
            for param in params:
                self.inst.write(param)
        except AttributeError as e:
            print(e)
            pass
        return


class KeithleyIV(Keithley):
    def __init__(self):
        return

    def measure(self):
        settings_fet = [
            '*RST',
            'ROUT:TERM FRONT',
            'SOUR:FUNC VOLT',
            'SOUR:VOLT:RANG 200',
            'SOUR:VOLT:ILIM 0.01',

            'SENS:FUNC "CURR"',
            'SENS:CURR:RSEN OFF',
            'SENS:CURR:RANGE 10E-6',
            'SENS:CURR:UNIT AMP'
        ]
        
        settings_hysteresis = [
            '*RST',
            'ROUT:TERM FRONT',
            'SENS:FUNC "VOLT"',
            'SENS:VOLT:RSEN ON',
            'SENS:VOLT:RANG:AUTO ON',
            'SENS:VOLT:NPLC 5',
            'SENS:VOLT:UNIT OHM',
            'SENS:VOLT:OCOM ON',

            'SOUR:FUNC CURR',
            'SOUR:CURR:RANG:AUTO ON',
            'SOUR:CURR:VLIM 200',
            #f'SENS:VOLT:RANG {voltmeter_range}',
            f'SOUR:CURR {settings_fet}',
            'OUTP ON',
            ':syst:beep 440,1',
        ]

        settings_iv = [
            '*RST',
            'ROUT:TERM FRONT',
            'SOUR:FUNC CURR',
            'SOUR:CURR:RANG:AUTO ON',
            'SOUR:CURR:VLIM 200',
            
            'SENS:FUNC "VOLT"',
            'SENS:VOLT:RSENSE ON',
            'SENS:VOLT:RANG 200',
            'SENS:VOLT:UNIT VOLT'
        ]
        return


class KeithleyLSV(Keithley):
    def __init__(self):
        return

    def measure(self, name):
        bias = self.measure_bias()
        margin = 0.5
        lsv_df = self.measure_sweep((bias-margin, bias+margin, margin*200+1))
        lsv_df.to_csv(f'{name}.csv')
        return lsv_df

    def measure_bias(self):
        scpi = [
            '*RST',
            'OUTP:SMOD HIMP',
            'SOUR:FUNC CURR',
            'SOUR:CURR 0',
            'SOUR:CURR:RANG 1',
            'SOUR:CURR:VLIM 20',
            
            'SENS:FUNC "VOLT"',
            'SENS:VOLT:RANG 20',

            'SENS:COUN 3',
            'TRAC:MAKE "biasdata", 100',

            'SOUR:CURR 0',
            'TRAC:CLE "biasdata"',
            'OUTP ON',
            'TRAC:TRIG "biasdata"'
        ]
        self.set_parameters(scpi)
        self.retrieve_data_SCPI = 'TRAC:DATA? 1, 3, "biasdata", READ'
        df = self.readData(['V'], average=True)

        ocv = round(df.at[0,0], 3)
        print(f'OCV = {ocv}V')
        return ocv

    def measure_sweep(self, volt_range=(np.nan, np.nan, np.nan), dwell_time=0.1):
        scpi = [
            '*RST',
            'OUTP:SMOD HIMP',
            'SOUR:FUNC VOLT',
            'SOUR:VOLT:RANG 20',
            'SOUR:VOLT:ILIM 1',

            'SENS:FUNC "CURR"',
            'SENS:CURR:RANG:AUTO ON',
            'SENS:CURR:RSEN OFF',
            
            f'SOUR:SWE:VOLT:LIN {", ".join(str(v) for v in volt_range)}, {dwell_time}, 1, BEST, OFF, ON',
            'INIT',
            '*WAI',
        ]
        self.set_parameters(scpi)
        time.sleep(2*volt_range[2] * 2*dwell_time)
        self.retrieve_data_SCPI = f'TRAC:DATA? 1, {2*volt_range[2]-1}, "defbuffer1", SOUR, READ, REL'
        df = self.readData(['V', 'I', 't'])
        self.inst.write('OUTP OFF')
        
        df.plot('V', 'I')
        diff = df.diff()
        df['Q'] = df['I'] * diff['t']
        df['dQdV'] = df['Q'].diff() / df['V'].diff()
        df.plot('V', 'dQdV')
        return df

