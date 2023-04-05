# %%
import init
from controllably.Move.Cartesian import Ender
from controllably.Control.GUI import MoverPanel

gui = MoverPanel(Ender('COM4'))
# gui.runGUI()
me = gui.tool
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
me.home()
# %%
me.setTemperature(30)
# %%
me.setTemperature(25)
# %%
me.setSpeed() # NOTE: waiting for update
# %%
