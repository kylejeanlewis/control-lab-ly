# %%
import init
from controllably.Move.Jointed.Dobot import MG400
from controllably.Control.GUI import MoverPanel

gui = MoverPanel(MG400('192.168.2.8'))
gui.runGUI()
me = gui.tool
# %%
me.home()
me.moveTo((50,50,50))
me.move('z',-30)
me.moveBy((10,10,5))
me.safeMoveTo((20,40,20))
me.home()
# %%
me.heat(30)
# %%
me.setSpeed()
# %%
me.__dict__