# %%
from init import library
from controllably.Transfer.Liquid import SyringeAssembly
from controllably.Transfer.Liquid.Pumps import Peristaltic
from controllably import Helper, Factory

details = Factory.get_details(Helper.read_yaml(library['configs']['syringe_assembly']))
me = SyringeAssembly(pump=Peristaltic('COM28'), **details['liquid']['settings'])
me.__dict__
# %%
me.fill(channel=2)
# %%
me.aspirate(500)
# %%
me.dispense(200, channel=4)
# %%
me.empty()
# %%
