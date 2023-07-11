# %%
from init import library
import numpy as np
from controllably.Compound.LiquidMover import LiquidMoverSetup
from controllably import Helper, Factory
# %%
details = Factory.get_details(Helper.read_yaml(library['configs']['skwr']))
us = LiquidMoverSetup(**details['setup']['settings'])
us.liquid.getInfo('BRL1000')
us.loadDeck(library['deck']['layoutB1'])
us.__dict__
# %%
us.attachTip(start_tip='D4')
# %%
us.mover.home()
# %%
us.aspirateAt(us.mover.tool_position[0], 200)
# %%
us.dispenseAt(us.mover.tool_position[0]+np.array((10,10,10)), 200)
# %%
us.returnTip()
# %%
from controllably.Control.GUI.Basic import MoverPanel
from controllably.Transfer.Substrate import Dobot
gui = MoverPanel(us.mover, axes='XYZa')
# %%
gui.runGUI()
# %%
