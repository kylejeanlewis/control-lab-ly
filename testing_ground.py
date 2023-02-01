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
from controllable.misc import Helper
if __name__ == "__main__":
    Helper.display_ports()
    pass

# %% Cartesian examples
from controllable.Move.Cartesian import Primitiv, Ender
from controllable.Control.GUI import MoverPanel
if __name__ == "__main__":
    mover = Ender('COM4')
    gui = MoverPanel(**dict(mover=mover, axes=['X','Y','Z']))
    gui.runGUI('Primitiv')
    pass

# %% Jointed MG400 examples
from controllable.Move.Jointed.Dobot import MG400
from controllable.Control.GUI import MoverPanel
if __name__ == "__main__":
    mover = MG400(ip_address='192.109.209.8')
    gui = MoverPanel(**dict(mover=mover, axes=['X','Y','Z','a']))
    gui.runGUI('M1Pro')
    pass

# %% Jointed M1 Pro examples
from controllable.Move.Jointed.Dobot import M1Pro
from controllable.Control.GUI import MoverPanel
if __name__ == "__main__":
    mover = M1Pro(ip_address='192.168.2.21', home_coordinates=(300,0,100))
    gui = MoverPanel(**dict(mover=mover, axes=['X','Y','Z','a']))
    gui.runGUI('M1Pro')
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

# %% Webcam examples
from controllable.View.Optical import Optical
import time

FOLDER = 'C:/Users/leongcj/Desktop/machine vision'

if __name__ == "__main__":
    viewer = Optical(1)
    viewer.getImage()
    viewer.toggleRecord(True, folder=FOLDER, timeout=10)
    time.sleep(10)
    viewer.toggleRecord(False)
    pass

# %% Thermal cam examples
from controllable.View.Thermal import Thermal
from controllable.Control.GUI import ViewerPanel
if __name__ == "__main__":
    viewer = Thermal('192.168.1.111')
    viewer.getImage()
    gui = ViewerPanel(**dict(viewer=viewer, name='AX8'))
    gui.runGUI('AX8')
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
        'Camera': (ViewerPanel, dict(viewer=Optical(1))),
        # 'Thermal': (ViewerPanel, dict(viewer=Thermal('192.168.1.111'))),
        # 'Primitiv': (MoverPanel, dict(mover=Primitiv('COM5'), axes=['X','Y','Z'])),
        # 'Ender': (MoverPanel, dict(mover=Ender('COM17'), axes=['X','Y','Z'])),
        # 'M1Pro': (MoverPanel, dict(mover=M1Pro(), axes=['X','Y','Z','a','b','c'])),
        # 'Keithley': (MeasurerPanel, dict(measurer=Keithley('192.168.1.104'))),
        # 'Biologic': (MeasurerPanel, dict(measurer=Biologic('192.168.1.104'))),
    }
    gui = CompoundPanel(ensemble)
    gui.runGUI('Demo')
    pass

# %% GUI examples: Keithley
from controllable.Measure.Electrical.Keithley import Keithley
from controllable.Control.GUI import MeasurerPanel
if __name__ == "__main__":
    gui = MeasurerPanel(**dict(measurer=Keithley('192.168.1.104'), name='Keithley'))
    gui.runGUI('Keithley')
    pass

# %% GUI examples: Biologic
from controllable.Measure.Electrical.Biologic import Biologic
from controllable.Control.GUI import MeasurerPanel
if __name__ == "__main__":
    gui = MeasurerPanel(**dict(measurer=Biologic(), name='Biologic'))
    gui.runGUI('Biologic')
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
    spinbot = SpinbotController(config_option=0)
    spinbot.loadRecipe(REAGENTS, RECIPE)
    spinbot.prepareSetup()
    spinbot.loadScheduler(ScanningScheduler(), rest=False)
    spinbot.runExperiment()
    pass

# %% Paraspin examples (B1)
from controllable.Compound.LiquidMover import LiquidMoverSetup
from controllable.Measure.Physical import MassBalance
import time

import pandas as pd
pd.options.plotting.backend = 'plotly'

