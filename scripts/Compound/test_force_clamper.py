# %%
import numpy as np
import plotly.express as px
import random as rd
import time

from init import library
from controllably import Factory, Helper, guide_me
from controllably.Move.Cartesian import Primitiv
from controllably.Measure.Electrical.Keithley import KeithleyDevice
from controllably.Measure.Mechanical import LoadCell

# %%
details = Factory.get_details(Helper.read_yaml(library['configs']['primitiv2']))
me = Primitiv(**details['mover']['settings'])
me.__dict__

# %%
me.move('y',-150, wait=False)
# %%
sensor = LoadCell(
    device = KeithleyDevice('192.109.209.100'),
    verbose = True
)

# %%
baseline = -0.03
volts = []
x,y,z = me.tool_position[0]
_, prevailing_speed = me.setSpeed(me.max_speed[2], 'z')
threshold = baseline*1.01
start = time.time()
target = np.array((x,y,20))
me.moveTo(target, wait=False, jog=True)
while True:
    # num = read_value()
    num=sensor.getValue()
    volts.append(num)
    print(num)
    # time.sleep(0.1)
    if num <= threshold:
        me.stop()
        break
    if time.time() - start > 60:
        break

# threshold = 0.90
target = np.array((x,y,me.tool_position[0][2]))
me.move('z',10)
time.sleep(3)

me.setSpeed(me.max_speed[2]*0.1, 'z')
me.moveTo(target, wait=False, jog=True)
while True:
    # num = read_value()
    num=sensor.getValue()
    volts.append(num)
    print(num)
    # time.sleep(0.1)
    if num <= threshold:
        me.stop()
        break
    if time.time() - start > 60:
        break
me.setSpeed(prevailing_speed[2], 'z')

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
class Sensor:
    def __init__(self, verbose=True):
        self.baseline = 0.9
        self.verbose = verbose
        return
    def getValue(self):
        value = rd.random()
        if self.verbose:
            print(value)
        return value

sensor = Sensor()
# %%
setup = ForceClampSetup(components=dict(mover=mover, sensor=sensor), component_config=dict())

# %%
setup.clamp(threshold=0.995, speed_factor=0.5)

# %%
from leapfrog.Measure.Electrical.BioLogic import BioLogic, programs

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
from leapfrog.Analyse.Data.Impedance import ImpedanceSpectrum
# %%
eis = ImpedanceSpectrum(bio.buffer_df, instrument='Biologic')
eis.plot()
# %%
