# %%
import init
from controllably.Transfer.Liquid.Pumps.TriContinent import TriContinent
me = TriContinent('COM23', channel=[1,2], model='C3000',capacity=1000, output_right=True, name=['first', 'second'])
# %%
me.setCurrentChannel(2)
# %%
me.prime(1)
# %%
me.move(40, up=False)
# %%
me.moveBy(150,1) # FIXME: channel parameter does not work
# %%
me.moveTo(1500)
# %%
me.aspirate(200)
# %%
me.dispense(500)
# %%
me.getPosition()
# %%
me.getStatus()

# %%
