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
from controllable.Analyse.Data.Types.eis_datatype import ImpedanceSpectrum
from controllable.Measure.Electrical import Biologic
# from controllable.builds.Paraspin import Setup, Program
# from controllable.builds.PrimitivEnder import Setup, Program
# from controllable.View import Optical
# from controllable.Move.Cartesian import Primitiv, Ender
# from controllable.Measure.Electrical.Keithley import Keithley
# from controllable.misc.misc_utils import Helper
from controllable.Measure.Electrical.Biologic.programs import base_programs
# from controllable.View.view_utils import Optical
print(f"Import: OK <{__name__}>")

if __name__ == "__main__":
    # helper = Helper()
    # see = Optical()
    # helper.display_ports()
    pass

# %% Cartesian examples
if __name__ == "__main__":
    mover = Ender('COM4')
    # mover = Primitiv('COM5')
    pass

# %% Keithley examples
if __name__ == "__main__":
    keith = Keithley.Keithley('192.168.1.100')
    keith.loadProgram('OCV')
    keith.measure()
    # mover = Primitiv('COM5')
    pass

# %%
if __name__ == "__main__":
    # measurer = Keithley.Keithley('192.168.1.100')
    measurer = Biologic.BioLogic('192.109.209.128')
    measurer.reset()
    params = {
        'voltage': 0,
        'amplitude_voltage': 0.01,
        'initial_frequency': 200E3,
        'final_frequency': 100E-3,
        'frequency_number': 38,
        'duration': 10,
        'repeat': 2,
        'wait': 0.10
    }

    measurer.loadProgram(base_programs.PEIS, params, channels=[0])
    measurer.measure(ImpedanceSpectrum)
    pass

# %%
if __name__ == "__main__":
    measurer.reset()
    params = {
        'time': 1,
        'voltage_interval': 0.01
    }

    measurer.loadProgram('OCV', params, channels=[0])
    measurer.measure(None)
    pass

# %%
if __name__ == "__main__":
    measurer.reset()
    params = dict(
        current = 0,
        amplitude_current = 0.001,
        initial_frequency = 200E3,
        final_frequency = 100E-3,
        frequency_number = 38,
        duration = 10,
        repeat= 2,
        wait= 0.5
    )

    measurer.loadProgram('GEIS', params, channels=[0])
    measurer.measure(ImpedanceSpectrum)
    pass

# %%
if __name__ == "__main__":
    measurer.reset()
    params = dict(
        voltages = [0,1,-2,0,0],
        scan_rate = 1,
        vs_initial = True,
        voltage_interval = 0.001,
        wait = 0.5,
        cycles = 1
    )

    measurer.loadProgram(base_programs.CV, params, channels=[0])
    measurer.measure(None)
    pass

# %%
