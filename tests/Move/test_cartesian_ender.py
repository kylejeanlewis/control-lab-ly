# %%
import init
from controllably.Move.Cartesian import Marlin
from controllably.Control.GUI.Basic import MoverPanel
import numpy as np
import random as rd
import time

me = Marlin(
    'COM4', 
    limits=((0,0,0),(220,220,250)),
    home_coordinates=(0,0,30),
    # speed_max=dict(x=100,y=100,z=100),
    # accel_max=dict(x=100,y=100,z=100),
    verbose=True
)
# me = Ender('COM18', limits=((0,0,0),(100,100,70)), max_speed=10, verbose=True)
gui = MoverPanel(me, axes='XYZ')
# gui.runGUI()
me.__dict__
# %%
me.home()
# %%
me.moveTo((50,50,50),speed_factor=0.2)
# %%
me.move('x',30,speed_factor=0.2)
# %%
me.moveBy((10,10,5), speed_factor=0.2)
# %%
me.safeMoveTo((20,40,20), ascent_speed_ratio=0.2, descent_speed_ratio=0.2, travel_speed_ratio=0.2)
# %%
me.home()
me.setSpeedFactor(0.7) 
# %%
me.moveTo((50,50,50))
# %%
me.move('x',30)
# %%
me.moveBy((10,10,5))
# %%
me.safeMoveTo((20,40,20))
# %%
me.home()
# %%
me.setSpeedFactor(1)
me.moveTo((150,150,50))
# %%
me.home()
# %%
me.setTemperature(50)
me.home()
# %%
me.setTemperature(0, False)
# %%
while True:
    step = np.array((0,0,-1))
    coordinates = me.coordinates + step
    condition1 = me.isFeasible(coordinates, transform_in=True, tool_offset=True)
    condition2 = True # (self.sensor.getValue() <= self.threshold)
    if not condition1 or not condition2:
        break
    me.move('z', step[2])
    if me.coordinates[2] < 30:
        break
# %%
me.setSpeedFactor(1)
threshold = 0.99
start = time.time()
target = np.array((0,0,me.limits[1][2]))
me.moveTo(target, wait=False)
while True:
    num = rd.random()
    print(num)
    time.sleep(0.1)
    if num >= threshold:
        me.stop()
        break
    if time.time() - start > 60:
        break

threshold = 0.95
target = np.array((0,0,me.coordinates[2]))
me.move('z',-10)

me.setSpeedFactor(0.01)
me.moveTo(target, wait=False)
while True:
    num = rd.random()
    print(num)
    time.sleep(0.1)
    if num >= threshold:
        me.stop()
        break
    if time.time() - start > 60:
        break
me.setSpeedFactor(1)
# %%
