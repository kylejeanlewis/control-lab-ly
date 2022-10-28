# %%
# -*- coding: utf-8 -*-
"""
Created on Fri 2022/08/15 09:00:00

@author: Chang Jie

Notes:
- validation on copper 
- rewrite the operation modes as programs, instead of subclasses
"""
import time
import numpy as np
import pandas as pd
import pyvisa as visa
print(f"Import: OK <{__name__}>")

NUM_READINGS = 3
BUFFER_SIZE = 100
MAX_BUFFER_SIZE = 10000

# %% Keithley
class SCPI(object):
    """
    SCPI input class for Keithley.
    
    Args:
        string (str): text string of SCPI commands or filename of txt file where SCPI commands are saved
        scpi_list (list): list of SCPI commands line-by-line
    """
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
        return

    def replace(self, inplace=False, **kwargs):
        """
        Replace placeholder text in SCPI commands with desired values.
        
        Args:
            inplace (bool): whether to replace text in place
        
        Retruns:
            str: SCPI commands with desired values
        """
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
        """
        Parse SCPI command into blocks corresponding to settings prompt, input prompt, and output prompt.
        
        Returns:
            list: SCPI prompts for settings, inputs, and outputs
        """
        scpi_split = self.string.split('###')
        for i,s in enumerate(scpi_split):
            scpi_split[i] = [l.strip() for l in s.split('\n') if len(l)]
        if len(scpi_split) == 1:
            scpi_split = scpi_split[0]
        return scpi_split


class Keithley(object):
    """
    Keithley class.
    
    Args:
        address (str/int): short IP address of Keithley
        name (str): nickname for Keithley
    """
    def __init__(self, address, name=''):
        print(f"\nSetting up {name.title()} Keithley comms...")
        
        self.address = address
        self.name = name
        self.inst = self.connect(address)
        self.buffer = f'{name}data'

        self.buffer_df = pd.DataFrame()
        self.buffersize = BUFFER_SIZE
        self.numreadings = NUM_READINGS
        self.scpi = None

        self.flags = {
            'stop_measure': False
        }
        return

    def connect(self, address):
        """
        Establish connection with Keithley.
        
        Args:
            address (str/int): short IP address of Keithley

        Returns: 
            pyvisa.Resource: Keithley instance
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
            print(f"{self.name.title()} Keithley ready")
        except Exception as e:
            print("Unable to connect to Keithley!")
            print(e)
            pass
        return inst

    def getSCPI(self, filename='', string='', **kwargs):
        """
        Retrieves the SCPI commands from either a file or text string, and replaces placeholder variables. 
        
        Args:
            filename (str): filename of txt file where SCPI commands are saved
            string (str): text string of SCPI commands
            
        Returns:
            list: SCPI prompts for settings, inputs, and outputs
        """
        if len(filename):
            self.scpi = SCPI(filename)
        elif len(string) == 0:
            print('Please input either filename or SCPI instruction string!')
            return []
        else:
            self.scpi = SCPI(string)
        
        self.scpi.replace(inplace=True, **kwargs)
        if self.scpi.string.count('###') != 2:
            print('Check SCPI input! Please use only 2 "###" dividers.')
            return []
        return self.scpi.parse()

    def logData(self, columns, average=False):
        """
        Logs data output as well as timestamp.
        
        Args:
            columns (list): list of parameters to read and log
            average  (bool): whether to calculate the average and standard deviation of multiple readings
        """
        start_time = time.time()
        while not self.flags['stop_measure'] and len(self.buffer_df) < MAX_BUFFER_SIZE:
            recv_msg = ['TRAC:TRIG "defbuffer1"', 'FETCH? "defbuffer1", READ, REL']
            self.readData(recv_msg, columns, average=average, cache=True)
            time.sleep(1)
        return

    def measure(self, columns=[], values=[], iterate=False, average=False, cache=False, pause=0, reset=False):
        """
        Perform the desired measurement.
        
        Args:
            columns (list): list of parameters to read
            values (list): list of values to iterate through
            iterate (bool): whether an iterative reading process is required
            average (bool): whether to calculate the average and standard deviation of multiple readings
            cache (bool): whetehr to save the measurements in a buffer dataframe
            pause (int/float): duration in seconds to wait before sending output prompt
            reset (bool): whether to reset Keithley before performing measurement
            
        Returns:
            pandas.DataFrame: dataframe of measurements
        """
        if reset:
            self.reset()
        settings, send_msg, recv_msg = self.scpi.parse()
        send_scpi = SCPI(scpi_list=[send_msg])

        df = pd.DataFrame()
        self.setParameters(settings)
        if iterate:
            for value in values:
                if self.flags['stop_measure']:
                    break
                send_value_scpi = SCPI(send_scpi.replace(value=value))
                self.setParameters(send_value_scpi.parse())
                time.sleep(pause)
                self.readData(recv_msg, columns=columns, average=average, cache=True)
            df = self.buffer_df
        else:
            self.setParameters(send_msg)
            time.sleep(pause)
            df = self.readData(recv_msg, columns=columns, average=average, cache=cache)

        self.setParameters(['OUTP OFF'])
        return df

    def readData(self, recv_msg, columns, average=False, cache=False):
        """
        Read data output from Keithley.
        
        Args:
            recv_msg (str): SCPI prompt for retrieving output
            columns (list): list of parameters to read
            average (bool): whether to calculate the average and standard deviation of multiple readings
            cache (bool): whetehr to save the measurements in a buffer dataframe
            
        Returns:
            pandas.DataFrame: dataframe of readings
        """
        outp = ''
        try:
            self.inst.write(recv_msg[0])
            outp = None
            while outp is None:
                outp = self.inst.read()
        except AttributeError as e:
            print(e)
        data = np.reshape(np.array(outp.split(','), dtype=np.float64), (-1,len(columns)))
        if average:
            avg = np.mean(data, axis=0)
            std = np.std(data, axis=0)
            data = np.concatenate([avg, std])
            columns = columns + [c+'_std' for c in columns]
            data = np.reshape(data, (-1,len(columns)))
        df = pd.DataFrame(data, columns=columns, dtype=np.float64)
        if cache:
            self.buffer_df = pd.concat([self.buffer_df, df], ignore_index=True)
        return df

    def reset(self):
        """Reset the Keithley."""
        self.buffer_df = pd.DataFrame()
        self.setParameters(['*RST'])
        return

    def setParameters(self, params=[]):
        """
        Relay parameters to Keithley.
        
        Args:
            params (list): list of parameters to write to Keithley
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


