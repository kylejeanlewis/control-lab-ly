# %%
import init
import time
from controllably.Make.ThinFilm import SpinnerAssembly, Spinner
#%%
me = SpinnerAssembly(
    ports=['COM37','COM38','COM39','COM40'], 
    channels=[1,2,3,4], 
    positions=[[57.5,42.5,128], [132.5,42.5,128],[207.5,42.5,128],[282.5,42.5,128]]
)
me.__dict__
# %%
me.run(soak_time=2, spin_speed=1000, spin_time=10, channel=1)
me.run(4, 2000, 20, 2)
me.run(6, 3000, 30, 3)
me.run(8, 4000, 40, 4)
# %%
me = Spinner('COM41')
# %%
