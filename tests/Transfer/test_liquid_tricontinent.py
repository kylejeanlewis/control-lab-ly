# %%
from .. import init
from controllably.Transfer.Liquid.Pumps.TriContinent import TriContinent
me = TriContinent(
    'COM23', 
    channel=[1,2], 
    model='C3000',
    capacity=1000, 
    output_right=True, 
    name=['first', 'second'],
    verbose=False
)
me.__dict__
# %%
me.setCurrentChannel(2)
# %%
me.prime(1)
# %%
me.move(40, up=False, channel=1)
# %%
me.moveBy(1000, channel=2)
# %%
me.moveTo(1500)
# %%
me.aspirate(20, channel=1)
# %%
me.dispense(500)
# %%
me.getPosition()
# %%
me.getStatus()
# %%
