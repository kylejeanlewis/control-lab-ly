# %%
import init
from controllably.Transfer.Liquid import SyringeAssembly
from controllably.Transfer.Liquid.Pumps import Peristaltic

me = SyringeAssembly(
    pump=Peristaltic('COM28'),
    capacities=[2000]*5,
    channels=[1,2,3,4,5],
    offsets=[(0,0,0)]*5
)
me.__dict__ # COM17 gantry
# %%
me.fill(channel=2)
# %%
me.aspirate(500)
# %%
me.dispense(200, channel=4)
# %%
me.empty()
# %%
