# %%
from init import library
from controllably import Factory, Helper, guide_me
from controllably.Move.Cartesian import Primitiv
from controllably.Control.GUI.Basic import MoverPanel
from controllably.Measure.Electrical.Keithley import Keithley, programs


import numpy as np
import time
import random as rd
import plotly.express as px
# %%
details = Factory.get_details(Helper.read_yaml(library['configs']['primitiv2']))
me = Primitiv(**details['mover']['settings'])
me.__dict__

# %%
me.move('y',-150)
# %%

you = Keithley('192.109.209.100')
you.__dict__
# %%
device = you.device
device.reset()
device.sendCommands(['ROUTe:TERMinals FRONT'])
device.configureSource('current')
device.configureSense('voltage', limit=0.2, four_point=True, count=1)
device.makeBuffer()
device.setSource(0)
device.toggleOutput(True)
device.beep()

# %%
def read_value():
    volt = device._query("MEASure:VOLTage?")
    volt = float(volt)
    return volt

# %%
baseline = 0.023596492368421054
volts = []
x,y,z = me.tool_position[0]
me.setSpeed(me.max_speed[2])
threshold = baseline*1.01
start = time.time()
target = np.array((x,y,20))
me.moveTo(target, wait=False, jog=True)
while True:
    num = read_value()
    volts.append(num)
    print(num)
    # time.sleep(0.1)
    if num >= threshold:
        me.stop()
        break
    if time.time() - start > 60:
        break

# threshold = 0.90
target = np.array((x,y,me.tool_position[0][2]))
me.move('z',10)
time.sleep(3)

me.setSpeed(me.max_speed[2]*0.1)
me.moveTo(target, wait=False, jog=True)
while True:
    num = read_value()
    volts.append(num)
    print(num)
    # time.sleep(0.1)
    if num >= threshold:
        me.stop()
        break
    if time.time() - start > 60:
        break
me.setSpeed(me.max_speed[2])

# %%
px.scatter(x=[i for i in range(len(volts))], y=volts)
# %%
"""START HERE"""
import numpy as np
import plotly.express as px
import random as rd
import time

from init import library
from controllably import Factory, Helper, guide_me

from controllably.Move.Cartesian import Primitiv
from controllably.Measure.Electrical.Keithley import KeithleyDevice
from controllably.Measure.Physical import Balance
from controllably.Measure.Mechanical import LoadCell

from controllably.Compound.ForceClamper import ForceClampSetup

# %%
details = Factory.get_details(Helper.read_yaml(library['configs']['primitiv2']))
mover = Primitiv(**details['mover']['settings'])
mover.__dict__
# %%
mover = Primitiv(
    port = 'COM99', 
    limits = ((0,0,0), (100,100,100)), 
    safe_height = 80,
    verbose = True
)
# %%
calib = 1/166322569.226326
sensor = LoadCell(
    device = KeithleyDevice('192.109.209.100'), 
    # calibration_factor = calib, 
    verbose = True
)
# %%
setup = ForceClampSetup(components=dict(mover=mover, sensor=sensor), component_config=dict())

# %%
setup.clamp(speed_fraction=0.5)

# %%
from controllably.Measure.Electrical.BioLogic import BioLogic, programs

bio = BioLogic('192.109.209.128')
# %%
bio.loadProgram(programs.PEIS)

# %%
parameters = dict(
    voltage = 0.0,
    amplitude_voltage = 10E-3,
    initial_frequency=100E6,
    final_frequency = 10,
    frequency_number = 100,
    duration = 30
)
# parameters = dict(
#     current = np.array([10E-3]),
#     amplitude_current = 1E-4,
#     initial_frequency = 100000,
#     final_frequency = 1,
#     frequency_number = 100,
#     duration = 30
# )
bio.measure(parameters=parameters, channel=[0])
eis = ImpedanceSpectrum(bio.buffer_df, instrument='Biologic')
eis.plot()
# %%
you = sensor
# you.clearCache()
you.toggleRecord(True)
# %%
# time.sleep(10)
you.toggleRecord(False)
px.scatter(you.buffer_df, 'Time', 'Value')
# %%
from controllably.Analyse.Data.Impedance import ImpedanceSpectrum
# %%
eis = ImpedanceSpectrum(bio.buffer_df, instrument='Biologic')
eis.plot()
# %%
