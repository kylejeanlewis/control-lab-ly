# %%
import init
from controllably.Move.Cartesian import Grbl
from controllably.Control.GUI.Basic import MoverPanel

me = Grbl('COM5', safe_height=-20, verbose=True)
gui = MoverPanel(me, axes='XYZ')
# gui.runGUI()
me.__dict__
speed_factor = 0.1
# %%
me.home()
# %%
me.moveTo((-50,-50,-50), speed_factor=speed_factor)
# %%
me.move('z',40, speed_factor=speed_factor)
# %%
me.moveBy((-10,-10,-50), speed_factor=speed_factor)
# %%
me.safeMoveTo((-20,-40,-50), ascent_speed_ratio=speed_factor, descent_speed_ratio=0.1, travel_speed_ratio=1)
# %%
me.home()
me.setSpeedFactor(0.7)
# %%
me.moveTo((-50,-50,-50))
# %%
me.move('z',40)
# %%
me.moveBy((-10,-10,-50))
# %%
me.safeMoveTo((-20,-40,-50))
# %%
me.setSpeedFactor(1)
me.moveTo((-50,-50,-50))
# %%
me.home()
# %%
