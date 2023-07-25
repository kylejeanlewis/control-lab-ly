# %%
import init
from controllably.Move.Cartesian import Ender
from controllably.Control.GUI.Basic import MoverPanel

me = Ender('COM18', limits=((0,0,0),(220,220,250)), max_speed=300, verbose=True)
# me = Ender('COM18', limits=((0,0,0),(100,100,70)), max_speed=10, verbose=True)
gui = MoverPanel(me, axes='XYZ')
# gui.runGUI()
me.__dict__
# %%
me.home()
# %%
me.moveTo((50,50,50))
# %%
me.move('x',30)
# %%
me.moveBy((10,10,5))
# %%
me.safeMoveTo((20,40,20))
# %%
me.setSpeed(20) # NOTE: max speed is 180 mm/s
# %%
me.moveTo((150,150,50))
# %%
me.home()
# %%
me.setTemperature(50)
me.home()
# %%
me.setTemperature(0, False)
# %%
