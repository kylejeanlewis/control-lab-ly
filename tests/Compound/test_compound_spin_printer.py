# %%
from init import library
from controllably.Transfer.Liquid import SyringeAssembly
from controllably.Transfer.Liquid.Pumps import Peristaltic
from controllably.Compound.LiquidMover import LiquidMoverSetup
from controllably import Helper, Factory
# %%
details = Factory.get_details(Helper.read_yaml(library['configs']['spin_printer']))
pump = Peristaltic('COM28')
me = LiquidMoverSetup(**details['setup']['settings'])
me.__dict__
me.liquid.device = pump
# %%
me.mover.home()
# %%
me.liquid.fill(channel=5)
# %%
me.liquid.aspirate(500)
# %%
me.aspirateAt((-200,0,0), 200, channel=4)
# %%
me.dispenseAt((-100,0,0), 200)
# %%
me.liquid.empty()
# %%
