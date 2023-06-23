# %%
from .. import init
from controllably.Make.ThinFilm import SpinnerAssembly

me = SpinnerAssembly(
    ports=['COM13','COM14','COM15','COM16'], 
    channels=[1,2,3,4], 
    positions=[(50,0,0),(100,0,0),(150,0,0),(200,0,0)]
)
me.__dict__
# %%
me.run(soak_time=2, spin_speed=1000, spin_time=10, channel=1)
me.run(4, 2000, 20, 2)
me.run(6, 3000, 30, 3)
me.run(8, 4000, 40, 4)
# %%