class KeithleyFET(object):
    """
    KeithleyFET class for FET measurements.
    
    Args:
        gate_details (tuple/list): address and name of gate Keithley
        drain_details (tuple/list): address and name of drain Keithley
    """
    def __init__(self, gate_details, drain_details):
        self.gate = Keithley(*gate_details)
        self.drain = Keithley(*drain_details)
        return

    def measure(self, save_name, sweep_drain, fixed_values, varied_values, reset=False):
        """
        Perform FET measurement.
        
        Args:
            save_name (str): filename of output file
            sweep_drain (bool): whether to sweep through values for drain (as opoosed to gate)
            fixed_values (list): step values
            varied_values (list): sweep values
            reset (bool): whether to reset Keithley before performing measurement
        """
        fixed, varied = (self.gate, self.drain) if sweep_drain else (self.drain, self.gate)
        test_name = 'Id-Vd' if sweep_drain else 'Id-Vg'
        
        keithleys = {'fixed': fixed, 'varied': varied}
        for keithley in keithleys.values():
            keithley.getSCPI('keithley/SCPI_fet.txt', count=keithley.numreadings, buff_name=keithley.buffer, buff_size=keithley.buffersize)
            if reset:
                keithley.reset()
            keithley.parsed = keithley.scpi.parse()
            keithley.setParameters(keithley.parsed[0])
        
        fixed_send_scpi = SCPI(scpi_list=[fixed.parsed[1]])
        varied_send_scpi = SCPI(scpi_list=[varied.parsed[1]])
        for f in fixed_values:
            if fixed.flags['stop_mesaure']:
                break
            send_scpi = SCPI(fixed_send_scpi.replace(value=f))
            fixed.setParameters(send_scpi.parse())
            time.sleep(0.5)
            for v in varied_values:
                if varied.flags['stop_mesaure']:
                    break
                send_scpi = SCPI(varied_send_scpi.replace(value=v))
                varied.setParameters(send_scpi.parse())
                fixed.setParameters([p for p in fixed.parsed[1] if p.startswith('TRAC:')])
                for keithley in keithleys.values():
                    keithley.readData(keithley.parsed[2], ['V', 'I'], average=True, cache=True)
            for keithley in keithleys.values():
                keithley.setParameters(['OUTP OFF'])
                keithley.buffer_df.to_csv(f'{save_name} {test_name}, {keithley.name.upper()[0]}.csv')
        return


