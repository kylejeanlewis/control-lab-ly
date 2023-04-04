# %%
import init
from controllably.Transfer.Liquid.Sartorius import Sartorius
me = Sartorius('COM17', verbose=True)
me.getInfo('BRL1000')
me.fill()

# %%
