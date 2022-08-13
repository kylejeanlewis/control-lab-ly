# %%
# -*- coding: utf-8 -*-
"""
Created on Fri 2022/03/18 09:00:00

@author: Chang Jie
"""
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
        self.numreadings = 0
        self.buffersize = 0
        self.buffer = ''
        self.buffer_df = pd.DataFrame()

        self.inst = self.connect(address)
        self.getI = ''
        self.getV = ''
        
        print(f"{self.name.title()} Keithley ready")
        pass
    
    def apply_settings(self, settings, source, numreadings, buffersize=100):
        """
        Apply settings to Keithley
        - settings: list of strings to be fed to Keithley
        - numbreadings: number of readings per measurement
        - buffersize: buffer size

        Return: str, str (tags for reading I,V data)
        """
        self.numreadings = numreadings
        self.buffersize = buffersize
        self.buffer = f'"{self.name}data"'
        count = f'SENS:COUN {numreadings}'
        makebuffer = f'TRAC:MAKE {self.buffer}, {buffersize}'
        if source == 'V':
            getV = f'TRAC:DATA? 1, {numreadings}, {self.buffer}, SOUR'
            getI = f'TRAC:DATA? 1, {numreadings}, {self.buffer}, READ'
        elif source== 'I':
            getI = f'TRAC:DATA? 1, {numreadings}, {self.buffer}, SOUR'
            getV = f'TRAC:DATA? 1, {numreadings}, {self.buffer}, READ'

        try:
            for setting in settings:
                self.inst.write(setting)
            self.inst.write(count)
            self.inst.write(makebuffer)
        except Exception as e:
            print(e)
            pass
        return getI, getV

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

    def read_data(self):
        """
        Read data from Keithley and saving to self.buffer_df
        """
        n = self.name[0]
        volt = 0
        try:
            self.inst.write(self.getV)
            volt = None
        except:
            pass
        while volt is None:
            try:
                volt = self.inst.read()
            except:
                pass
        volt_split = volt.split(',')

        curr = 0
        try:
            self.inst.write(self.getI)
            curr = None
        except:
            pass
        while curr is None:
            try:
                curr = self.inst.read()
            except:
                pass
        curr_split = curr.split(',')
        
        row = np.column_stack((volt_split, curr_split)).astype('float64')
        data_row = pd.DataFrame(row, columns = [f'V{n}', f'I{n}'])
        self.buffer_df = pd.concat([self.buffer_df, data_row])
        return

    def set_parameters(self, params=[]):
        """
        Relay parameters to Keithley
        - params: list of parameters to write to Keithley
        """
        try:
            for param in params:
                self.inst.write(param)
        except:
            pass
        return
