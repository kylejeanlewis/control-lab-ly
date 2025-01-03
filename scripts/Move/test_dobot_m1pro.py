 # %%
from init import library
from controllably.Move.Jointed.Dobot import M1Pro
from controllably.Control.GUI.Basic import MoverPanel
from controllably import Helper, Factory

# %%
pro = M1Pro('192.109.209.21', verbose=True)
# %%

details = Factory.get_details(Helper.read_yaml(library['configs']['m1pro_B1']))
details['mover']['settings']['ip_address'] = '192.109.209.21'
me = M1Pro(**details['mover']['settings'])
gui = MoverPanel(me, axes='XYZa')
# gui.runGUI()
me.__dict__
speed_factor = 0.05
# %%
me.home()
# %%
me.moveTo((450,0,200))
# %%
me.moveBy((50,50,50))
# %%
me.move('z',-70)
# %%
me.safeMoveTo((450,0,200), ascent_speed_ratio=0.2, descent_speed_ratio=0.5)
# %%
me.home()
# %%
me.rotateBy((50,0,0))
# %%
me.rotateTo((-50,0,0))
# %%
me.home()
# %%
me.moveTo((450,0,200), speed_factor=speed_factor)
# %%
me.moveBy((50,50,50), speed_factor=speed_factor)
# %%
me.move('z',-70, speed_factor=speed_factor)
# %%
me.safeMoveTo((450,0,200), ascent_speed_ratio=0.3, descent_speed_ratio=0.1, travel_speed_ratio=0.5)
# %%
me.home()
# %%
me.rotateBy((50,0,0),speed_factor=speed_factor)
# %%
me.rotateTo((-50,0,0), speed_factor=speed_factor)
# %%
