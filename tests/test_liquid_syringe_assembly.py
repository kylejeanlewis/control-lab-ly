# %%
import init
from controllably.Transfer.Liquid import SyringeAssembly
from controllably.Transfer.Liquid.Pumps import Peristaltic
me = SyringeAssembly(Peristaltic('COM8'),[2000]*5,[1,2,3,4,5],[(0,0,0)]*5)
# %%
me.__dict__
# %%
me.fill(channel=2)
# %%
me.aspirate(500)
# %%
me.dispense(200)