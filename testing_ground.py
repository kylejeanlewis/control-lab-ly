# %% -*- coding: utf-8 -*-
"""
Created: Tue 2022/11/01 17:13:35
@author: Chang Jie

Notes / actionables:
- test Viewers (Optical / Thermal)
- test database_utils
- add 'Visualisation' modules
- add 'GUI' modules
"""
# Standard library imports
import numpy as np
import pandas as pd
# Third party imports

# Local application imports
# from controllable.builds.Paraspin import Setup, Program
# from controllable.builds.PrimitivEnder import Setup, Program
print(f"Import: OK <{__name__}>")

# %% Helper examples
from controllable.misc import Helper
if __name__ == "__main__":
    from controllable.misc.misc_utils import Helper
    helper = Helper()
    helper.display_ports()
    pass

# %% Cartesian examples
from controllable.Move.Cartesian import Primitiv, Ender
if __name__ == "__main__":
    mover = Ender('COM4')
    # mover = Primitiv('COM5')
    pass

# %% Jointed examples
from controllable.Move.Jointed import Dobot
if __name__ == "__main__":
    mover = Dobot('192.168.2.8')
    pass

# %% Keithley examples
from controllable.Measure.Electrical import Keithley
if __name__ == "__main__":
    measurer = Keithley.Keithley('192.168.1.104')
    measurer.loadProgram('LSV')
    measurer.measure(volt_range=(-0.7, 0.7, 0.01))
    pass

# %% BioLogic examples
from controllable.Measure.Electrical import Biologic
from controllable.Measure.Electrical.Biologic.programs import base_programs
from controllable.Analyse.Data.Types.eis_datatype import ImpedanceSpectrum
if __name__ == "__main__":
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

# %% BioLogic examples
if __name__ == "__main__":
    measurer.reset()
    params = {
        'time': 1,
        'voltage_interval': 0.01
    }

    measurer.loadProgram('OCV', params, channels=[0])
    measurer.measure(None)
    pass

# %% BioLogic examples
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

# %% BioLogic examples
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

# %% Webcam examples
from controllable.View import Optical
if __name__ == "__main__":
    viewer = Optical()
    viewer.getImage()
    pass

# %% GUI examples
from controllable.Move.Cartesian import Ender
# from controllable.Move.Jointed import Dobot
from controllable.View import Optical
from controllable.Control.GUI.gui_utils import MoverPanel, CompoundPanel, ViewerPanel
if __name__ == "__main__":
    ensemble = {
        'Camera': (ViewerPanel, dict(viewer=Optical())),
        # 'Primitiv': (MoverPanel, dict(mover=Primitiv('COM4'), axes=['X'])),
        'Ender': (MoverPanel, dict(mover=Ender('COM5'), axes=['X','Y','Z'])),
        # 'Dobot': (MoverPanel, dict(mover=Dobot('COM5'), axes=['X','Y','Z','a','b','g'])),
    }
    gui = CompoundPanel(ensemble)
    gui.runGUI('Primitiv')
    pass

# %%