if __name__ == "__main__":
    spinbot = LiquidMoverSetup(config_option=0)
    balance = MassBalance('COM8')

    setup =spinbot
    mover = setup.mover
    liquid = setup.liquid
    
    for _ in range(96):
        coord = setup.attachTip()
        setup.ejectTipAt(coordinates=(*coord[:2],coord[2]-18))
    
    # coord = setup.attachTip()
    # mover.home()
    # vol = 100
    # for i in range(30):
    #     print(f'Cycle {i+1}')
    #     setup.aspirateAt((424.3,21,-74), vol)
    #     setup.dispenseAt((227,30,-15), vol)
    #     time.sleep(20)
    # balance.buffer_df.plot(x='Time', y='Value')
    # balance.buffer_df.to_csv(f'sartorius calib 5-0-{vol}uL.csv')
    # mover.move('z', 50)
    # mover.home()
    # setup.ejectTipAt(*coord[:2],coord[2]-18)
    # balance.reset()
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
from controllable.Measure.Physical.balance_utils import MassBalance
if __name__ == "__main__":
    balance = MassBalance('COM8')
    balance.zero()
    balance.toggleRecord(True)
    time.sleep(10)
    balance.toggleRecord(False)
    pass

# %% Mass calibration
import numpy as np
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
from scipy.signal import find_peaks

RUNS = 7

calibration_steps = []
calib_dfs = []
pct_errors = []
for i in range(RUNS):
    volume = int(100/((i%2)+1))
    filename = f'C:\\Users\\leongcj\\Desktop\\Astar_git\\control-lab-le\\sartorius calib 5-{i}-{volume}uL.csv'
    df = pd.read_csv(filename, index_col=0)
    df['Time'] = pd.to_datetime(df['Time'])
    df['Value'] = df['Value']/0.9955
    df.dropna(inplace=True)
    df = df[(df['Value']<df['Value'].mean()*0.8) & (df['Value']>df['Value'].mean()*1.2)]    #Filter
    df.reset_index(drop=True, inplace=True)

    d1df = df['Value'].diff()
    d2df = d1df.diff()
    df = df.join(d1df, rsuffix='_d1')
    df = df.join(d2df, rsuffix='_d2')
    df = df[abs(df['Value_d1'])<500]    #Filter
    df.reset_index(drop=True, inplace=True)
    fig = px.scatter(df, x='Time', y=['Value', 'Value_d1','Value_d2'])
    # fig.show()
    
    x = df['Value_d1']
    peaks, _ = find_peaks(x, distance=100, height=(20,100))
    plt.plot(x)
    plt.plot(peaks, x[peaks], "x")
    plt.show()
    print(f'Number of peaks: {len(peaks)}')

    levels = []
    for peak in peaks:
        avg = df.loc[peak-55:peak-5, 'Value'].mean()
        levels.append(avg)
    step_sizes = np.diff(np.array(levels))
    step_sizes = np.extract(step_sizes>20, step_sizes)  #Filter
    avg_step_size = np.mean(step_sizes)
    print(f'Average step size: {avg_step_size}')
    pct_error = abs((step_sizes - volume)/volume) *100
    pct_errors.append(pct_error)

    step_per_uL = avg_step_size / volume
    print(f'Average step per uL: {step_per_uL}')
    calibration_steps.append(step_per_uL)
    
    data = {
        'step': [n for n in range(len(step_sizes))],
        'mass_diff': step_sizes,
        'mass_per_uL': np.array(step_sizes) / volume,
        'run': [f'{i}-{volume}uL' for _ in range(len(step_sizes))]
    }
    sub_df = pd.DataFrame(data)
    calib_dfs.append(sub_df)

calib_df = pd.concat(calib_dfs, ignore_index=True)
overall_avg_calibration = calib_df['mass_per_uL'].mean()
print(f'Overall average step per uL: {overall_avg_calibration:.5}')
overall_pct_error = np.mean(np.concatenate(pct_errors))
print(f'Overall percentage error: {overall_pct_error:.2}%')

n_colors = RUNS
colors = px.colors.sample_colorscale("viridis", [n/(n_colors -1) for n in range(n_colors)])
fig = px.scatter(calib_df, x='step', y='mass_diff', color='run', color_discrete_sequence=colors)
fig.show()

fig = px.scatter(calib_df, x='step', y='mass_per_uL', color='run', color_discrete_sequence=colors)
fig.show()

# %%
from controllable.misc.layout_utils import Deck
if __name__ == "__main__":
    deck = Deck(r'C:\Users\leongcj\Desktop\Astar_git\control-lab-le\examples\Labware\layout.json')
    pass

# %% Mass calibration
import numpy as np
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
from scipy.signal import find_peaks

pd.options.plotting.backend = 'plotly'
filename = r"C:\Users\leongcj\Desktop\Astar_git\control-lab-le\data\calibration\balance\sartorius calib 7-0-25g.csv"