# Rewrite the following as "programs" to load into the Keithley object
class KeithleyHYS(Keithley):
    """
    KeithleyHYS for hysteresis measurements.
    
    Args:
        address (str/int): short IP address of Keithley
        name (str): nickname for Keithley
    """
    def __init__(self, address, name=''):
        super().__init__(address, name)
        return

    def measure(self, save_name, values):
        """
        Perform hysteresis measurement.
        
        Args:
            save_name (str): filename of output file
            values (list): sweep values
            
        Returns:
            pandas.DataFrame: dataframe of readings
        """
        self.getSCPI('keithley/SCPI_hysteresis.txt', count=self.numreadings, buff_name=self.buffer, buff_size=self.buffersize)
        df = super().measure(['I', 'V'], values=values, iterate=True, average=True, cache=True)
        self.buffer_df.to_csv(f'{save_name}.csv')
        return df


class KeithleyIV(Keithley):
    """
    KeithleyIV for I-V measurements.
    
    Args:
        address (str/int): short IP address of Keithley
        name (str): nickname for Keithley
    """
    def __init__(self, address, name=''):
        super().__init__(address, name)
        return

    def measure(self, save_name, values):
        """
        Perform hysteresis measurement.
        
        Args:
            save_name (str): filename of output file
            values (list): sweep values
            
        Returns:
            pandas.DataFrame: dataframe of readings
        """
        self.getSCPI('keithley/SCPI_iv.txt', count=self.numreadings, buff_name=self.buffer, buff_size=self.buffersize)
        df = super().measure(['I', 'V'], values=values, iterate=True, average=True, cache=True)
        self.buffer_df.to_csv(f'{save_name}.csv')
        return df


class KeithleyLSV(Keithley):
    """
    KeithleyLSV for linear sweep voltammetry measurements.
    
    Args:
        address (str/int): short IP address of Keithley
        name (str): nickname for Keithley
    """
    def __init__(self, address, name=''):
        super().__init__(address, name)
        return

    def measure(self, save_name, margin=0.5):
        """
        Perform LSV measurement by first measuring the open-circuit voltage (OCV) of the cell, then sweep through a range of values within the specific margin from the OCV.
        
        Args:
            save_name (str): filename of output file
            margin (float): margin from the OCV to sweep voltage values
            
        Returns:
            pandas.DataFrame: dataframe of readings
        """
        bias = self.measure_bias()
        df = self.measure_sweep((bias-margin, bias+margin, 0.01))
        df.to_csv(f'{save_name}.csv')
        return df

    def measure_bias(self):
        """
        Measures the OCV of the cell.
        
        Returns:
            float: open-circuit voltage of cell
        """
        self.getSCPI('keithley/SCPI_bias.txt', count=self.numreadings, buff_name=self.buffer, buff_size=self.buffersize)
        df = super().measure(['V'], average=True)

        ocv = round(df.at[0,'V'], 3)
        print(f'OCV = {ocv}V')
        return ocv

    def measure_sweep(self, volt_range=(0, 1, 1), sweep_rate=0.01, dual=True):
        """
        Performs linear sweep voltammetry within specified range at specified sweep rate.
        
        Args:
            volt_range (tuple): start, stop and step values for voltage
            sweep_rate (float): sweep rate in V/s
            dual (bool): whether to sweep up and down (as opposed to just one direction/up)
        
        Returns:
            pandas.DataFrame: dataframe of readings and calculated values
        """
        start, stop, step = volt_range
        points = ((stop - start) / step) + 1
        num_points = 2 * points - 1 if dual else points

        voltages = ", ".join(str(v) for v in (start,stop,points))
        dwell_time = step / sweep_rate
        pause_time = num_points * dwell_time * 2
        print(time.time())
        print(f'Expected measurement time: {pause_time}s')

        self.getSCPI('keithley/SCPI_sweep_volt.txt', voltages=voltages, dwell_time=dwell_time, num_points=num_points)
        df = super().measure(['V', 'I', 't'], iterate=False, pause=pause_time)
        diff = df.diff()
        df['Q'] = df['I'] * diff['t']
        df['dQdV'] = df['Q'].diff() / df['V'].diff()
        self.buffer_df = df

        df.plot('V', 'I')
        df.plot('V', 'dQdV')
        return df


# %%
keith = KeithleyLSV(113, 'LSV')
keith.measure('LSV_test', margin=0.7)
# %%
