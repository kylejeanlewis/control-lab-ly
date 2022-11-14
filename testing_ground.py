# %% -*- coding: utf-8 -*-
"""
Created: Tue 2022/11/01 17:13:35
@author: Chang Jie

Notes / actionables:
-
"""
# Standard library imports
import numpy as np
import pandas as pd
# Third party imports

# Local application imports
# from controllable.Move import Cartesian, Jointed
# from controllable.builds import mySetup
# from controllable.Measure.Electrical.Biologic import biologic_utils
from controllable.Analyse.Data.Types.eis_datatype import ImpedanceSpectrum
from controllable.Measure.Electrical import Biologic, Keithley
# from controllable.builds.Paraspin import Setup, Program
# from controllable.builds.PrimitivEnder import Setup, Program
from controllable.View import Optical
from controllable.Move.Cartesian import Primitiv, Ender
# from controllable.Measure.Electrical.Keithley import Keithley
from controllable.misc.misc_utils import Helper
print(f"Import: OK <{__name__}>")

if __name__ == "__main__":
    helper = Helper()
    # helper.display_ports()
    pass
# %%
if __name__ == "__main__":
    mover = Ender('COM4')
    # mover = Primitiv('COM5')
    pass
# %%
if __name__ == "__main__":
    # measurer = Keithley.Keithley('192.168.1.100')
    measurer = Biologic.BioLogic('192.109.209.128')
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

    measurer.loadProgram('PEIS', params, channels=[0])
    measurer.measure(ImpedanceSpectrum)

# %%
if __name__ == "__main__":
    params = {
        'time': 1,
        'voltage_interval': 0.01
    }

    measurer.loadProgram('OCV', params, channels=[0])
    measurer.measure()