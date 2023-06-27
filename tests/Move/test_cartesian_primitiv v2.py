# %%
import init
from controllably import Factory, Helper, guide_me
from controllably.Move.Cartesian import Primitiv
from controllably.Transfer.Liquid.Sartorius import Sartorius

from controllably.Compound.LiquidMover import LiquidMoverSetup
from controllably.Control.GUI import CompoundPanel
from controllably.Control.GUI.Basic import MoverPanel, LiquidPanel

# %%
details = Factory.get_details(Helper.read_yaml('../configs/primitiv2.yaml'))
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
me._query("$$")
# %%
me.device.write("$$\n".encode("utf-8"))
me.device.readlines()
