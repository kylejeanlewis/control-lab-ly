 # %%
from .. import init
from controllably.Move.Jointed.Dobot import M1Pro
from controllably.Control.GUI.Basic import MoverPanel
from controllably import Helper, Factory

details = Factory.get_details(Helper.read_yaml('configs/m1pro.yaml'))['mover']
gui = MoverPanel(M1Pro(**details['settings']), axes='XYZa')
# gui.runGUI()
me = gui.tool
me.__dict__
# %%
me.home()
# %%
me.moveTo((450,0,200))
# %%
me.moveBy((50,50,50))
# %%
me.move('z',-70)
# %%
me.safeMoveTo((450,0,200), ascent_speed=20, descent_speed=50)
# %%
me.home()
# %%
me.rotateBy((50,0,0))
# %%
me.rotateTo((-50,0,0))
# %%
me.home()
# %%
