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
