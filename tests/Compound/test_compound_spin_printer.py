# %%
import init
from controllably.Transfer.Liquid import SyringeAssembly
from controllably.Transfer.Liquid.Pumps import Peristaltic
from controllably.Compound.LiquidMover import LiquidMoverSetup
from controllably import Helper, Factory

details = Factory.get_details(Helper.read_yaml('../configs/spin_printer.yaml'))['setup']
you = SyringeAssembly(
    pump=Peristaltic('COM28'),
    capacities=[2000]*5,
    channels=[3,4,5,6,7],
    offsets=((-100,0,0),(-75,0,0),(-50,0,0),(-25,0,0),(0,0,0))
)
me = LiquidMoverSetup(components=dict(liquid=you), **details['settings'])
me.__dict__
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