df = pd.read_csv(filename, index_col=0)
df['Mass'] = df['Mass'] 
df['Mass'] = df['Mass'] - df.loc[:100,'Mass'].mean()
d1df = df['Mass'].diff()
d2df = d1df.diff()
df = df.join(d1df, rsuffix='_d1')
df.reset_index(drop=True, inplace=True)
df = df.join(d2df, rsuffix='_d2')
df.reset_index(drop=True, inplace=True)
trim_threshold = 1000
fig = px.line(df, x='Time', y=['Mass', 'Mass_d1','Mass_d2'])
fig.show()

x = df['Mass_d2']
peaks, _ = find_peaks(x, distance=100, height=(2500,50000))
plt.plot(x)
plt.plot(peaks, x[peaks], "x")
plt.show()
print(f'Number of peaks: {len(peaks)}')

A = 24.9959
B = 25.0015
C = 25.0036
D = 25.0054
# order = np.array([A,C,B,-C,-A,D,C,-D,-B,D,A,-A-C,A,B,C,-A-B-C-D])*1000
order = np.array([A,C,B,-C,-A,D,C,-D,-B,D,A,B,-C,-B,-A,-D])*1000
expected_levels = np.insert(np.cumsum(order), 0, 1E-10)
expected_step_sizes = np.array(order)

levels = []
for peak in peaks:
    avg = df.loc[peak-55:peak-5, 'Mass'].mean()
    levels.append(avg)
levels = np.array(levels) - levels[0]
level_error = levels - expected_levels
level_pct_error = (levels/(expected_levels) - 1)*100
level_mae = abs(level_error).mean()
level_mape = abs(level_pct_error[1:-1]).mean()

step_sizes = np.diff(np.array(levels))
calib_factor = step_sizes/expected_step_sizes
step_error = step_sizes - expected_step_sizes
step_pct_error = abs(calib_factor - 1) * 100
calib_factor_avg = calib_factor.mean()
step_mae = abs(step_error).mean()
step_mape = abs(step_pct_error).mean()
print(f'Average calibration factor: {calib_factor_avg}')
print(f'Mean absolute error (level): {level_mae:.03} mg')
print(f'Mean absolute percentage error (level): {level_mape:.03} %')
print(f'Mean absolute error (step): {step_mae:.03} mg')
print(f'Mean absolute percentage error (step): {step_mape:.03} %')
fig_lvl = px.bar(x=[i for i in range(len(levels))], y=levels/1000)
fig_lvl.show()

# %% Paraspin examples (B1)
from controllable.Compound.LiquidMover import LiquidMoverSetup
from controllable.Measure.Physical import MassBalance
from controllable.View.Optical import Optical
import plotly.express as px
import time

import pandas as pd
pd.options.plotting.backend = 'plotly'

if __name__ == "__main__":
    spinbot = LiquidMoverSetup(config_option=0)
    balance = MassBalance('COM8')
    camera = Optical(1)

    setup =spinbot
    mover = setup.mover
    liquid = setup.liquid
    
    # setup.align(setup.deck.get_slot(name='jars').get_well('A1').middle)
    # balance.toggleRecord(True)
    # camera.toggleRecord(True, folder='C:/Users/leongcj/Desktop/machine vision', timeout=60)
    # liquid.aspirate(volume=200, speed=None)
    # time.sleep(60)
    # balance.toggleRecord(False)
    # camera.toggleRecord(False)
    pass

# %%
from controllable.builds.SynthesisB1 import program

this = program.create_setup()
this.liquid.setFlag('tip_on', True)
# %%
from controllable.Control.GUI import MoverPanel
gui = MoverPanel(mover=this.mover, axes=['X','Y','Z','a'])
gui.runGUI()
# %%
import time
import pandas as pd
pd.options.plotting.backend = "plotly"
# %%
# time.sleep(2)
# this.balance.toggleRecord(True)
this.camera.toggleRecord(True, folder='C:/Users/leongcj/Desktop/machine vision')
this.liquid.aspirate(volume=1000, speed=150, wait=5)
# time.sleep(1)
this.camera.toggleRecord(False)
# this.balance.toggleRecord(False)
this.liquid.dispense(volume=1000, speed=150)
# %%
df = pd.read_csv(r'C:\Users\leongcj\Desktop\machine vision\2023-01-30_1419\timestamps.csv')
df.plot(x='frame_num', y='timestamp')
# %%
