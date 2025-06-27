# %%
from init import library
from controllably.Make.ThinFilm import SpinnerAssembly
from controllably import Helper, Factory
#%%
details = Factory.get_details(Helper.read_yaml(library['configs']['spin_assembly']))
me = SpinnerAssembly(**details['spinner']['settings'])
me.__dict__
# %%
me.run(soak_time=2, spin_speed=1000, spin_time=10, channel=1)
me.run(4, 2000, 20, 2)
me.run(6, 3000, 30, 3)
me.run(8, 4000, 40, 4)
# %%
