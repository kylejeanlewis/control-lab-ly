# %%
import init
import numpy as np
from controllably.Compound.LiquidMover import LiquidMoverSetup
from controllably import Helper, Factory

details = Factory.get_details(Helper.read_yaml('../configs/skwr.yaml'))['setup']
me = LiquidMoverSetup(**details['settings'])
me.liquid.getInfo('BRL1000')
me.__dict__
# %%
me.loadDeck(r"C:\Users\leongcj\Desktop\Astar_git\control-lab-le\library\deck\layoutB1.json")
# %%
me.attachTip(start_tip='D4')
# %%
me.mover.home()
# %%
me.aspirateAt(me.mover.tool_position[0], 200)
# %%
me.dispenseAt(me.mover.tool_position[0]+np.array((10,10,10)), 200)
# %%
me.returnTip()
# %%
