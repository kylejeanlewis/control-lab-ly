# %%
import init
from controllably.Transfer.Liquid.Pumps import Peristaltic

me = Peristaltic('COM28')
me.__dict__
# %%
me.aspirate(3000,1)
# %%
me.dispense(2000, 1)
# %%
me.pullback(200,3)
# %%
me.turnAntiClockwise(2000)
# %%
me.stop()
# %%
me.setCurrentChannel(4)
# %%
me.turnClockwise(1000)
# %%
me.stop()
# %%
