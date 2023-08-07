# %%
from init import library
from controllably import Factory, Helper, guide_me
from controllably.Move.Cartesian import Primitiv
from controllably.Control.GUI.Basic import MoverPanel
import numpy as np
import time
import random as rd
# %%
details = Factory.get_details(Helper.read_yaml(library['configs']['primitiv2']))
me = Primitiv(**details['mover']['settings'])
me.__dict__

# %%
gui = MoverPanel(me, axes='XYZ')
gui.runGUI()

# %%
me.home()
# %%
me.moveTo((180,-450,-150))
# %%
me.home()
# %%
me.moveTo((-150,-50,-50))
# %%
me.moveTo((-50,-50,-50))
# %%
me.move('z',-20)
# %%
me.moveBy((-50,-50,-50))
# %%
me.safeMoveTo((-120,-40,-90))
# %%
me.moveTo((-120,-40,-90))
# %%
me.moveTo((-190,-10,-10))
# %%
me.home()
# %%
me.setSpeed(10) # NOTE: speed does not change for Primitiv

# %%
me.move('y',-150)
# %%
x,y,z = me.tool_position[0]
me.setSpeed(me.max_speed[2])
threshold = 0.99
start = time.time()
target = np.array((x,y,20))
me.moveTo(target, wait=False, jog=True)
while True:
    num = rd.random()
    print(num)
    time.sleep(0.1)
    if num >= threshold:
        me.stop()
        break
    if time.time() - start > 60:
        break

threshold = 0.90
target = np.array((x,y,me.tool_position[0][2]))
me.move('z',10)
time.sleep(3)

me.setSpeed(me.max_speed[2]*0.1)
me.moveTo(target, wait=False, jog=True)
while True:
    num = rd.random()
    print(num)
    time.sleep(0.1)
    if num >= threshold:
        me.stop()
        break
    if time.time() - start > 60:
        break
me.setSpeed(me.max_speed[2])
    # %%
