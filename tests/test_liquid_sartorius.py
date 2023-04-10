# %%
import init
from controllably.Transfer.Liquid.Sartorius import Sartorius

me = Sartorius('COM17')
# me.getInfo('BRL1000')
# %%
me.fill()
# %%
me.dispense(volume=750, speed=265)
# %%
me.aspirate(volume=750, speed=120)
# %%
me.rinse(speed=200)
# %%
me.aspirate(volume=750)
# %%
me.dispense(volume=750, blowout=True, blowout_home=True)
# %%
