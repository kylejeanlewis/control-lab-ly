# %% -*- coding: utf-8 -*-
"""
Created: Tue 2022/11/01 17:13:35
@author: Chang Jie

Notes / actionables:
TODO
- test View.Classifier
- test builds

LATER TODO
- test database_utils
- add 'Visualisation' modules
"""
# Standard library imports
import numpy as np
import pandas as pd

# Local application imports
print(f"Import: OK <{__name__}>")

pd.options.plotting.backend = "plotly"

# %% Helper examples
from controllable.misc import HELPER
if __name__ == "__main__":
    HELPER.display_ports()
    pass

# %% Cartesian examples
from controllable.Move.Cartesian import Primitiv, Ender
if __name__ == "__main__":
    mover = Ender('COM4')
    # mover = Primitiv('COM5')
    pass

# %% Jointed MG400 examples
from controllable.Move.Jointed.Dobot import MG400
if __name__ == "__main__":
    mover = MG400(ip_address='192.109.209.8')
    pass

# %% Jointed M1 Pro examples
from controllable.Move.Jointed.Dobot import M1Pro
if __name__ == "__main__":
    mover = M1Pro(ip_address='192.168.2.21', home_coordinates=(300,0,100))
    pass

# %% Keithley examples
from controllable.Measure.Electrical.Keithley import Keithley, base_programs
if __name__ == "__main__":
    me = base_programs.IV_Scan
    measurer = Keithley('192.168.1.104')
    measurer.loadProgram('LSV')
    measurer.measure()
    pass

# %% BioLogic examples
from controllable.Measure.Electrical.Biologic import Biologic
if __name__ == "__main__":
    measurer = Biologic('192.109.209.128')
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

    measurer.loadProgram(name='PEIS')
    measurer.loadDataType(name='ImpedanceSpectrum')
    measurer.measure(params, channels=[0])
    pass

# %% BioLogic examples
if __name__ == "__main__":
    measurer.reset()
    params = {
        'time': 1,
        'voltage_interval': 0.01
    }

    measurer.loadProgram('OCV')
    measurer.measure(params, channels=[0])
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

    measurer.loadProgram(name='GEIS')
    measurer.loadDataType(name='ImpedanceSpectrum')
    measurer.measure(params, channels=[0])
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

    measurer.loadProgram(name='CV')
    measurer.measure(params, channels=[0])
    pass

# %% Webcam examples
from controllable.View.Optical import Optical
if __name__ == "__main__":
    viewer = Optical()
    viewer.getImage()
    pass

# %% Thermal cam examples
from controllable.View.Thermal import Thermal
if __name__ == "__main__":
    viewer = Thermal('192.168.1.111')
    viewer.getImage()
    pass

# %% Sartorius examples
from controllable.Transfer.Liquid.Sartorius import Sartorius
if __name__ == "__main__":
    pipet = Sartorius('COM17')
    pass

# %% GUI examples: Ensemble
from controllable.Measure.Electrical.Keithley import Keithley
from controllable.Measure.Electrical.Biologic import Biologic
from controllable.Move.Cartesian import Ender, Primitiv
from controllable.Move.Jointed.Dobot import M1Pro
from controllable.View.Optical import Optical
from controllable.View.Thermal import Thermal
from controllable.Control.GUI import CompoundPanel, MeasurerPanel, MoverPanel, ViewerPanel
if __name__ == "__main__":
    ensemble = {
        'Camera': (ViewerPanel, dict(viewer=Optical())),
        # 'Thermal': (ViewerPanel, dict(viewer=Thermal('192.168.1.111'))),
        'Primitiv': (MoverPanel, dict(mover=Primitiv('COM5'), axes=['X','Y','Z'])),
        'Ender': (MoverPanel, dict(mover=Ender('COM17'), axes=['X','Y','Z'])),
        'M1Pro': (MoverPanel, dict(mover=M1Pro(), axes=['X','Y','Z','a','b','c'])),
        'Keithley': (MeasurerPanel, dict(measurer=Keithley('192.168.1.104'))),
        'Biologic': (MeasurerPanel, dict(measurer=Biologic('192.168.1.104'))),
    }
    gui = CompoundPanel(ensemble)
    gui.runGUI('Demo')
    pass

# %% GUI examples: Primitiv
from controllable.Move.Cartesian import Primitiv
from controllable.Control.GUI import MoverPanel
if __name__ == "__main__":
    gui = MoverPanel(**dict(mover=Primitiv('COM4'), axes=['X','Y']))
    gui.runGUI('Primitiv')
    pass

# %% GUI examples: M1Pro
from controllable.Move.Jointed.Dobot import M1Pro, MG400
from controllable.Control.GUI import MoverPanel
if __name__ == "__main__":
    gui = MoverPanel(**dict(mover=M1Pro(ip_address='192.168.2.21', home_coordinates=(300,0,100)), axes=['X','Y','Z','a']))
    # gui = MoverPanel(**dict(mover=MG400(ip_address='192.109.209.8'), axes=['X','Y','Z','a']))
    gui.runGUI('MG400')
    pass

# %% GUI examples: Keithley
from controllable.Measure.Electrical.Keithley import Keithley, base_programs
from controllable.Control.GUI import MeasurerPanel
if __name__ == "__main__":
    gui = MeasurerPanel(**dict(measurer=Keithley('192.168.1.104'), name='Keithley'))
    gui.runGUI('Keithley')
    pass

