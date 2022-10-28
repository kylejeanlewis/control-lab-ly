# %% -*- coding: utf-8 -*-
"""
Created on Fri 2022/06/18 09:00:00

@author: Chang Jie

Easy BioLogic package documentation can be found at:
https://github.com/bicarlsen/easy-biologic

Notes:
- (actionables)
"""
# Standard library imports
import nest_asyncio
import numpy as np
import os
import pandas as pd
import sys
import time

# Third party imports
import easy_biologic as biologic_api # pip install easy-biologic
import easy_biologic.base_programs as programs
from easy_biologic.program import BiologicProgram
import plotly.express as px # pip install plotly-express

# Local application imports
from eis_datatype import ImpedanceSpectrum
print(f"Import: OK <{__name__}>")

# CONSTANTS
IP_ADDRESS = '192.109.209.128'

# INITIALIZING
nest_asyncio.apply()

# %%
class BioLogic(object):
    def __init__(self, name='', address=IP_ADDRESS):
        self.name = name
        self.flags = {}
        self.address = address
        self.inst = biologic_api.BiologicDevice(address, populate_info=True)
        self.buffer_df = pd.DataFrame()
        self.program = None
        return
    
    def _connect(self):
        return self.inst.connect()
    
    def loadProgram(self, program: BiologicProgram, params={}, channels=[0]):
        self.program = program(self.inst, params, channels)
        return
    
    def measure(self):
        self.program.run()
        return
    
    def readData(self):
        return self.program.data
    
    def reset(self):
        self.program = None
        return
    
    def saveData(self, filename):
        self.program.save_data(filename)
        return
    
    def setParameters(self, params={}):
        return
    
#%% create GEIS program
# create device
# bl = biologic_api.BiologicDevice(IP_ADDRESS, populate_info=True)
device = BioLogic(address=IP_ADDRESS)
'''
current: Initial current in Ampere.
amplitude_current: Sinus amplitude in Ampere.
initial_frequency: Initial frequency in Hertz.
final_frequency: Final frequency in Hertz.
frequency_number: Number of frequencies.
duration: Overall duration in seconds. # Comment: Isn't this really a step duration?
vs_initial: If step is vs. initial or previous.
    [Default: False]
time_interval: Maximum time interval between points in seconds.
    [Default: 1]
potential_interval: Maximum interval between points in Volts.
    [Default: 0.001]
sweep: Defines whether the spacing between frequencies is logarithmic
    ('log') or linear ('lin'). [Default: 'log']
repeat: Number of times to repeat the measurement and average the values
    for each frequency. [Default: 1]
correction: Drift correction. [Default: False]
wait: Adds a delay before the measurement at each frequency. The delay
    is expressed as a fraction of the period. [Default: 0]
'''
params = {
	'voltage': 0,
    'amplitude_voltage': 0.01,
    'initial_frequency': 200E3,
    'final_frequency': 100E-3,
    'frequency_number': 38,
    'duration': 120,
    'repeat': 2,
    'wait': 0.10
}

# peis = programs.PEIS(bl, params, channels=[0])
device.loadProgram(programs.PEIS, params, [0])
# %%run program
# peis.run()
device.measure()
# %%
params = {
	'time':1,
    'voltage_interval':0.01
}

ocv = programs.OCV(bl, params, channels=[0])

# %%run program
ocv.run()
ocv.save_data()
# %%
"""
First-party recommended way
"""
import time
from bio_logic import SP150, OCV, GeneralPotentiostat

class SP300(GeneralPotentiostat):
    """Specific driver for the SP-150 potentiostat"""

    def __init__(self, address, EClib_dll_path=None):
        """Initialize the SP150 potentiostat driver

        See the __init__ method for the GeneralPotentiostat class for an
        explanation of the arguments.
        """
        super(SP300, self).__init__(
            type_='KBIO_DEV_SP300',
            address=address,
            EClib_dll_path=EClib_dll_path
        )

# %%
def run_ocv(device_class):
    """Test the OCV technique"""
    global device
    ip_address = b'192.168.0.135'  # REPLACE THIS WITH A VALID IP
    # Instantiate the instrument and connect to it
    device = device_class(ip_address)
    device.connect()

    # Instantiate the technique. Make sure to give values for all the
    # arguments where the default values does not fit your purpose. The
    # default values can be viewed in the API documentation for the
    # technique.
    ocv = OCV(rest_time_T=0.2,
              record_every_dE=10.0,
              record_every_dT=0.01)

    # Load the technique onto channel 0 of the potentiostat and start it
    device.load_technique(0, ocv)
    device.start_channel(0)

    time.sleep(0.1)
    while True:
        # Get the currently available data on channel 0 (only what has
        # been gathered since last get_data)
        data_out = device.get_data(0)

        # If there is none, assume the technique has finished
        if data_out is None:
            break

        # The data is available in lists as attributes on the data
        # object. The available data fields are listed in the API
        # documentation for the technique.
        print("Time:", data_out.time)
        print("Ewe:", data_out.Ewe)

        # If numpy is installed, the data can also be retrieved as
        # numpy arrays
        #print('Time:', data_out.time_numpy)
        #print('Ewe:', data_out.Ewe_numpy)
        time.sleep(0.1)

    device.stop_channel(0)
    device.disconnect()

if __name__ == '__main__':
    run_ocv(SP300)

# %%
