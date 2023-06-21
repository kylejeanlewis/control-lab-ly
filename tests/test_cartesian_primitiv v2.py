# %%
import init
from controllably.Move.Cartesian import Primitiv
from controllably.Control.GUI.Basic import MoverPanel

# %%
me = Primitiv(
    'COM18', 
    ((-199,-480,-200),(-15,0,0)), 
    home_coordinates=(-199,0,0),
    max_speed=20,
    verbose=True
)
me.__dict__

# %%
gui = MoverPanel(me, axes='XYZ')
gui.runGUI()

# %%
me.home()
# %%
me.moveTo((-150,-50,-50))
# %%
me.move('z',-20)
# %%
me.moveBy((50,-50,-50))
# %%
me.safeMoveTo((-120,-40,-90))
# %%
me.moveTo((-120,-40,-90))
# %%
me.home()
# %%
me.setSpeed(10) # NOTE: speed does not change for Primitiv
# %%
me._query("$$")
# %%
me.device.write("$$".encode("utf-8"))
me.device.read_until(b'\r\n')
# %%

# %%
