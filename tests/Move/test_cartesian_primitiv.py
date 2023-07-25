# %%
import init
from controllably.Move.Cartesian import Primitiv
from controllably.Control.GUI.Basic import MoverPanel

me = Primitiv('COM5')
gui = MoverPanel(me, axes='XYZ')
# gui.runGUI()
me.__dict__
# %%
me.home()
# %%
me.moveTo((-50,-50,-50))
# %%
me.move('z',20)
# %%
me.moveBy((-10,-10,-50))
# %%
me.safeMoveTo((-20,-40,-90))
# %%
me.home()
# %%
me.setSpeed(10)
# %%
