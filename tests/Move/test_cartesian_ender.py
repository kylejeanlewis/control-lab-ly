# %%
import init
from controllably.Move.Cartesian import Ender
from controllably.Control.GUI.Basic import MoverPanel

gui = MoverPanel(Ender('COM4'))
# gui.runGUI()
me = gui.tool
me.verbose = True
me.__dict__
# %%
me.home()
# %%
me.moveTo((50,50,50))
# %%
me.move('z',-30)
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
me.setTemperature(30)
# %%
me.setTemperature(25)
# %%
