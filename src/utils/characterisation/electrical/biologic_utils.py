# %%
# -*- coding: utf-8 -*-
"""
Created on Fri 2022/06/18 09:00:00

@author: Chang Jie

Easy BioLogic package documentation can be found at:
https://github.com/bicarlsen/easy-biologic
"""
import os, sys
import time
import easy_biologic as ebl # pip install easy-biologic
import easy_biologic.base_programs as blp

from eis_datatype import ImpedanceSpectrum
print(f"Import: OK <{__name__}>")

# %%
# create device
bl = ebl.BiologicDevice('192.168.1.2', populate_info=False)

# create GEIS program
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
	'run_time': 10* 60,
    'current': 0,
    'amplitude_current': 5E-3,
    'initial_frequency': 5,
    'final_frequency': 5E4,
    'frequency_number': 100,
    'duration': 1
}

geis = blp.GEIS(
    bl,
    params, 	
    channels = [0]        
)

# run program
geis.run( 'data' )

# %%
"""
First-party recommended way
"""


class BioLogic(object):
    def __init__(self, address, timeout=5, populate_info=True):
        super().__init__(address, timeout, populate_info)
        
    def connect(self, bin_file=None, xlx_file=None):
        return super().connect(bin_file, xlx_file)
    
    def measure(self, chs=None):
        return super().start_channels(chs)
