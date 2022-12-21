# %% -*- coding: utf-8 -*-
"""
Created: Tue 2022/11/01 17:13:35
@author: Chang Jie

Notes / actionables:
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
from controllable.Move.Jointed import MG400
if __name__ == "__main__":
    mover = MG400(ip_address='192.168.1.7')
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

# %% Thermal cam examples
from controllable.View import Thermal
if __name__ == "__main__":
    viewer = Thermal('192.168.1.111')
    viewer.getImage()
    pass

# %% GUI examples
from controllable.Move.Cartesian import Ender, Primitiv
from controllable.Move.Jointed import Dobot
from controllable.View import Optical, Thermal
from controllable.Control.GUI.gui_utils import MoverPanel, CompoundPanel, ViewerPanel
if __name__ == "__main__":
    ensemble = {
        'Camera': (ViewerPanel, dict(viewer=Optical())),
        'Thermal': (ViewerPanel, dict(viewer=Thermal('192.168.1.111'))),
        'Primitiv': (MoverPanel, dict(mover=Primitiv('COM5'), axes=['X','Y','Z'])),
        # 'Ender': (MoverPanel, dict(mover=Ender('COM4'), axes=['X','Y','Z'])),
        # 'Dobot': (MoverPanel, dict(mover=Dobot('COM5'), axes=['X','Y','Z','a','b','g'])),
    }
    gui = CompoundPanel(ensemble)
    gui.runGUI('Primitiv')
    pass

# %% Spinner examples
from controllable.Make.ThinFilm import SpinnerAssembly
if __name__ == "__main__":
    ports = ['COM6','COM5','COM4','COM3']
    channels = [0,1,2,3]
    positions = [[-325,0,0],[-250,0,0],[-175,0,0],[-100,0,0]]
    spinners = SpinnerAssembly(ports=ports, channels=channels,positions=positions)
    pass

# %% Paraspin examples
from controllable.builds.Paraspin import program
from controllable.Control.Schedule import Scheduler
if __name__ == "__main__":
    REAGENTS = r'C:\Users\leongcj\Desktop\Astar_git\control-lab-le\controllable\builds\Paraspin\reagents.csv' 
    RECIPE = r'C:\Users\leongcj\Desktop\Astar_git\control-lab-le\controllable\builds\Paraspin\recipe.csv'
    spinbot = program.Program(config_option=0)
    spinbot.loadRecipe(REAGENTS, RECIPE)
    spinbot.labelPosition('fill', (-100,0,0))
    spinbot.prepareSetup()
    spinbot.loadScheduler(Scheduler())
    # spinbot.runExperiment()
    pass

# %% Sartorius examples
from controllable.Move.Liquid.Sartorius import SartoriusDevice
if __name__ == "__main__":
    pipet = SartoriusDevice('COM17')
    pass

# %%
# %% Jointed M1 Pro examples
from controllable.Move.Jointed import M1Pro
if __name__ == "__main__":
    mover = M1Pro(ip_address='192.168.2.21', home_position=(300,0,100))
    pass
# %%