# %% GUI examples: Biologic
from controllable.Measure.Electrical.Biologic import Biologic, base_programs
from controllable.Control.GUI import MeasurerPanel
if __name__ == "__main__":
    gui = MeasurerPanel(**dict(measurer=Biologic(), name='Biologic'))
    gui.runGUI('Biologic')
    pass

# %% GUI examples: Keithley
from controllable.View.Thermal import Thermal
from controllable.Control.GUI import ViewerPanel
if __name__ == "__main__":
    # me = base_programs.OCV
    gui = ViewerPanel(**dict(viewer=Thermal('192.168.1.111'), name='AX8'))
    gui.runGUI('AX8')
    pass

# %% Spinner examples
from controllable.Make.ThinFilm import SpinnerAssembly
if __name__ == "__main__":
    kwargs = dict(
        ports = ['COM6','COM5','COM4','COM3'],
        channels = [0,1,2,3],
        positions = [[-325,0,0],[-250,0,0],[-175,0,0],[-100,0,0]]
    )
    spinners = SpinnerAssembly(**kwargs)
    pass

# %% Paraspin examples (L6)
from controllable.builds.Paraspin import SpinbotController
from controllable.Control.Schedule import ScanningScheduler
if __name__ == "__main__":
    REAGENTS = r'C:\Users\leongcj\Desktop\Astar_git\control-lab-le\controllable\builds\Paraspin\parameters\reagents.csv' 
    RECIPE = r'C:\Users\leongcj\Desktop\Astar_git\control-lab-le\controllable\builds\Paraspin\parameters\recipe.csv'
    # REAGENTS = r'C:\Users\Asus\Desktop\Astar_git\control-lab-le\controllable\builds\Paraspin\parameters\reagents.csv' 
    # RECIPE = r'C:\Users\Asus\Desktop\Astar_git\control-lab-le\controllable\builds\Paraspin\parameters\recipe.csv'
    spinbot = SpinbotController(config_option=0)
    spinbot.loadRecipe(REAGENTS, RECIPE)
    spinbot.prepareSetup()
    spinbot.loadScheduler(ScanningScheduler(), rest=False)
    spinbot.runExperiment()
    pass

# %% Paraspin examples (B1)
from controllable.builds.Paraspin import SpinbotController
from controllable.Control.Schedule import ScanningScheduler
if __name__ == "__main__":
    REAGENTS = r'C:\Users\leongcj\Desktop\Astar_git\control-lab-le\controllable\builds\Paraspin\parameters\reagents.csv' 
    RECIPE = r'C:\Users\leongcj\Desktop\Astar_git\control-lab-le\controllable\builds\Paraspin\parameters\recipe.csv'
    # REAGENTS = r'C:\Users\Asus\Desktop\Astar_git\control-lab-le\controllable\builds\Paraspin\parameters\reagents.csv' 
    # RECIPE = r'C:\Users\Asus\Desktop\Astar_git\control-lab-le\controllable\builds\Paraspin\parameters\recipe.csv'
    spinbot = SpinbotController(config_option=1)
    # spinbot.loadRecipe(REAGENTS, RECIPE)
    # spinbot.prepareSetup()
    # spinbot.loadScheduler(ScanningScheduler(), rest=False)
    # spinbot.runExperiment()
    pass

# %% Primitiv examples
from controllable.builds.PrimitivBench import PrimitivController
if __name__ == "__main__":
    primitiv = PrimitivController()
    pass

# %% PiezoRobotics examples
from controllable.Measure.Mechanical.PiezoRobotics import PiezoRobotics
import pandas as pd
pd.options.plotting.backend = "plotly"
if __name__ == "__main__":
    measurer = PiezoRobotics('COM19')
    measurer.reset()
    params = {
        'low_frequency': 1,
        'high_frequency': 150,
        'sample_thickness': 1E-3,
        'repeat': 3
    }
    measurer.measure(params)
    df = measurer.buffer_df
    
    df['Absolute Storage Modulus (MPa)'] = abs(df['Storage Modulus (MPa)'])
    df['Absolute Loss Modulus (MPa)'] = abs(df['Loss Modulus (MPa)'])
    df['Tan Delta'] = df['Absolute Loss Modulus (MPa)'] / df['Absolute Storage Modulus (MPa)'] 
    df['freq_id'] = df.index % (len(df) / max(df['run']))
    
    avg_df = df.groupby('freq_id').mean()
    std_df = df.groupby('freq_id').std()
    final_df = avg_df.join(std_df, rsuffix='_std')
    final_df.drop(columns=[col for col in final_df.columns if col.startswith('run')], inplace=True)
    final_df.reset_index(drop=True, inplace=True)
    
    fig1 = final_df.plot('Frequency (Hz)', ['Absolute Storage Modulus (MPa)','Absolute Loss Modulus (MPa)'])
    fig2 = final_df.plot('Frequency (Hz)', 'Tan Delta')
    fig1.show()
    fig2.show()
    pass

# %%
from controllable.Measure.Mechanical.PiezoRobotics.piezorobotics_device import PiezoRoboticsDevice
if __name__ == "__main__":
    device = PiezoRoboticsDevice('COM19')
    pass

# %%
