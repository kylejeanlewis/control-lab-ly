# %%
from init import library
from controllably.Transfer.Liquid.Pump.TriContinent import TriContinent
from controllably import Helper, Factory

details = Factory.get_details(Helper.read_yaml(library['configs']['tricontinent_pumps']))
me = TriContinent(**details['liquid']['settings'])
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
